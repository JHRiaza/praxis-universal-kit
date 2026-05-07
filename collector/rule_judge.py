"""PRAXIS Rule-Based Second Judge (v0.14.1)

Deterministic alternative to LLM-as-Judge for Layer 2 cross-validation.
Uses a weighted scoring model with different logic than L1 heuristics,
providing a genuine second opinion without any LLM dependency.

Use cases:
- Participants without Ollama/GPU
- Batch processing where LLM latency is prohibitive  
- Reproducibility validation (deterministic, same input = same output)
- Scientific defensibility (fully interpretable weights)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Signal weights — different emphasis than L1 heuristics
# L1 fires on thresholds (iterations > 2, etc). L2 uses graduated scoring.
SIGNAL_WEIGHTS = {
    "iteration_loop": 0.15,       # per iteration above 1
    "human_override": 0.20,       # per intervention
    "governance_event": 0.25,     # flat if tagged
    "long_session": 0.10,         # per hour above 2
    "active_steering": 0.15,      # graduated from steering_intensity
    "high_skepticism": 0.10,      # graduated from skepticism_activation
    "context_heavy": 0.10,        # from context_provision_effort
    "delegation_chain": 0.08,     # from delegation_depth
    "low_trust_verification": 0.12,  # inverse of trust_willingness
    "quality_outcome_mismatch": 0.15,  # mismatch penalty
}

DETECTION_THRESHOLD = 0.20  # minimum weight to count as signal detected


def rule_judge_session(entry):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Rule-based second judge. Deterministic, interpretable, no LLM.
    
    Uses graduated scoring (not binary thresholds) so it produces
    different results than L1 heuristics — genuine second opinion.
    """
    signals = []  # type: List[str]
    details = {}  # type: Dict[str, Dict[str, Any]]
    
    iterations = entry.get("iterations", 1) or 1
    interventions = entry.get("human_interventions", entry.get("interventions", 0)) or 0
    duration = entry.get("duration_minutes", entry.get("duration", 0)) or 0
    quality = entry.get("quality_self", entry.get("quality", 0)) or 0
    outcome = entry.get("checkout_outcome", "")
    gov_tag = entry.get("governance_tag", "none") or "none"
    l1r = entry.get("l1r_observations") or {}
    steering = l1r.get("steering_intensity", 0) or 0
    skepticism = l1r.get("skepticism_activation", 0) or 0
    trust = l1r.get("trust_willingness", 0) or 0
    context_effort = entry.get("context_provision_effort", 0) or 0
    delegation = entry.get("delegation_depth", 0) or 0
    gas = entry.get("governance_activity_score")
    
    # S1: Iteration loop — graduated (0.15 per iteration above 1)
    if iterations > 1:
        weight = min(1.0, (iterations - 1) * SIGNAL_WEIGHTS["iteration_loop"])
        if weight >= DETECTION_THRESHOLD:
            signals.append("iteration_loop")
            details["iteration_loop"] = {
                "weight": round(weight, 3),
                "iterations": iterations,
                "reason": "Graduated: {} cycles above baseline (weight={:.3f})".format(iterations - 1, weight)
            }
    
    # S2: Human override — graduated (0.20 per intervention)
    if interventions > 0:
        weight = min(1.0, interventions * SIGNAL_WEIGHTS["human_override"])
        if weight >= DETECTION_THRESHOLD:
            signals.append("human_override")
            details["human_override"] = {
                "weight": round(weight, 3),
                "interventions": interventions,
                "reason": "Graduated: {} interventions (weight={:.3f})".format(interventions, weight)
            }
    
    # S3: Governance event — flat weight if tagged
    if gov_tag != "none":
        weight = SIGNAL_WEIGHTS["governance_event"]
        signals.append("governance_event")
        details["governance_event"] = {
            "weight": round(weight, 3),
            "tag": gov_tag,
            "reason": "Tagged: {} (flat weight={:.3f})".format(gov_tag, weight)
        }
    
    # S4: Long session — graduated (0.10 per hour above 2)
    hours = duration / 60.0
    if hours > 2:
        weight = min(1.0, (hours - 2) * SIGNAL_WEIGHTS["long_session"])
        if weight >= DETECTION_THRESHOLD:
            signals.append("long_session")
            details["long_session"] = {
                "weight": round(weight, 3),
                "hours": round(hours, 1),
                "reason": "Graduated: {:.1f}h above 2h threshold (weight={:.3f})".format(hours - 2, weight)
            }
    
    # S5: Active steering — graduated from Likert
    if isinstance(steering, int) and steering >= 2:
        weight = min(1.0, (steering - 1) / 4.0 * SIGNAL_WEIGHTS["active_steering"] * 5)
        if weight >= DETECTION_THRESHOLD:
            signals.append("active_steering")
            details["active_steering"] = {
                "weight": round(weight, 3),
                "steering_intensity": steering,
                "reason": "Graduated: steering={} (weight={:.3f})".format(steering, weight)
            }
    
    # S6: High skepticism — graduated from Likert
    if isinstance(skepticism, int) and skepticism >= 3:
        weight = min(1.0, (skepticism - 2) / 5.0 * SIGNAL_WEIGHTS["high_skepticism"] * 5)
        if weight >= DETECTION_THRESHOLD:
            signals.append("high_skepticism")
            details["high_skepticism"] = {
                "weight": round(weight, 3),
                "skepticism": skepticism,
                "reason": "Graduated: skepticism={} (weight={:.3f})".format(skepticism, weight)
            }
    
    # S7: Context heavy — from context_provision_effort
    if isinstance(context_effort, int) and context_effort >= 3:
        weight = min(1.0, (context_effort - 2) / 3.0 * SIGNAL_WEIGHTS["context_heavy"] * 4)
        if weight >= DETECTION_THRESHOLD:
            signals.append("context_heavy")
            details["context_heavy"] = {
                "weight": round(weight, 3),
                "context_effort": context_effort,
                "reason": "Graduated: context effort={} (weight={:.3f})".format(context_effort, weight)
            }
    
    # S8: Delegation chain
    if isinstance(delegation, int) and delegation >= 1:
        weight = min(1.0, delegation * SIGNAL_WEIGHTS["delegation_chain"])
        if weight >= DETECTION_THRESHOLD:
            signals.append("delegation_chain")
            details["delegation_chain"] = {
                "weight": round(weight, 3),
                "delegation_depth": delegation,
                "reason": "Graduated: depth={} (weight={:.3f})".format(delegation, weight)
            }
    
    # S9: Low trust verification — inverse of trust_willingness
    if isinstance(trust, int) and trust <= 3:
        weight = min(1.0, (4 - trust) / 3.0 * SIGNAL_WEIGHTS["low_trust_verification"] * 3)
        if weight >= DETECTION_THRESHOLD:
            signals.append("low_trust_verification")
            details["low_trust_verification"] = {
                "weight": round(weight, 3),
                "trust": trust,
                "reason": "Graduated: trust={} (low, weight={:.3f})".format(trust, weight)
            }
    
    # S10: Quality-outcome mismatch
    if (outcome == "solved" and quality <= 2) or (outcome == "partial" and quality >= 4):
        weight = SIGNAL_WEIGHTS["quality_outcome_mismatch"]
        signals.append("quality_outcome_mismatch")
        details["quality_outcome_mismatch"] = {
            "weight": round(weight, 3),
            "quality": quality,
            "outcome": outcome,
            "reason": "Mismatch: outcome={}, quality={} (weight={:.3f})".format(outcome, quality, weight)
        }
    
    # Compute governance intensity (weighted sum, normalized)
    total_weight = sum(details.get(s, {}).get("weight", 0) for s in signals)
    intensity = min(1.0, total_weight)
    
    return {
        "judge_signals": signals,
        "governance_intensity": round(intensity, 3),
        "reasoning": "Rule-based L2: {} signals detected, total weight={:.3f}".format(len(signals), total_weight),
        "judge_model": "rule_based_v1",
        "judge_success": True,
        "details": details,
    }


def cross_validate_rule_based(entry, heuristic_result=None):
    # type: (Dict[str, Any], Optional[Dict[str, Any]]) -> Dict[str, Any]
    """Cross-validate L1 heuristics against rule-based L2 judge.
    
    Identical interface to llm_judge.cross_validate() but uses
    deterministic rule-based judge instead of Ollama.
    """
    if heuristic_result is None:
        try:
            from collector.heuristics import detect_governance_signals
        except ImportError:
            from heuristics import detect_governance_signals
        heuristic_result = detect_governance_signals(entry)
    
    judge_result = rule_judge_session(entry)
    
    h_signals = set(heuristic_result.get("signals", []))
    j_signals = set(judge_result.get("judge_signals", []))
    
    agreement = h_signals & j_signals
    h_only = h_signals - j_signals
    j_only = j_signals - h_signals
    
    total_unique = len(h_signals | j_signals)
    agreement_ratio = len(agreement) / total_unique if total_unique > 0 else 1.0
    
    return {
        "heuristic_signals": sorted(h_signals),
        "judge_signals": sorted(j_signals),
        "agreement_signals": sorted(agreement),
        "disagreement_heuristic_only": sorted(h_only),
        "disagreement_judge_only": sorted(j_only),
        "agreement_ratio": round(agreement_ratio, 2),
        "judge_result": judge_result,
        "cross_validation_version": "1.0",
        "judge_type": "rule_based",
    }
