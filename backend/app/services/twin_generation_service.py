"""Twin generation orchestrator — coordinates the full twin creation pipeline."""

import logging
import re
import time
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewModule, InterviewSession
from app.models.twin import TwinProfile
from app.schemas.llm_responses import ProfileExtractionResponse
from app.services.evidence_indexer import (
    EvidenceIndexerService,
    get_evidence_indexer_service,
)
from app.services.persona_generator import (
    PersonaGeneratorService,
    get_persona_generator_service,
)
from app.services.profile_builder import (
    ProfileBuilderService,
    get_profile_builder_service,
)

logger = logging.getLogger(__name__)

MANDATORY_MODULES = {"M1", "M2", "M3", "M4"}


class TwinGenerationService:
    """Orchestrate the full twin generation pipeline."""

    def __init__(
        self,
        profile_builder: ProfileBuilderService | None = None,
        persona_generator: PersonaGeneratorService | None = None,
        evidence_indexer: EvidenceIndexerService | None = None,
    ):
        self.profile_builder = profile_builder or get_profile_builder_service()
        self.persona_generator = persona_generator or get_persona_generator_service()
        self.evidence_indexer = evidence_indexer or get_evidence_indexer_service()

    async def generate_twin(
        self,
        user_id: UUID,
        modules_to_include: list[str],
        db: AsyncSession,
    ) -> TwinProfile:
        """Run the full twin generation pipeline.

        Steps:
            1. Validate modules are completed
            2. Create TwinProfile with status="generating"
            3. Extract structured profile (LLM)
            4. Generate persona summary (LLM)
            5. Index evidence snippets + embeddings
            6. Calculate quality metrics
            7. Update TwinProfile to status="ready"

        Args:
            user_id: User to generate twin for.
            modules_to_include: List of module IDs to include.
            db: Database session.

        Returns:
            Completed TwinProfile.

        Raises:
            ValueError: If required modules are not completed.
        """
        start_time = time.time()

        # 1. Validate all requested modules are completed
        completed = await self._get_completed_modules(user_id, db)
        requested = set(modules_to_include)
        missing = requested - completed
        if missing:
            raise ValueError(
                f"Modules not completed: {', '.join(sorted(missing))}. "
                f"Completed: {', '.join(sorted(completed))}"
            )

        # 2. Determine version number
        version = await self._get_next_version(user_id, db)

        # 3. Create initial twin profile
        quality_label = self._determine_quality_label(modules_to_include)
        twin = TwinProfile(
            user_id=user_id,
            version=version,
            status="generating",
            modules_included=sorted(modules_to_include),
            quality_label=quality_label,
            quality_score=0.0,
        )
        db.add(twin)
        await db.flush()  # Get the twin ID

        logger.info(
            f"Starting twin generation for user {user_id}, "
            f"version {version}, modules: {modules_to_include}"
        )

        try:
            # 4. Extract structured profile
            profile_response = await self.profile_builder.extract_profile(user_id, db)

            # 5. Generate persona summary
            profile_dict = profile_response.model_dump()
            persona_response = await self.persona_generator.generate_summary(
                structured_profile=profile_dict,
                modules_included=modules_to_include,
                uncertainty_flags=profile_response.uncertainty_flags,
            )

            # 6. Index evidence snippets with embeddings
            snippets = await self.evidence_indexer.index_evidence(
                user_id=user_id,
                twin_profile_id=twin.id,
                db=db,
            )

            # 7. Enrichment: rank exemplars and select narrative memories
            ranked_exemplars = self._rank_and_select_exemplars(profile_dict, snippets)
            profile_dict["ranked_exemplars"] = ranked_exemplars

            selected_memories = self._select_narrative_memories(profile_dict)
            profile_dict["selected_narrative_memories"] = selected_memories

            # 8. Assemble voice/rules reference text
            voice_rules_text = self._assemble_voice_rules_reference(profile_dict)

            # 9. Calculate quality metrics
            coverage_confidence = await self._build_coverage_confidence(
                user_id, modules_to_include, db
            )
            interview_score = self._calculate_quality_score(coverage_confidence)

            # 10. Calculate simulation readiness
            readiness = self._calculate_simulation_readiness(
                profile_dict, snippets, modules_to_include
            )
            readiness_overall = readiness["overall"]

            # 11. Blend quality score: 50% interview + 50% simulation readiness
            blended = 0.5 * interview_score + 0.5 * readiness_overall

            # 12. Update twin profile
            elapsed = time.time() - start_time
            twin.status = "ready"
            twin.structured_profile_json = profile_dict
            twin.persona_summary_text = persona_response.persona_summary_text
            twin.persona_full_text = voice_rules_text or None
            twin.quality_score = round(blended, 3)
            twin.coverage_confidence = coverage_confidence
            twin.extraction_meta = {
                "completion_time_sec": round(elapsed, 1),
                "evidence_snippets_count": len(snippets),
                "key_traits": persona_response.key_traits,
                "uncertainty_flags": profile_response.uncertainty_flags,
                "simulation_notes": getattr(persona_response, "simulation_notes", []),
                "quality_breakdown": {
                    "interview_score": round(interview_score, 3),
                    "simulation_readiness": round(readiness_overall, 3),
                    "blended_score": round(blended, 3),
                    "components": {
                        "rule_density": readiness["rule_density"],
                        "voice_capture": readiness["voice_capture"],
                        "grounding_ratio": readiness["grounding_ratio"],
                        "narrative_richness": readiness["narrative_richness"],
                        "tension_coverage": readiness["tension_coverage"],
                    },
                },
            }

            await db.flush()

            logger.info(
                f"Twin generation complete for user {user_id}: "
                f"version={version}, quality={quality_label} ({quality_score:.2f}), "
                f"snippets={len(snippets)}, time={elapsed:.1f}s"
            )
            return twin

        except Exception as e:
            # Mark twin as failed
            twin.status = "failed"
            twin.extraction_meta = {"error": str(e)}
            await db.flush()
            logger.error(f"Twin generation failed for user {user_id}: {e}")
            raise

    async def _get_completed_modules(
        self, user_id: UUID, db: AsyncSession
    ) -> set[str]:
        """Get set of completed module IDs for a user."""
        stmt = (
            select(InterviewModule.module_id)
            .join(InterviewSession, InterviewModule.session_id == InterviewSession.id)
            .where(
                InterviewSession.user_id == user_id,
                InterviewModule.status == "completed",
            )
            .distinct()
        )
        result = await db.execute(stmt)
        return {row[0] for row in result.fetchall()}

    async def _get_next_version(self, user_id: UUID, db: AsyncSession) -> int:
        """Get the next version number for a user's twin."""
        stmt = select(func.max(TwinProfile.version)).where(
            TwinProfile.user_id == user_id
        )
        result = await db.execute(stmt)
        max_version = result.scalar()
        return (max_version or 0) + 1

    def _determine_quality_label(self, modules: list[str]) -> str:
        """Determine quality label based on modules included."""
        addons = set(modules) - MANDATORY_MODULES
        addon_count = len(addons)
        if addon_count == 0:
            return "base"
        elif addon_count <= 2:
            return "enhanced"
        elif addon_count <= 4:
            return "rich"
        else:
            return "full"

    async def _build_coverage_confidence(
        self,
        user_id: UUID,
        modules: list[str],
        db: AsyncSession,
    ) -> dict:
        """Build coverage/confidence map from completed modules."""
        stmt = (
            select(
                InterviewModule.module_id,
                InterviewModule.coverage_score,
                InterviewModule.confidence_score,
                InterviewModule.signals_captured,
            )
            .join(InterviewSession, InterviewModule.session_id == InterviewSession.id)
            .where(
                InterviewSession.user_id == user_id,
                InterviewModule.module_id.in_(modules),
                InterviewModule.status == "completed",
            )
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        by_module = {}
        for row in rows:
            module_id, coverage, confidence, signals = row
            by_module[module_id] = {
                "coverage": round(coverage, 2),
                "confidence": round(confidence, 2),
                "signals_captured": signals or [],
            }

        # Map modules to domains
        module_to_domain = {
            "M1": "identity",
            "M2": "decision_making",
            "M3": "preferences",
            "M4": "communication",
            "A1": "lifestyle",
            "A2": "spending",
            "A3": "career",
            "A4": "work_style",
            "A5": "technology",
            "A6": "health",
        }

        by_domain = {}
        for mid, data in by_module.items():
            domain = module_to_domain.get(mid, mid)
            by_domain[domain] = {
                "coverage": data["coverage"],
                "confidence": data["confidence"],
            }

        return {"by_module": by_module, "by_domain": by_domain}

    def _rank_and_select_exemplars(
        self, profile_dict: dict, snippets: list
    ) -> list[dict]:
        """Rank and select top exemplar quotes deterministically.

        Ranking heuristic per quote:
        - specificity (+2): contains a number, proper noun, or concrete detail
        - uniqueness (+1): not substantially similar to already selected exemplars
        - domain_coverage (+1): covers a domain not yet represented
        - length_penalty (-1): too short (<10 words) or too long (>50 words)

        Returns top 7 ranked exemplars.
        """
        exemplar_quotes = profile_dict.get("exemplar_quotes", [])
        if not exemplar_quotes:
            return []

        # Infer domains from behavioral rules for each quote
        rules = profile_dict.get("behavioral_rules", [])
        rule_domains = {r.get("source_quote", ""): r.get("domain", "") for r in rules if isinstance(r, dict)}

        scored = []
        for quote in exemplar_quotes:
            if not isinstance(quote, str) or not quote.strip():
                continue
            score = 0
            domains = []

            # Specificity: contains numbers, proper nouns (capitalized words), or concrete details
            if re.search(r'\d', quote):
                score += 2
            elif re.search(r'\b[A-Z][a-z]{2,}', quote):
                score += 2

            # Length penalty
            word_count = len(quote.split())
            if word_count < 10 or word_count > 50:
                score -= 1

            # Domain from matching rule
            for src, domain in rule_domains.items():
                if src and src in quote:
                    domains.append(domain)

            scored.append({"quote": quote, "score": score, "domains": domains})

        # Uniqueness and domain coverage pass
        selected = []
        covered_domains: set[str] = set()
        for item in sorted(scored, key=lambda x: x["score"], reverse=True):
            if len(selected) >= 7:
                break

            # Check uniqueness against already selected (word overlap < 50%)
            words = set(item["quote"].lower().split())
            is_duplicate = False
            for sel in selected:
                sel_words = set(sel["quote"].lower().split())
                if len(words) > 0 and len(words & sel_words) / len(words) > 0.5:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue

            # Domain coverage bonus
            new_domains = [d for d in item["domains"] if d and d not in covered_domains]
            if new_domains:
                item["score"] += 1

            covered_domains.update(item["domains"])
            selected.append(item)

        # Re-sort by final score and assign ranks
        selected.sort(key=lambda x: x["score"], reverse=True)
        result = []
        for i, item in enumerate(selected):
            result.append({
                "quote": item["quote"],
                "rank": i + 1,
                "score": item["score"],
                "domains": item["domains"],
            })

        return result

    def _select_narrative_memories(self, profile_dict: dict) -> list[dict]:
        """Select and deduplicate narrative memories.

        - Deduplicate by checking pairwise word overlap (>60% → drop shorter one)
        - Cap at 6 memories
        - Sort by domain diversity first, then emotional variety
        """
        memories = profile_dict.get("narrative_memories", [])
        if not memories:
            return []

        # Ensure we have dicts
        mem_dicts = []
        for m in memories:
            if isinstance(m, dict):
                mem_dicts.append(m)

        # Deduplicate by word overlap
        deduped = []
        for mem in mem_dicts:
            words = set(mem.get("memory", "").lower().split())
            is_dup = False
            for i, existing in enumerate(deduped):
                ex_words = set(existing.get("memory", "").lower().split())
                if len(words) > 0 and len(ex_words) > 0:
                    overlap = len(words & ex_words) / min(len(words), len(ex_words))
                    if overlap > 0.6:
                        # Keep the longer one
                        if len(mem.get("memory", "")) > len(existing.get("memory", "")):
                            deduped[i] = mem
                        is_dup = True
                        break
            if not is_dup:
                deduped.append(mem)

        # Sort by domain diversity then emotional variety
        seen_domains: set[str] = set()
        seen_tones: set[str] = set()
        priority = []
        remaining = []

        for mem in deduped:
            domain = mem.get("domain", "")
            tone = mem.get("emotional_tone", "")
            if domain not in seen_domains:
                priority.append(mem)
                seen_domains.add(domain)
                seen_tones.add(tone)
            elif tone not in seen_tones:
                priority.append(mem)
                seen_tones.add(tone)
            else:
                remaining.append(mem)

        result = (priority + remaining)[:6]
        return result

    def _assemble_voice_rules_reference(self, profile_dict: dict) -> str:
        """Assemble a compact text reference from enriched profile data.

        Deterministic — no LLM call. Stored in persona_full_text as a convenience view.
        """
        lines = []

        # Voice
        voice = profile_dict.get("voice_signature", {})
        if isinstance(voice, dict) and any(voice.values()):
            lines.append("VOICE:")
            if voice.get("tone_descriptors"):
                lines.append(f"- Tone: {', '.join(voice['tone_descriptors'])}")
            if voice.get("characteristic_phrases"):
                phrases = ', '.join(f'"{p}"' for p in voice["characteristic_phrases"])
                lines.append(f"- Phrases: {phrases}")
            if voice.get("hedging_style"):
                lines.append(f"- Hedging: {voice['hedging_style']}")
            if voice.get("explanation_style"):
                lines.append(f"- Explains by: {voice['explanation_style']}")

        # Rules
        rules = profile_dict.get("behavioral_rules", [])
        if rules:
            lines.append("")
            lines.append("RULES:")
            for r in rules:
                if isinstance(r, dict):
                    conf = r.get("confidence", 0)
                    lines.append(f"- When {r.get('condition', '?')} -> {r.get('behavior', '?')} ({conf})")

        # Tensions
        tensions = profile_dict.get("tensions", [])
        if tensions:
            lines.append("")
            lines.append("TENSIONS:")
            for t in tensions:
                if isinstance(t, dict):
                    lines.append(f"- {t.get('tension', '?')}")

        # Narrative memories
        selected_memories = profile_dict.get("selected_narrative_memories", [])
        if selected_memories:
            lines.append("")
            lines.append("NARRATIVE MEMORIES:")
            for m in selected_memories:
                if isinstance(m, dict):
                    tone = m.get("emotional_tone", "")
                    domain = m.get("domain", "")
                    lines.append(f"- {m.get('memory', '?')} [{tone}, {domain}]")

        # Exemplars
        ranked = profile_dict.get("ranked_exemplars", [])
        if ranked:
            lines.append("")
            lines.append("EXEMPLARS:")
            for e in ranked[:5]:
                if isinstance(e, dict):
                    lines.append(f'- "{e.get("quote", "")}"')

        return "\n".join(lines) if lines else ""

    def _calculate_simulation_readiness(
        self,
        profile_dict: dict,
        snippets: list,
        modules: list[str],
    ) -> dict:
        """Calculate simulation readiness across 5 dimensions.

        All calculated deterministically, no LLM call.
        Returns component scores and overall blended score.
        """
        # 1. Rule density: min(1.0, num_rules / 8)
        rules = profile_dict.get("behavioral_rules", [])
        rule_density = min(1.0, len(rules) / 8)

        # 2. Voice capture: proportion of voice_signature checks satisfied
        voice = profile_dict.get("voice_signature", {})
        if not isinstance(voice, dict):
            voice = {}
        voice_checks = 0
        if len(voice.get("tone_descriptors", [])) >= 3:
            voice_checks += 1
        if len(voice.get("characteristic_phrases", [])) >= 2:
            voice_checks += 1
        if voice.get("explanation_style"):
            voice_checks += 1
        if voice.get("hedging_style"):
            voice_checks += 1
        voice_capture = voice_checks / 4

        # 3. Grounding ratio: proportion of direct_quote snippets / 0.3 target
        total_snippets = len(snippets) if snippets else 0
        if total_snippets > 0:
            direct_count = sum(
                1 for s in snippets
                if hasattr(s, 'snippet_metadata') and
                isinstance(s.snippet_metadata, dict) and
                s.snippet_metadata.get("snippet_type") == "direct_quote"
            )
            ratio = direct_count / total_snippets
            grounding_ratio = min(1.0, ratio / 0.3)
        else:
            grounding_ratio = 0.0

        # 4. Tension coverage
        tensions = profile_dict.get("tensions", [])
        if tensions:
            tension_coverage = 1.0
        elif len(modules) < 6:
            tension_coverage = 0.5
        else:
            tension_coverage = 0.3

        # 5. Narrative richness: min(1.0, num_memories / 4) * diversity_bonus
        memories = profile_dict.get("narrative_memories", [])
        num_memories = len(memories)
        if num_memories > 0:
            base = min(1.0, num_memories / 4)
            unique_domains = len({
                m.get("domain", "") for m in memories if isinstance(m, dict)
            })
            diversity_bonus = min(1.0, unique_domains / num_memories) if num_memories > 0 else 0
            narrative_richness = base * diversity_bonus
        else:
            narrative_richness = 0.0

        # Overall blended score
        overall = (
            0.30 * rule_density
            + 0.20 * voice_capture
            + 0.20 * grounding_ratio
            + 0.15 * narrative_richness
            + 0.15 * tension_coverage
        )

        return {
            "rule_density": round(rule_density, 3),
            "voice_capture": round(voice_capture, 3),
            "grounding_ratio": round(grounding_ratio, 3),
            "narrative_richness": round(narrative_richness, 3),
            "tension_coverage": round(tension_coverage, 3),
            "overall": round(overall, 3),
        }

    def _calculate_quality_score(self, coverage_confidence: dict) -> float:
        """Calculate overall quality score as weighted average of module scores."""
        by_module = coverage_confidence.get("by_module", {})
        if not by_module:
            return 0.0

        # Weights: mandatory modules are more important
        weights = {
            "M1": 0.20, "M2": 0.25, "M3": 0.25, "M4": 0.20,
            "A1": 0.10, "A2": 0.10, "A3": 0.10, "A4": 0.10,
            "A5": 0.10, "A6": 0.08,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        for mid, data in by_module.items():
            w = weights.get(mid, 0.10)
            # Combined score = 60% coverage + 40% confidence
            score = 0.6 * data["coverage"] + 0.4 * data["confidence"]
            weighted_sum += w * score
            total_weight += w

        return round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0


# Singleton
_service: TwinGenerationService | None = None


def get_twin_generation_service() -> TwinGenerationService:
    """Get the singleton twin generation service."""
    global _service
    if _service is None:
        _service = TwinGenerationService()
    return _service
