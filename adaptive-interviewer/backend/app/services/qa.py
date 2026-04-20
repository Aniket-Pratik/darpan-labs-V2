"""Automated data-quality checks — spec §11.

Run at finalize time against the full turn log. Returns a dict
reported in the output JSON's `qa` key + downstream filters.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any, Optional

from app.models import InterviewSession, InterviewTurn
from app.services.phase_defs import ItemDef, all_items
from app.services.state_machine import flatten_items


@dataclass
class QaFlag:
    key: str
    severity: str   # "info" | "warning" | "critical"
    detail: str


def _word_count(s: Optional[str]) -> int:
    if not s:
        return 0
    return len([w for w in s.strip().split() if w.strip()])


def _coverage(
    turns: list[InterviewTurn],
    archetype: Optional[str],
) -> tuple[float, list[str]]:
    items = flatten_items(archetype)
    missing: list[str] = []
    satisfied_codes = {
        t.module_id for t in turns
        if t.role == "interviewer"
        and (t.question_meta or {}).get("item_satisfied") is True
    }
    for item in items:
        if item.required and item.module_code not in satisfied_codes:
            missing.append(item.module_code)
    total_required = sum(1 for i in items if i.required)
    satisfied_required = total_required - len(missing)
    pct = (satisfied_required / total_required * 100.0) if total_required else 100.0
    return pct, missing


def _open_response_richness(turns: list[InterviewTurn]) -> dict[str, Any]:
    open_user_turns = [
        t for t in turns
        if t.role == "user"
        and t.answer_text
        and t.answer_structured is None
    ]
    wordcounts = [_word_count(t.answer_text) for t in open_user_turns]
    if not wordcounts:
        return {"median_words": 0, "mean_words": 0, "n_open_answers": 0, "low_engagement": False}
    med = median(wordcounts)
    return {
        "median_words": med,
        "mean_words": sum(wordcounts) / len(wordcounts),
        "n_open_answers": len(wordcounts),
        "low_engagement": med < 8,
    }


def _straight_lining(turns: list[InterviewTurn]) -> dict[str, Any]:
    """Flag 3+ consecutive identical slider values within any
    slider_battery or slider_matrix response."""
    found: list[dict[str, Any]] = []
    for t in turns:
        if t.role != "user" or not t.answer_structured:
            continue
        struct = t.answer_structured
        # BFI/PVQ typically shaped as {"responses": {"1": 5, "2": 3, ...}}
        resps = struct.get("responses")
        if isinstance(resps, dict):
            values = [v for _, v in sorted(resps.items(), key=lambda kv: str(kv[0]))]
            run = 1
            max_run = 1
            for i in range(1, len(values)):
                if values[i] == values[i - 1]:
                    run += 1
                    max_run = max(max_run, run)
                else:
                    run = 1
            if max_run >= 3:
                found.append({
                    "module_code": t.module_id,
                    "max_run": max_run,
                    "n_items": len(values),
                })
    return {"straight_line_runs": found, "flagged": bool(found)}


def _interviewer_drift(turns: list[InterviewTurn]) -> dict[str, Any]:
    long_utterances: list[dict[str, Any]] = []
    for t in turns:
        if t.role != "interviewer" or not t.question_text:
            continue
        wc = _word_count(t.question_text)
        if wc > 90:
            long_utterances.append({
                "module_code": t.module_id,
                "turn_index": t.turn_index,
                "word_count": wc,
            })
    return {"long_utterances": long_utterances, "flagged": bool(long_utterances)}


def _classification_confidence(session: InterviewSession) -> dict[str, Any]:
    classifications = list(session.classifications or [])
    if not classifications:
        return {"top_confidence": None, "flagged": True, "reason": "no_classification"}
    # Last classification wins (may be a reclassification).
    last = classifications[-1]
    probs = last.probs or {}
    top = max(probs.values()) if probs else 0.0
    return {
        "top_confidence": top,
        "primary": last.primary_archetype,
        "trigger": last.trigger,
        "is_hybrid": last.is_hybrid,
        "is_enterprise_flag": last.is_enterprise_flag,
        "flagged": top < 0.70,
    }


def _truncation(session: InterviewSession) -> dict[str, Any]:
    from datetime import datetime, timezone
    if session.started_at is None:
        return {"elapsed_sec": 0, "flagged": False}
    started = session.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    ended = session.ended_at or datetime.now(timezone.utc)
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)
    elapsed = int((ended - started).total_seconds())
    return {"elapsed_sec": elapsed, "flagged": elapsed > 65 * 60}


def _contradictions(turns: list[InterviewTurn]) -> dict[str, Any]:
    """Cheap heuristic contradiction check. A real implementation
    would pass the transcript to an LLM; for v1 we flag a couple of
    known-high-signal contradictions."""
    hits: list[str] = []
    combined = " ".join(
        (t.answer_text or "").lower()
        for t in turns if t.role == "user" and t.answer_text
    )
    if "self-employed" in combined and "it issued" in combined:
        hits.append("self_employed_and_it_issued")
    if "retired" in combined and ("i buy for the team" in combined or "my team" in combined):
        hits.append("retired_and_team_buyer")
    return {"hits": hits, "flagged": bool(hits)}


def run_qa(
    session: InterviewSession,
    turns: list[InterviewTurn],
    archetype: Optional[str],
) -> dict[str, Any]:
    coverage_pct, missing = _coverage(turns, archetype)
    open_richness = _open_response_richness(turns)
    straight = _straight_lining(turns)
    drift = _interviewer_drift(turns)
    classif = _classification_confidence(session)
    trunc = _truncation(session)
    contradictions = _contradictions(turns)

    flags: list[dict[str, str]] = []
    if missing:
        flags.append({"key": "coverage_missing", "severity": "critical",
                      "detail": f"{len(missing)} required items missing: {missing}"})
    if open_richness["low_engagement"]:
        flags.append({"key": "low_engagement", "severity": "warning",
                      "detail": f"median open answer = {open_richness['median_words']} words"})
    if straight["flagged"]:
        flags.append({"key": "straight_lining", "severity": "warning",
                      "detail": f"{len(straight['straight_line_runs'])} slider batteries with 3+ identical consecutive values"})
    if drift["flagged"]:
        flags.append({"key": "interviewer_drift", "severity": "info",
                      "detail": f"{len(drift['long_utterances'])} long interviewer utterances (>90 words)"})
    if classif["flagged"]:
        flags.append({"key": "low_classification_confidence", "severity": "warning",
                      "detail": f"top archetype confidence {classif.get('top_confidence')}"})
    if trunc["flagged"]:
        flags.append({"key": "truncated", "severity": "warning",
                      "detail": f"elapsed {trunc['elapsed_sec']}s over the 65-min hard budget"})
    if contradictions["flagged"]:
        flags.append({"key": "contradictions", "severity": "critical",
                      "detail": f"contradictions: {contradictions['hits']}"})

    return {
        "coverage_pct": coverage_pct,
        "missing_items": missing,
        "open_response_richness": open_richness,
        "straight_lining": straight,
        "interviewer_drift": drift,
        "classification": classif,
        "truncation": trunc,
        "contradictions": contradictions,
        "flags": flags,
        "human_review_required": any(f["severity"] == "critical" for f in flags),
    }
