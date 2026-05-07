"""PRAXIS Heuristic Governance Detection Engine (v0.13.0)

Layer 1 of the cross-validation stack. Analyzes session metrics
to detect governance signals using interpretable rules. Zero ML.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def detect_governance_signals(entry):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Analyze a single session entry for governance signals.

    Returns a dict with:
    - signals: list of detected signal names
    - confidence: 0.0-1.0 how confident the detection is
    - details: per-signal explanation
    """
    signals = []  # type: List[str]
    details = {}  # type: Dict[str, Dict[str, Any]]

    iterations = entry.get("iterations", 1) or 1
    interventions = entry.get("human_interventions", entry.get("interventions", 0)) or 0
    duration = entry.get("duration_minutes", entry.get("duration", 0)) or 0
    quality = entry.get("quality_self", entry.get("quality", 0)) or 0
    outcome = entry.get("checkout_outcome", "")
    gov_tag = entry.get("governance_tag", "none") or "none"
    gas = entry.get("governance_activity_score")
    l1r = entry.get("l1r_observations") or {}
    steering = l1r.get("steering_intensity", 0)
    skepticism = l1r.get("skepticism_activation", 0)

    # H1: Iteration loop (>2 iterations suggests governance friction)
    if iterations > 2:
        signals.append("iteration_loop")
        details["iteration_loop"] = {
            "iterations": iterations,
            "reason": "{} AI generation cycles detected - suggests governance friction or unclear requirements".format(iterations)
        }

    # H2: Human override (any intervention)
    if interventions > 0:
        signals.append("human_override")
        details["human_override"] = {
            "interventions": interventions,
            "reason": "{} human correction(s)/override(s) detected".format(interventions)
        }

    # H3: Governance tag present
    if gov_tag and gov_tag != "none":
        signals.append("governance_event")
        details["governance_event"] = {
            "tag": gov_tag,
            "reason": "Participant tagged governance moment: {}".format(gov_tag)
        }

    # H4: Long session (>240 min)
    if duration > 240:
        signals.append("long_session")
        details["long_session"] = {
            "duration": duration,
            "reason": "Session lasted {} min (>4h) - potential scope expansion or context accumulation".format(duration)
        }

    # H5: Abandoned outcome
    if outcome == "abandoned":
        signals.append("task_failure")
        details["task_failure"] = {
            "reason": "Session outcome: abandoned - task could not be completed"
        }

    # H6: High steering (Likert >= 4)
    if isinstance(steering, int) and steering >= 4:
        signals.append("active_steering")
        details["active_steering"] = {
            "steering_intensity": steering,
            "reason": "Steering intensity {} >= 4 - human actively guided AI throughout".format(steering)
        }

    # H7: High skepticism (Likert >= 5)
    if isinstance(skepticism, int) and skepticism >= 5:
        signals.append("high_skepticism")
        details["high_skepticism"] = {
            "skepticism": skepticism,
            "reason": "Skepticism activation {} >= 5 - participant verified independently".format(skepticism)
        }

    # H8: Quality-outcome mismatch
    if outcome == "solved" and quality <= 2:
        signals.append("quality_outcome_mismatch")
        details["quality_outcome_mismatch"] = {
            "quality": quality,
            "outcome": outcome,
            "reason": "Outcome is 'solved' but quality rated {} - possible low-bar acceptance".format(quality)
        }
    elif outcome == "partial" and quality >= 4:
        signals.append("quality_outcome_mismatch")
        details["quality_outcome_mismatch"] = {
            "quality": quality,
            "outcome": outcome,
            "reason": "Outcome is 'partial' but quality rated {} - possible scope creep".format(quality)
        }

    # H9: GAS-based governance detection
    if gas is not None and gas > 0.6:
        signals.append("high_governance_activity")
        details["high_governance_activity"] = {
            "gas": gas,
            "reason": "GAS={:.3f} > 0.6 - substantial human governance detected".format(gas)
        }

    # Compute heuristic confidence
    signal_count = len(signals)
    if signal_count == 0:
        confidence = 0.0
    elif signal_count == 1:
        confidence = 0.4
    elif signal_count == 2:
        confidence = 0.7
    else:
        confidence = min(1.0, 0.7 + (signal_count - 2) * 0.1)

    return {
        "signals": signals,
        "signal_count": signal_count,
        "confidence": round(confidence, 2),
        "details": details,
        "heuristic_version": "1.0",
    }


def batch_analyze(entries):
    # type: (List[Dict[str, Any]]) -> Dict[str, Any]
    """Analyze a batch of entries and return aggregate heuristic report."""
    results = []  # type: List[Dict[str, Any]]
    signal_counts = {}  # type: Dict[str, int]
    total_with_signals = 0

    for entry in entries:
        if entry.get("type", "sprint") != "sprint":
            continue
        result = detect_governance_signals(entry)
        results.append(result)
        if result["signals"]:
            total_with_signals += 1
        for sig in result["signals"]:
            signal_counts[sig] = signal_counts.get(sig, 0) + 1

    return {
        "total_entries": len(results),
        "entries_with_signals": total_with_signals,
        "signal_distribution": signal_counts,
        "most_common_signal": max(signal_counts, key=signal_counts.get) if signal_counts else None,
        "results": results,
    }
