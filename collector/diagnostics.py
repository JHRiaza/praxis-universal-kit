"""PRAXIS diagnostics — user-facing workflow observability insights.

Turns logged PRAXIS data into a compact personal diagnosis so participants
get immediate value from contributing to the study.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _pct(value: Optional[float]) -> Optional[int]:
    if value is None:
        return None
    return round(value * 100)


def _parse_ts(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_percent(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{round(value * 100)}%"


def build_user_diagnosis(
    entries: List[Dict[str, Any]],
    governance_events: Optional[List[Dict[str, Any]]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    governance_events = governance_events or []
    state = state or {}
    work_entries = [e for e in entries if e.get("type", "sprint") == "sprint"]

    if not work_entries:
        return {
            "ready": False,
            "headline": "Log a few real AI-assisted work sessions to unlock your workflow diagnosis.",
            "summary": "PRAXIS becomes useful once it can compare duration, quality, rework, trust, and session-boundary patterns.",
            "insights": [
                "You’ll see where your AI workflow costs time.",
                "You’ll see where trust may be too high or too low.",
                "You’ll get a longitudinal picture instead of one-off impressions.",
            ],
            "user_value": [
                "A mirror for your AI workflow",
                "Evidence about quality vs. rework",
                "Visible patterns you can act on later",
            ],
            "metrics": {},
        }

    total_entries = len(work_entries)
    durations = [e.get("duration_minutes", e.get("duration")) for e in work_entries if isinstance(e.get("duration_minutes", e.get("duration")), int)]
    qualities = [e.get("quality_self", e.get("quality")) for e in work_entries if isinstance(e.get("quality_self", e.get("quality")), int)]
    iterations = [e.get("iterations") for e in work_entries if isinstance(e.get("iterations"), int)]
    autonomy_values = [1 if e.get("autonomous") else 0 for e in work_entries if "autonomous" in e]
    interventions = [e.get("human_interventions", e.get("interventions")) for e in work_entries if isinstance(e.get("human_interventions", e.get("interventions")), int)]

    trust = []
    skepticism = []
    warmth = []
    confidence = []
    mismatch_count = 0
    degraded_boundaries = 0
    partial_boundaries = 0

    for entry in work_entries:
        l1r = entry.get("l1r_observations") or {}
        if isinstance(l1r.get("trust_willingness"), int):
            trust.append(l1r["trust_willingness"])
        if isinstance(l1r.get("skepticism_activation"), int):
            skepticism.append(l1r["skepticism_activation"])
        if isinstance(l1r.get("perceived_warmth"), int):
            warmth.append(l1r["perceived_warmth"])
        if isinstance(l1r.get("perceived_confidence"), int):
            confidence.append(l1r["perceived_confidence"])
        if l1r.get("personality_mismatch") is True:
            mismatch_count += 1

        boundary = entry.get("session_boundary") or {}
        if boundary.get("calibration_recovery") == "significant_degradation":
            degraded_boundaries += 1
        elif boundary.get("calibration_recovery") == "gradual":
            partial_boundaries += 1

    total_minutes = sum(durations)
    avg_quality = _mean([float(v) for v in qualities])
    avg_iterations = _mean([float(v) for v in iterations])
    avg_interventions = _mean([float(v) for v in interventions])
    autonomy_rate = _mean([float(v) for v in autonomy_values])
    avg_trust = _mean([float(v) for v in trust])
    avg_skepticism = _mean([float(v) for v in skepticism])
    avg_warmth = _mean([float(v) for v in warmth])
    avg_confidence = _mean([float(v) for v in confidence])

    first_ts = _parse_ts(work_entries[0].get("timestamp", ""))
    last_ts = _parse_ts(work_entries[-1].get("timestamp", ""))
    observation_days = 0
    if first_ts and last_ts:
        observation_days = max(1, (last_ts - first_ts).days + 1)

    insights: List[str] = []
    flags: List[str] = []

    if avg_iterations is not None and avg_iterations >= 3:
        insights.append(f"Your workflow shows notable rework drag ({avg_iterations:.1f} iterations per task on average).")
        flags.append("rework_drag")
    elif avg_iterations is not None:
        insights.append(f"Your workflow is relatively compact ({avg_iterations:.1f} iterations per task on average).")

    if autonomy_rate is not None and autonomy_rate < 0.5:
        insights.append(f"You are intervening often — autonomy is {_format_percent(autonomy_rate)}, so the AI is still leaning heavily on human correction.")
        flags.append("low_autonomy")
    elif autonomy_rate is not None:
        insights.append(f"Autonomy is {_format_percent(autonomy_rate)}, which helps reveal when AI can finish cleanly versus when it still needs steering.")

    if avg_trust is not None and avg_skepticism is not None:
        if avg_trust >= 5 and avg_skepticism <= 3:
            insights.append("Your logs suggest a possible over-trust zone: the AI feels persuasive before enough independent verification kicks in.")
            flags.append("over_trust")
        elif avg_skepticism >= 5 and avg_trust <= 4:
            insights.append("Your logs suggest a healthy skepticism pattern: you keep verification active even when the AI sounds confident.")
        else:
            insights.append("Trust and skepticism are both visible in the data, which makes the relational layer scientifically useful instead of anecdotal.")

    if degraded_boundaries > 0:
        insights.append(f"Session-boundary fragility is visible: {degraded_boundaries} sessions showed significant calibration degradation after context breaks or resets.")
        flags.append("session_fragility")
    elif partial_boundaries > 0:
        insights.append(f"Some continuity drag is already visible: {partial_boundaries} sessions recovered only gradually after session boundaries.")

    if governance_events:
        insights.append(f"Rules are not theoretical here — {len(governance_events)} governance events were logged, showing how structure emerges from real failure or escalation moments.")

    if mismatch_count > 0:
        insights.append(f"Personality portability is unstable in {mismatch_count} logged cases, which means the same governance setup does not always produce the same behavioral surface.")
        flags.append("personality_drift")

    if not insights:
        insights.append("Your current data already gives you a baseline picture of time, quality, and rework — enough to start seeing patterns instead of relying on memory.")

    user_value = [
        "See where AI saves time versus where it creates rework.",
        "Spot trust, confidence, and compliance patterns that usually stay invisible.",
        "Build a longitudinal evidence trail instead of judging one session at a time.",
    ]

    headline = "PRAXIS is giving you a workflow mirror, not just a research log."
    if "over_trust" in flags:
        headline = "PRAXIS is already revealing a trust calibration issue in your AI workflow."
    elif "rework_drag" in flags:
        headline = "PRAXIS is already showing where your AI workflow is leaking effort."
    elif "session_fragility" in flags:
        headline = "PRAXIS is already showing that session continuity is part of your quality problem."

    summary = (
        f"Based on {total_entries} logged sessions across {observation_days or 1} day(s), "
        f"PRAXIS can describe your workflow in terms of time, quality, rework, trust, and continuity."
    )

    return {
        "ready": True,
        "headline": headline,
        "summary": summary,
        "insights": insights[:5],
        "user_value": user_value,
        "flags": flags,
        "metrics": {
            "total_entries": total_entries,
            "total_minutes": total_minutes,
            "avg_quality": avg_quality,
            "avg_iterations": avg_iterations,
            "avg_interventions": avg_interventions,
            "autonomy_rate": autonomy_rate,
            "avg_trust": avg_trust,
            "avg_skepticism": avg_skepticism,
            "avg_warmth": avg_warmth,
            "avg_confidence": avg_confidence,
            "governance_events": len(governance_events),
            "degraded_boundaries": degraded_boundaries,
            "personality_mismatch_count": mismatch_count,
            "phase": state.get("phase"),
            "observation_days": observation_days,
        },
    }
