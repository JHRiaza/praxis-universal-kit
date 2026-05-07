"""PRAXIS LLM-as-Judge Module (v0.14.0)

Layer 2 of the cross-validation stack. Uses local Ollama to independently
assess governance signals in session entries. Compares against Layer 1 heuristics.

Requirements: Ollama running locally with a model loaded.
Default model: qwen3:4b (fits GTX 1080). Override via PRAXIS_JUDGE_MODEL env var.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_JUDGE_MODEL = os.environ.get("PRAXIS_JUDGE_MODEL", "qwen3:4b")


def _ollama_generate(prompt, model=DEFAULT_JUDGE_MODEL, timeout=120):
    # type: (str, str, int) -> Optional[str]
    """Call Ollama generate API. Returns response text or None on failure."""
    url = "{}/api/generate".format(OLLAMA_BASE.rstrip("/"))
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512}
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError):
        return None


def _build_judge_prompt(entry):
    # type: (Dict[str, Any]) -> str
    """Build a structured prompt for the LLM judge."""
    # Sanitize: remove PII fields
    pii_keys = {"task", "notes", "participant_id", "session_id", "raw_transcript",
                "heuristic_analysis", "gas_components", "cross_validation"}
    safe_entry = {k: v for k, v in entry.items()
                  if k not in pii_keys and not k.startswith("passive_")}

    return (
        "You are a governance pattern analyst. "
        "Analyze this AI-assisted work session and detect governance signals.\n\n"
        'A "governance signal" is evidence that a human actively managed, '
        "directed, corrected, or constrained AI behavior during this session.\n\n"
        "Session data (JSON):\n{}\n\n"
        "Respond with ONLY a JSON object (no markdown, no explanation):\n"
        '{{\n'
        '  "signals": ["signal_name_1", "signal_name_2"],\n'
        '  "governance_intensity": 0.0,\n'
        '  "reasoning": "brief explanation"\n'
        "}}\n\n"
        "Valid signal names: iteration_loop, human_override, governance_event, "
        "long_session, task_failure, active_steering, high_skepticism, "
        "quality_outcome_mismatch, delegation_chain, context_heavy, "
        "low_trust_verification\n\n"
        "governance_intensity: 0.0 (no governance) to 1.0 (heavy governance)\n"
    ).format(json.dumps(safe_entry, indent=2, default=str))


def judge_session(entry, model=DEFAULT_JUDGE_MODEL):
    # type: (Dict[str, Any], str) -> Dict[str, Any]
    """Run LLM-as-judge on a single session entry.

    Returns dict with judge_signals, governance_intensity, reasoning,
    judge_model, judge_success.
    """
    prompt = _build_judge_prompt(entry)
    response = _ollama_generate(prompt, model=model)

    if not response:
        return {
            "judge_signals": [],
            "governance_intensity": None,
            "reasoning": "LLM judge failed to respond",
            "judge_model": model,
            "judge_success": False,
        }

    # Parse response: try to extract JSON
    try:
        # Strip any markdown fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        return {
            "judge_signals": result.get("signals", []),
            "governance_intensity": float(result.get("governance_intensity", 0)),
            "reasoning": str(result.get("reasoning", "")),
            "judge_model": model,
            "judge_success": True,
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "judge_signals": [],
            "governance_intensity": None,
            "reasoning": "Failed to parse judge response: {}".format(response[:200]),
            "judge_model": model,
            "judge_success": False,
        }


def cross_validate(entry, heuristic_result=None, model=DEFAULT_JUDGE_MODEL, prefer_rule_based=False):
    # type: (Dict[str, Any], Optional[Dict[str, Any]], str, bool) -> Dict[str, Any]
    """Cross-validate heuristic detection against LLM judge.
    
    If prefer_rule_based=True or Ollama is unavailable, falls back to
    rule-based L2 judge (collector.rule_judge) for deterministic results.
    
    Returns dict with heuristic_signals, judge_signals, agreement_signals,
    disagreement sets, agreement_ratio, judge_result, cross_validation_version.
    """
    if heuristic_result is None:
        try:
            from collector.heuristics import detect_governance_signals
        except ImportError:
            from heuristics import detect_governance_signals
        heuristic_result = detect_governance_signals(entry)

    if prefer_rule_based:
        try:
            from collector.rule_judge import cross_validate_rule_based
        except ImportError:
            from rule_judge import cross_validate_rule_based
        result = cross_validate_rule_based(entry, heuristic_result=heuristic_result)
        result["judge_type"] = "rule_based_preferred"
        return result

    judge_result = judge_session(entry, model=model)

    # Fallback to rule-based if LLM failed
    if not judge_result["judge_success"]:
        try:
            from collector.rule_judge import rule_judge_session
        except ImportError:
            from rule_judge import rule_judge_session
        rule_result = rule_judge_session(entry)
        judge_result = rule_result
        judge_result["reasoning"] += " (rule-based fallback: LLM unavailable)"
        used_fallback = True
    else:
        used_fallback = False

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
        "judge_type": "rule_based_fallback" if used_fallback else "llm",
    }


def _count(items):
    # type: (List[str]) -> Dict[str, int]
    d = {}  # type: Dict[str, int]
    for i in items:
        d[i] = d.get(i, 0) + 1
    return d


def generate_cross_validation_report(entries, model=DEFAULT_JUDGE_MODEL, prefer_rule_based=False):
    # type: (List[Dict[str, Any]], str, bool) -> Dict[str, Any]
    """Generate a full cross-validation report for all entries with heuristic_analysis."""
    results = []  # type: List[Dict[str, Any]]
    for entry in entries:
        if entry.get("type") != "sprint" or not entry.get("heuristic_analysis"):
            continue
        cv = cross_validate(entry, heuristic_result=entry["heuristic_analysis"], model=model, prefer_rule_based=prefer_rule_based)
        results.append(cv)

    agreement_ratios = [r["agreement_ratio"] for r in results]
    all_agreement = [s for r in results for s in r["agreement_signals"]]
    all_h_only = [s for r in results for s in r["disagreement_heuristic_only"]]
    all_j_only = [s for r in results for s in r["disagreement_judge_only"]]
    success_rate = sum(1 for r in results if r["judge_result"]["judge_success"]) / max(len(results), 1)

    return {
        "total_entries": len(results),
        "judge_success_rate": round(success_rate, 2),
        "mean_agreement_ratio": round(sum(agreement_ratios) / max(len(agreement_ratios), 1), 2),
        "agreement_signal_distribution": _count(all_agreement),
        "heuristic_only_distribution": _count(all_h_only),
        "judge_only_distribution": _count(all_j_only),
        "model_used": model,
        "results": results,
    }


def check_ollama_available():
    # type: () -> Dict[str, Any]
    """Check if Ollama is running and what models are available."""
    url = "{}/api/tags".format(OLLAMA_BASE.rstrip("/"))
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "available": True,
                "models": models,
                "default_model": DEFAULT_JUDGE_MODEL,
                "model_ready": any(DEFAULT_JUDGE_MODEL in m for m in models),
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "default_model": DEFAULT_JUDGE_MODEL,
            "model_ready": False,
        }
