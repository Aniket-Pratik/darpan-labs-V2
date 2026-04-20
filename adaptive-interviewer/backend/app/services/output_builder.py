"""Assemble the final per-respondent output JSON.

Inputs: full InterviewSession (with classifications), all turns,
optional LLM-synthesized narrative summaries. Output shape follows
spec §3.2 with top-level keys context / archetype / jtbd / conjoint
/ brand_lattice / personality / values / identity / tone_preference
/ projective / qa.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from app.models import AdaptiveOutput, InterviewSession, InterviewTurn
from app.services import conjoint as cj
from app.services.phase_defs import Archetype, all_items
from app.services.qa import run_qa

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
_BFI = json.loads((DATA_DIR / "bfi_2s_items.json").read_text())
_PVQ = json.loads((DATA_DIR / "pvq10_items.json").read_text())
_IDENTITY = json.loads((DATA_DIR / "identity_adjectives.json").read_text())
_BRAND_LATTICE = json.loads((DATA_DIR / "brand_lattice.json").read_text())
_TONE_PAIRS = json.loads((DATA_DIR / "tone_pairs.json").read_text())


def _by_module(turns: list[InterviewTurn]) -> dict[str, list[InterviewTurn]]:
    g: dict[str, list[InterviewTurn]] = defaultdict(list)
    for t in turns:
        g[t.module_id].append(t)
    return g


def _answer_text(turns: list[InterviewTurn], module_code: str) -> str:
    for t in turns:
        if t.module_id == module_code and t.role == "user" and t.answer_text:
            return t.answer_text
    return ""


def _answer_structured(turns: list[InterviewTurn], module_code: str) -> Optional[dict]:
    for t in turns:
        if t.module_id == module_code and t.role == "user" and t.answer_structured:
            return t.answer_structured
    return None


def _build_context(turns: list[InterviewTurn]) -> dict[str, Any]:
    preamble = {
        "P1_role": _answer_text(turns, "P1"),
        "P2_device_landscape": _answer_text(turns, "P2"),
        "P3_last_purchase": _answer_text(turns, "P3"),
        "P4_decision_unit": _answer_text(turns, "P4"),
        "P5_process_formality": _answer_text(turns, "P5"),
        "P6_engagement": _answer_text(turns, "P6"),
    }
    disambig = []
    for t in turns:
        if t.module_id.startswith("P2D") and t.role == "user" and t.answer_text:
            disambig.append({"module_code": t.module_id, "answer": t.answer_text})
    return {"preamble": preamble, "disambiguation": disambig}


def _build_archetype(session: InterviewSession) -> dict[str, Any]:
    classifications = list(session.classifications or [])
    latest = classifications[-1] if classifications else None
    history = [
        {
            "sequence_index": c.sequence_index,
            "trigger": c.trigger,
            "probs": c.probs,
            "primary": c.primary_archetype,
            "secondary": c.secondary_archetype,
            "is_hybrid": c.is_hybrid,
            "is_enterprise_flag": c.is_enterprise_flag,
            "rationale": c.rationale,
        }
        for c in classifications
    ]
    return {
        "primary": latest.primary_archetype if latest else None,
        "secondary": latest.secondary_archetype if latest else None,
        "probs": latest.probs if latest else None,
        "is_hybrid": latest.is_hybrid if latest else False,
        "is_enterprise_flag": latest.is_enterprise_flag if latest else False,
        "history": history,
    }


def _jtbd_codes(archetype: Optional[Archetype]) -> list[str]:
    if archetype == "prosumer":
        return [f"A_J{i}" for i in range(1, 9)]
    if archetype == "smb_it":
        return [f"B_J{i}" for i in range(1, 9)]
    if archetype == "consumer":
        return [f"C_J{i}" for i in range(1, 10)]
    return []


def _build_jtbd(turns: list[InterviewTurn], archetype: Optional[Archetype]) -> dict[str, Any]:
    codes = _jtbd_codes(archetype)
    qa_pairs = []
    for code in codes:
        qa_pairs.append({
            "code": code,
            "answer": _answer_text(turns, code),
        })
    summary_code = codes[-1] if codes else None
    synthesis_answer = _answer_text(turns, summary_code) if summary_code else ""
    return {
        "raw_qa": qa_pairs,
        "narrative_synthesis": synthesis_answer,
        "archetype": archetype,
    }


def _conjoint_codes(archetype: Optional[Archetype]) -> list[str]:
    prefix = {"prosumer": "A", "smb_it": "B", "consumer": "C"}.get(archetype or "")
    if not prefix:
        return []
    return [f"{prefix}_C{i+1}" for i in range(8)]


def _build_conjoint(turns: list[InterviewTurn], archetype: Optional[Archetype], session_id) -> dict[str, Any]:
    if archetype is None:
        return {}
    codes = _conjoint_codes(archetype)
    choices: list[dict[str, Any]] = []
    by_module = _by_module(turns)

    for code in codes:
        # Widget was stored on the interviewer turn; answer on user turn.
        alts: list[dict[str, Any]] = []
        chosen_alt_index: int = -1
        for t in by_module.get(code, []):
            if t.role == "interviewer" and t.question_meta:
                widget = t.question_meta.get("widget") or {}
                if widget.get("type") == "conjoint":
                    alts = [a["attributes"] for a in widget.get("alternatives", [])]
            if t.role == "user" and t.answer_structured:
                chosen_alt_index = int(t.answer_structured.get("chosen_alt_index", -1))
        if not alts:
            # Fallback: regenerate deterministically from session id.
            try:
                idx = int(code.split("_C")[1]) - 1
                cs = cj.generate_choice_set(archetype, session_id, idx)
                alts = [a["attributes"] for a in cs.alternatives]
            except Exception as e:
                logger.warning(f"Could not reconstruct conjoint set {code}: {e}")
                continue
        choices.append({
            "code": code,
            "alternatives": alts,
            "chosen_alt_index": chosen_alt_index,
        })

    estimation = cj.estimate_part_worths(choices, archetype)
    return {
        "archetype": archetype,
        "raw_choices": choices,
        **estimation,
    }


def _build_brand_lattice(turns: list[InterviewTurn], archetype: Optional[Archetype]) -> dict[str, Any]:
    if archetype is None:
        return {}
    prefix = {"prosumer": "A", "smb_it": "B", "consumer": "C"}[archetype]
    b1 = _answer_text(turns, f"{prefix}_B1")
    b2_struct = _answer_structured(turns, f"{prefix}_B2") or {}
    lattice_def = _BRAND_LATTICE.get(archetype, {})
    return {
        "archetype": archetype,
        "unaided_recall": b1,
        "slider_matrix_raw": b2_struct,
        "brands": lattice_def.get("brands", []),
        "attributes": lattice_def.get("attributes", []),
    }


def _score_bfi(struct: Optional[dict]) -> dict[str, Any]:
    if not struct:
        return {}
    responses = struct.get("responses") or {}
    per_trait: dict[str, list[int]] = defaultdict(list)
    items_by_n = {item["n"]: item for item in _BFI["items"]}
    for n_str, val in responses.items():
        n = int(n_str)
        item = items_by_n.get(n)
        if not item:
            continue
        v = int(val)
        if item["reversed"]:
            v = 6 - v  # reverse 1..5 -> 5..1
        per_trait[item["trait"]].append(v)
    scores = {
        trait: round(sum(vs) / len(vs), 3) if vs else None
        for trait, vs in per_trait.items()
    }
    return {
        "trait_scores": scores,
        "trait_labels": _BFI["trait_labels"],
        "n_items_answered": len(responses),
    }


def _build_personality(turns: list[InterviewTurn]) -> dict[str, Any]:
    struct = _answer_structured(turns, "F_BFI") or {}
    scored = _score_bfi(struct)
    return {
        "instrument": "BFI-2-S",
        "citation": _BFI["citation"],
        "raw_responses": struct.get("responses", {}),
        **scored,
    }


def _score_pvq(struct: Optional[dict]) -> dict[str, Any]:
    if not struct:
        return {}
    responses = struct.get("responses") or {}
    per_value: dict[str, int] = {}
    higher_order: dict[str, list[int]] = defaultdict(list)
    items_by_n = {item["n"]: item for item in _PVQ["items"]}
    for n_str, val in responses.items():
        n = int(n_str)
        item = items_by_n.get(n)
        if not item:
            continue
        per_value[item["value"]] = int(val)
        higher_order[item["higher_order"]].append(int(val))
    higher_means = {k: round(sum(v) / len(v), 3) for k, v in higher_order.items() if v}
    return {
        "basic_value_scores": per_value,
        "higher_order_scores": higher_means,
        "value_labels": _PVQ["value_labels"],
        "n_items_answered": len(responses),
    }


def _build_values(turns: list[InterviewTurn]) -> dict[str, Any]:
    struct = _answer_structured(turns, "F_PVQ") or {}
    scored = _score_pvq(struct)
    return {
        "instrument": "PVQ-10",
        "citation": _PVQ["citation"],
        "raw_responses": struct.get("responses", {}),
        **scored,
    }


def _build_identity(turns: list[InterviewTurn]) -> dict[str, Any]:
    struct = _answer_structured(turns, "F_RANK") or {}
    ranking = struct.get("ranking") or []
    axes = _IDENTITY.get("identity_axes", {})
    axis_scores: dict[str, float] = {}
    for axis_name, tagged in axes.items():
        # rank-weighted score: rank 1 gets weight 5, rank 5 gets weight 1
        total = 0.0
        for position, adj in enumerate(ranking[:5]):
            if adj in tagged:
                total += (5 - position)
        axis_scores[axis_name] = total
    return {
        "ranking_top_5": ranking[:5],
        "full_ranking": ranking,
        "axis_scores": axis_scores,
    }


def _build_tone_preference(turns: list[InterviewTurn], archetype: Optional[Archetype]) -> dict[str, Any]:
    if archetype is None:
        return {}
    prefix = {"prosumer": "A", "smb_it": "B", "consumer": "C"}[archetype]
    pairs_def = _TONE_PAIRS.get(archetype, {})
    def _pair(code: str, pair_key: str):
        struct = _answer_structured(turns, code) or {}
        return {
            "code": code,
            "chosen_ad_id": struct.get("chosen_ad_id"),
            "why_text": struct.get("why_text") or _answer_text(turns, code),
            "pair_definition": pairs_def.get(pair_key, {}),
        }
    return {
        "archetype": archetype,
        "pair_a": _pair(f"{prefix}_T1", "pair_a"),
        "pair_b": _pair(f"{prefix}_T2", "pair_b"),
    }


def _build_projective(turns: list[InterviewTurn], archetype: Optional[Archetype]) -> dict[str, Any]:
    if archetype is None:
        return {}
    prefix = {"prosumer": "A", "smb_it": "B", "consumer": "C"}[archetype]
    return {
        "archetype": archetype,
        "peer_advice_text": _answer_text(turns, f"{prefix}_T3"),
    }


def build_output(
    session: InterviewSession,
    turns: list[InterviewTurn],
) -> dict[str, Any]:
    archetype: Optional[Archetype] = (session.settings or {}).get("archetype")
    return {
        "session_id": str(session.id),
        "archetype": _build_archetype(session),
        "context": _build_context(turns),
        "jtbd": _build_jtbd(turns, archetype),
        "conjoint": _build_conjoint(turns, archetype, session.id),
        "brand_lattice": _build_brand_lattice(turns, archetype),
        "personality": _build_personality(turns),
        "values": _build_values(turns),
        "identity": _build_identity(turns),
        "tone_preference": _build_tone_preference(turns, archetype),
        "projective": _build_projective(turns, archetype),
        "qa": run_qa(session, turns, archetype),
    }


async def persist_output(session: InterviewSession, output: dict[str, Any], db) -> AdaptiveOutput:
    row = AdaptiveOutput(
        session_id=session.id,
        context=output.get("context"),
        archetype=output.get("archetype"),
        jtbd=output.get("jtbd"),
        conjoint=output.get("conjoint"),
        brand_lattice=output.get("brand_lattice"),
        personality=output.get("personality"),
        values=output.get("values"),
        identity=output.get("identity"),
        tone_preference=output.get("tone_preference"),
        projective=output.get("projective"),
        qa=output.get("qa"),
    )
    db.add(row)
    await db.flush()
    return row
