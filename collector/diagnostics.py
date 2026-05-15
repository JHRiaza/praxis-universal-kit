"""PRAXIS diagnostics - user-facing workflow observability insights.

Turns logged PRAXIS data into a compact personal diagnosis so participants
get immediate value from contributing to the study.

v0.12.0: GAS replaces binary autonomy. L1-R filtering by l1r_source.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _mean(values):
    # type: (List[float]) -> Optional[float]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _pct(value):
    # type: (Optional[float]) -> Optional[int]
    if value is None:
        return None
    return round(value * 100)


def _parse_ts(ts):
    # type: (str) -> Optional[datetime]
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_percent(value):
    # type: (Optional[float]) -> str
    if value is None:
        return "n/a"
    return "{}%".format(round(value * 100))


def build_user_diagnosis(
    entries,  # type: List[Dict[str, Any]]
    governance_events=None,  # type: Optional[List[Dict[str, Any]]]
    state=None,  # type: Optional[Dict[str, Any]]
):
    # type: (...) -> Dict[str, Any]
    governance_events = governance_events or []
    state = state or {}
    work_entries = [e for e in entries if e.get("type", "sprint") == "sprint"]

    if not work_entries:
        return {
            "ready": False,
            "headline": "Log a few real AI-assisted work sessions to unlock your workflow diagnosis.",
            "summary": "PRAXIS becomes useful once it can compare duration, quality, rework, trust, and session-boundary patterns.",
            "insights": [
                "You'll see where your AI workflow costs time.",
                "You'll see where trust may be too high or too low.",
                "You'll get a longitudinal picture instead of one-off impressions.",
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
    interventions_list = [e.get("human_interventions", e.get("interventions")) for e in work_entries if isinstance(e.get("human_interventions", e.get("interventions")), int)]
    reliability_scores = [float(e.get("reliability_score")) for e in work_entries if isinstance(e.get("reliability_score"), (int, float))]

    # GAS (Governance Activity Score) - replaces binary autonomy
    gas_values = [e.get("governance_activity_score") for e in work_entries if e.get("governance_activity_score") is not None]

    passive_only_count = 0
    reviewed_count = 0
    manual_count = 0

    # L1-R: ONLY use observed/mixed values for Likert aggregations
    # Derived values are arithmetic identities, not psychological measurements
    trust = []
    skepticism = []
    warmth = []
    confidence = []
    mismatch_count = 0
    degraded_boundaries = 0
    partial_boundaries = 0

    for entry in work_entries:
        capture_mode = entry.get("capture_mode")
        if capture_mode == "passive_auto":
            passive_only_count += 1
        elif capture_mode in {"manual", "micro_checkout"}:
            manual_count += 1
        if entry.get("reviewed"):
            reviewed_count += 1

        # L1-R filtering: only use observed/mixed source
        l1r = entry.get("l1r_observations") or {}
        l1r_src = entry.get("l1r_source", "unknown")
        if l1r_src in ("observed", "mixed"):
            if isinstance(l1r.get("trust_willingness"), int):
                trust.append(l1r["trust_willingness"])
            if isinstance(l1r.get("skepticism_activation"), int):
                skepticism.append(l1r["skepticism_activation"])
            if isinstance(l1r.get("perceived_warmth"), int):
                warmth.append(l1r["perceived_warmth"])
            if isinstance(l1r.get("perceived_confidence"), int):
                confidence.append(l1r["perceived_confidence"])
        # personality_mismatch is not a Likert scale - safe to count from all sources
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
    avg_interventions = _mean([float(v) for v in interventions_list])
    avg_trust = _mean([float(v) for v in trust])
    avg_skepticism = _mean([float(v) for v in skepticism])
    avg_warmth = _mean([float(v) for v in warmth])
    avg_confidence = _mean([float(v) for v in confidence])
    avg_reliability = _mean(reliability_scores)

    # GAS-based governance activity
    gas_avg = _mean(gas_values) if gas_values else None

    first_ts = _parse_ts(work_entries[0].get("timestamp", ""))
    last_ts = _parse_ts(work_entries[-1].get("timestamp", ""))
    observation_days = 0
    if first_ts and last_ts:
        observation_days = max(1, (last_ts - first_ts).days + 1)

    insights = []  # type: List[str]
    flags = []  # type: List[str]

    if avg_iterations is not None and avg_iterations >= 3:
        insights.append("Your workflow shows notable rework drag ({:.1f} iterations per task on average).".format(avg_iterations))
        flags.append("rework_drag")
    elif avg_iterations is not None:
        insights.append("Your workflow is relatively compact ({:.1f} iterations per task on average).".format(avg_iterations))

    if passive_only_count > 0:
        insights.append(
            "{} session(s) were captured passively without checkout yet, so PRAXIS has timing evidence but still needs quick human calibration for stronger conclusions.".format(passive_only_count)
        )
        flags.append("needs_checkout")

    if avg_reliability is not None:
        if avg_reliability < 0.55:
            insights.append("Current evidence reliability is still light ({}%). Passive capture is working, but more micro-checkouts would make the diagnosis materially stronger.".format(round(avg_reliability * 100)))
            flags.append("low_reliability")
        else:
            insights.append("Data reliability is building ({}%), which means the workflow picture is becoming more defensible over time.".format(round(avg_reliability * 100)))

    # GAS-based governance activity insight (replaces binary autonomy)
    if gas_values:
        if gas_avg is not None and gas_avg > 0.6:
            insights.append("Governance activity is high (GAS={:.2f}/1.0) - you are actively steering the AI in most sessions.".format(gas_avg))
            flags.append("high_governance_activity")
        elif gas_avg is not None and gas_avg > 0.3:
            insights.append("Governance activity is moderate (GAS={:.2f}/1.0) - a mix of autonomous work and human steering.".format(gas_avg))
        elif gas_avg is not None:
            insights.append("Governance activity is low (GAS={:.2f}/1.0) - most sessions run autonomously after initial setup.".format(gas_avg))
    else:
        insights.append("Governance Activity Score not yet available - complete more checkouts with steering ratings to unlock this metric.")
        flags.append("needs_gas_data")

    # L1-R trust/skepticism insight (only from observed data)
    observed_l1r_count = len(trust)
    if avg_trust is not None and avg_skepticism is not None:
        if avg_trust >= 5 and avg_skepticism <= 3:
            insights.append("Your logs suggest a possible over-trust zone: the AI feels persuasive before enough independent verification kicks in.")
            flags.append("over_trust")
        elif avg_skepticism >= 5 and avg_trust <= 4:
            insights.append("Your logs suggest a healthy skepticism pattern: you keep verification active even when the AI sounds confident.")
        else:
            insights.append("Trust and skepticism are both visible in the data ({} observed rating(s), derived values excluded from averages), which makes the relational layer scientifically useful instead of anecdotal.".format(observed_l1r_count))
    elif observed_l1r_count == 0:
        insights.append("No directly observed L1-R ratings yet - use the full Likert checkout to generate relational governance data. Note: entries logged before v0.12 are excluded from L1-R averages for scientific validity.")

    if degraded_boundaries > 0:
        insights.append("Session-boundary fragility is visible: {} sessions showed significant calibration degradation after context breaks or resets.".format(degraded_boundaries))
        flags.append("session_fragility")
    elif partial_boundaries > 0:
        insights.append("Some continuity drag is already visible: {} sessions recovered only gradually after session boundaries.".format(partial_boundaries))

    if governance_events:
        insights.append("Rules are not theoretical here - {} governance events were logged, showing how structure emerges from real failure or escalation moments.".format(len(governance_events)))

    if mismatch_count > 0:
        insights.append("Personality portability is unstable in {} logged cases, which means the same governance setup does not always produce the same behavioral surface.".format(mismatch_count))
        flags.append("personality_drift")

    # Heuristic governance detection summary (v0.13.0)
    heuristic_entries = [e.get("heuristic_analysis") for e in work_entries if e.get("heuristic_analysis")]
    if heuristic_entries:
        total_signals = sum(h.get("signal_count", 0) for h in heuristic_entries)
        most_common = {}  # type: Dict[str, int]
        for h in heuristic_entries:
            for sig in h.get("signals", []):
                most_common[sig] = most_common.get(sig, 0) + 1
        if most_common:
            top_signal = max(most_common, key=most_common.get)
            insights.append("Heuristic governance detection found {} signals across {} sessions. Most common: {} ({}x).".format(
                total_signals, len(heuristic_entries), top_signal, most_common[top_signal]
            ))
            flags.append("heuristic_signals_detected")

    # Cross-validation summary (v0.14.0)
    cv_entries = [e for e in work_entries if e.get("cross_validation")]
    if cv_entries:
        ratios = [e["cross_validation"]["agreement_ratio"] for e in cv_entries
                   if isinstance(e.get("cross_validation"), dict)
                   and e["cross_validation"].get("agreement_ratio") is not None]
        if ratios:
            mean_ratio = sum(ratios) / len(ratios)
            verdict = ("Strong convergence." if mean_ratio > 0.7
                       else "Moderate divergence - heuristic rules may need calibration." if mean_ratio > 0.4
                       else "Significant divergence - investigate disagreements.")
            insights.append("Cross-validation (heuristic vs LLM judge) shows {:.0%} agreement across {} sessions. {}".format(
                mean_ratio, len(ratios), verdict
            ))

    if not insights:
        insights.append("Your current data already gives you a baseline picture of time, quality, and rework - enough to start seeing patterns instead of relying on memory.")

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
        "Based on {} logged sessions across {} day(s), "
        "PRAXIS can describe your workflow in terms of time, quality, rework, trust, and continuity."
    ).format(total_entries, observation_days or 1)

    return {
        "ready": True,
        "headline": headline,
        "summary": summary,
        "insights": insights[:8],
        "user_value": user_value,
        "flags": flags,
        "metrics": {
            "total_entries": total_entries,
            "total_minutes": total_minutes,
            "avg_quality": avg_quality,
            "avg_iterations": avg_iterations,
            "avg_interventions": avg_interventions,
            "governance_activity_avg": gas_avg,
            "gas_sample_size": len(gas_values),
            "avg_trust": avg_trust,
            "avg_skepticism": avg_skepticism,
            "avg_warmth": avg_warmth,
            "avg_confidence": avg_confidence,
            "avg_reliability": avg_reliability,
            "passive_only_count": passive_only_count,
            "reviewed_count": reviewed_count,
            "manual_or_checkout_count": manual_count,
            "governance_events": len(governance_events),
            "degraded_boundaries": degraded_boundaries,
            "personality_mismatch_count": mismatch_count,
            "observed_l1r_count": observed_l1r_count,
            "phase": state.get("phase", "obs"),
            "observation_days": observation_days,
        },
    }
