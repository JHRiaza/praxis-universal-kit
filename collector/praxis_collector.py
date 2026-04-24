"""
PRAXIS Universal Kit — Core Data Collector
==========================================
Handles all data persistence for the PRAXIS research kit.
Reads/writes .praxis/ directory, manages state, validates metrics.

Python 3.8+ compatible. Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KIT_VERSION = "0.2"
SCHEMA_VERSION = "0.2"
PRAXIS_DIR = ".praxis"
STATE_FILE = "state.json"
METRICS_FILE = "metrics.jsonl"
GOVERNANCE_FILE = "governance.jsonl"
SESSIONS_FILE = "sessions.jsonl"

VALID_CONDITIONS = ("A1", "A2", "B1", "B2")
VALID_PHASES = ("A", "B")
VALID_LAYERS = ("L1", "L1-R", "L2", "L3", "L4", "L5")
VALID_ITERATION_TYPES = (
    "implementation",
    "debug",
    "refactor",
    "research",
    "design_cycle",
    "playtest",
    "revision",
    "refinement",
)
VALID_GOVERNANCE_TYPES = (
    "rule_created",
    "rule_modified",
    "rule_deleted",
    "incident",
    "escalation",
    "other",
)
VALID_INCIDENT_CATEGORIES = ("OPS", "GOV", "COM", "PRD", "RES", "DES")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class PraxisError(Exception):
    """Base exception for all PRAXIS collector errors."""


class StateNotFoundError(PraxisError):
    """Raised when .praxis/state.json does not exist."""


class InvalidPhaseError(PraxisError):
    """Raised when an operation is not valid in the current phase."""


class ValidationError(PraxisError):
    """Raised when a metrics entry fails validation."""


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def find_praxis_dir(start: Optional[Path] = None) -> Optional[Path]:
    """
    Walk up from `start` (default: cwd) looking for a .praxis/ directory.
    Returns the Path to .praxis/ if found, None otherwise.
    """
    current = Path(start or Path.cwd()).resolve()
    for directory in [current] + list(current.parents):
        candidate = directory / PRAXIS_DIR
        if candidate.is_dir() and (candidate / STATE_FILE).is_file():
            return candidate
    return None


def get_or_create_praxis_dir(project_dir: Optional[Path] = None) -> Path:
    """Return the .praxis/ dir under project_dir, creating it if needed."""
    root = Path(project_dir or Path.cwd()).resolve()
    praxis_path = root / PRAXIS_DIR
    praxis_path.mkdir(parents=True, exist_ok=True)
    return praxis_path


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _default_state(participant_id: str, consent_given: bool = False) -> Dict[str, Any]:
    now = _now_iso()
    return {
        "kit_version": KIT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "participant_id": participant_id,
        "phase": "A",
        "installed_at": now,
        "activated_at": None,
        "consent_given": consent_given,
        "consent_given_at": now if consent_given else None,
        "pre_survey_completed": False,
        "post_survey_completed": False,
        "platform_ids": [],
        "session_count": 0,
        "last_active": now,
        "withdrawn": False,
    }


def load_state(praxis_dir: Path) -> Dict[str, Any]:
    """Load state.json from the given .praxis/ directory."""
    state_path = praxis_dir / STATE_FILE
    if not state_path.is_file():
        raise StateNotFoundError(
            f"No PRAXIS state found at {state_path}. "
            "Run 'praxis status' from your project directory."
        )
    try:
        with state_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise PraxisError(f"Failed to read state file: {exc}") from exc


def save_state(praxis_dir: Path, state: Dict[str, Any]) -> None:
    """Write state to state.json atomically (write-then-rename)."""
    state_path = praxis_dir / STATE_FILE
    tmp_path = state_path.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        tmp_path.replace(state_path)
    except OSError as exc:
        raise PraxisError(f"Failed to write state file: {exc}") from exc


def initialize_state(
    praxis_dir: Path,
    participant_id: str,
    consent_given: bool = False,
) -> Dict[str, Any]:
    """Create a fresh state.json. Raises if one already exists."""
    state_path = praxis_dir / STATE_FILE
    if state_path.is_file():
        raise PraxisError(
            "PRAXIS is already initialized in this directory. "
            "Use 'praxis status' to check the current state."
        )
    state = _default_state(participant_id, consent_given)
    save_state(praxis_dir, state)
    return state


def touch_last_active(praxis_dir: Path) -> None:
    """Update last_active and increment session_count."""
    try:
        state = load_state(praxis_dir)
        state["last_active"] = _now_iso()
        state["session_count"] = state.get("session_count", 0) + 1
        save_state(praxis_dir, state)
    except PraxisError:
        pass  # Don't crash on touch failure


# ---------------------------------------------------------------------------
# Participant ID generation
# ---------------------------------------------------------------------------

def generate_participant_id() -> str:
    """
    Generate a deterministic-but-anonymous participant ID.
    Uses machine-specific data hashed to produce a stable 6-char suffix.
    Format: PRAXIS-XXXXXXXX (8 hex chars from SHA-256 of machine identity).
    """
    try:
        # Combine platform info for a stable hash seed
        seed_parts = [
            platform.node(),
            str(uuid.getnode()),  # MAC address as integer
            platform.system(),
            platform.machine(),
        ]
        seed = "|".join(seed_parts).encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()[:8].upper()
        return f"PRAXIS-{digest}"
    except Exception:
        # Fallback: random ID
        return f"PRAXIS-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Metrics logging
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_entry_id(task: str) -> str:
    """Generate a unique, readable entry ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    # Slugify the task description
    slug = re.sub(r"[^a-z0-9]+", "_", task.lower().strip())[:40].strip("_")
    return f"praxis_{ts}_{slug}"


def _get_git_commit(project_dir: Optional[Path] = None) -> Optional[str]:
    """Attempt to get the current git commit hash. Returns None on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_dir or Path.cwd()),
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _get_session_id(state: Dict[str, Any]) -> str:
    """Generate a session ID based on date and session count."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = state.get("session_count", 0)
    return f"session_{date_str}_{count:04d}"


def _derive_condition(state: Dict[str, Any], model: str) -> str:
    """Map legacy phase/model inputs to v0.2 2x2 experimental condition."""
    condition = state.get("condition")
    if condition in VALID_CONDITIONS:
        return condition

    structure = "B" if state.get("phase") == "B" else "A"
    model_name = model.lower()
    model_axis = "2" if "opus" in model_name else "1"
    return f"{structure}{model_axis}"


def validate_metric_entry(entry: Dict[str, Any]) -> List[str]:
    """
    Validate a metrics entry against the schema.
    Returns a list of validation error messages (empty = valid).
    """
    errors: List[str] = []
    required_fields = [
        "id", "timestamp", "participant_id", "condition", "task",
        "duration_minutes", "quality_self",
    ]
    for field in required_fields:
        if field not in entry:
            errors.append(f"Missing required field: '{field}'")

    if "phase" in entry and entry["phase"] not in VALID_PHASES:
        errors.append(f"Invalid phase '{entry['phase']}'. Must be one of: {VALID_PHASES}")

    if "condition" in entry and entry["condition"] not in VALID_CONDITIONS:
        errors.append(
            f"Invalid condition '{entry['condition']}'. Must be one of: {VALID_CONDITIONS}"
        )

    if "quality" in entry:
        q = entry["quality"]
        if not isinstance(q, int) or not (1 <= q <= 5):
            errors.append(f"'quality' must be an integer 1-5, got: {q!r}")

    if "quality_self" in entry:
        q = entry["quality_self"]
        if not isinstance(q, int) or not (1 <= q <= 5):
            errors.append(f"'quality_self' must be an integer 1-5, got: {q!r}")

    if "quality_external" in entry and entry["quality_external"] is not None:
        q = entry["quality_external"]
        if not isinstance(q, int) or not (1 <= q <= 5):
            errors.append(f"'quality_external' must be an integer 1-5, got: {q!r}")

    if "duration" in entry:
        d = entry["duration"]
        if not isinstance(d, int) or d < 1:
            errors.append(f"'duration' must be a positive integer (minutes), got: {d!r}")

    if "duration_minutes" in entry:
        d = entry["duration_minutes"]
        if not isinstance(d, int) or d < 1:
            errors.append(f"'duration_minutes' must be a positive integer, got: {d!r}")

    if "iterations" in entry:
        i = entry["iterations"]
        if not isinstance(i, int) or i < 1:
            errors.append(f"'iterations' must be a positive integer, got: {i!r}")

    if "iteration_type" in entry and entry["iteration_type"] is not None:
        iteration_type = entry["iteration_type"]
        if iteration_type not in VALID_ITERATION_TYPES:
            errors.append(
                f"'iteration_type' must be one of {VALID_ITERATION_TYPES}, got: {iteration_type!r}"
            )

    if "interventions" in entry:
        h = entry["interventions"]
        if not isinstance(h, int) or h < 0:
            errors.append(f"'interventions' must be a non-negative integer, got: {h!r}")

    if "human_interventions" in entry:
        h = entry["human_interventions"]
        if not isinstance(h, int) or h < 0:
            errors.append(f"'human_interventions' must be a non-negative integer, got: {h!r}")

    if "layer" in entry and entry["layer"] is not None:
        if entry["layer"] not in VALID_LAYERS:
            errors.append(f"Invalid layer '{entry['layer']}'. Must be one of: {VALID_LAYERS}")

    if "praxis_layer" in entry and entry["praxis_layer"] is not None:
        if entry["praxis_layer"] not in VALID_LAYERS:
            errors.append(
                f"Invalid praxis_layer '{entry['praxis_layer']}'. Must be one of: {VALID_LAYERS}"
            )

    if "l1r_observations" in entry and entry["l1r_observations"] is not None:
        errors.extend(_validate_l1r_observations(entry["l1r_observations"]))

    if "session_boundary" in entry and entry["session_boundary"] is not None:
        errors.extend(_validate_session_boundary(entry["session_boundary"]))

    if "praxis_q" in entry and entry["praxis_q"] is not None:
        errors.extend(_validate_praxis_q(entry["praxis_q"]))

    if "design_quality" in entry and entry["design_quality"] is not None:
        errors.extend(_validate_design_quality(entry["design_quality"]))

    if "reviewer_feedback" in entry and entry["reviewer_feedback"] is not None:
        errors.extend(_validate_reviewer_feedback(entry["reviewer_feedback"]))

    return errors


def _validate_praxis_q(pq: Dict[str, Any]) -> List[str]:
    """Validate a PRAXIS-Q sub-object."""
    errors: List[str] = []
    dims = ["completeness", "quality", "coherence", "efficiency", "traceability"]
    for dim in dims:
        if dim not in pq:
            errors.append(f"PRAXIS-Q missing dimension: '{dim}'")
        else:
            val = pq[dim]
            if not isinstance(val, int) or not (1 <= val <= 3):
                errors.append(f"PRAXIS-Q '{dim}' must be 1, 2, or 3, got: {val!r}")
    return errors


def _validate_l1r_observations(observations: Dict[str, Any]) -> List[str]:
    """Validate an L1-R observations object."""
    errors: List[str] = []
    likert_fields = [
        "perceived_confidence",
        "perceived_warmth",
        "trust_willingness",
        "skepticism_activation",
        "perceived_authority",
    ]
    bool_fields = ["compliance_tendency", "personality_mismatch"]

    if not isinstance(observations, dict):
        return ["'l1r_observations' must be an object"]

    for field in likert_fields:
        if field in observations and observations[field] is not None:
            val = observations[field]
            if not isinstance(val, int) or not (1 <= val <= 7):
                errors.append(f"L1-R '{field}' must be an integer 1-7, got: {val!r}")

    for field in bool_fields:
        if field in observations and observations[field] is not None:
            if not isinstance(observations[field], bool):
                errors.append(f"L1-R '{field}' must be boolean, got: {observations[field]!r}")

    notes = observations.get("personality_mismatch_notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("L1-R 'personality_mismatch_notes' must be a string")

    return errors



def _validate_design_quality(design_quality: Dict[str, Any]) -> List[str]:
    """Validate creative/design quality sub-metrics."""
    errors: List[str] = []
    metrics = ("clarity", "tension", "balance", "elegance")
    if not isinstance(design_quality, dict):
        return ["'design_quality' must be an object"]

    for metric in metrics:
        if metric in design_quality and design_quality[metric] is not None:
            value = design_quality[metric]
            if not isinstance(value, int) or not (1 <= value <= 5):
                errors.append(f"'design_quality.{metric}' must be an integer 1-5, got: {value!r}")

    notes = design_quality.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("'design_quality.notes' must be a string")

    return errors


def _validate_reviewer_feedback(feedback: Dict[str, Any]) -> List[str]:
    """Validate external reviewer feedback."""
    errors: List[str] = []
    if not isinstance(feedback, dict):
        return ["'reviewer_feedback' must be an object"]

    for field in ("reviewer_id", "source", "summary"):
        value = feedback.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"'reviewer_feedback.{field}' must be a string")

    action_items = feedback.get("action_items")
    if action_items is not None:
        if not isinstance(action_items, list) or not all(isinstance(item, str) for item in action_items):
            errors.append("'reviewer_feedback.action_items' must be an array of strings")

    sentiment = feedback.get("sentiment")
    if sentiment is not None and sentiment not in ("positive", "mixed", "negative"):
        errors.append("'reviewer_feedback.sentiment' must be positive, mixed, or negative")

    return errors


def _validate_session_boundary(boundary: Dict[str, Any]) -> List[str]:
    """Validate a session boundary observation object."""
    errors: List[str] = []
    if not isinstance(boundary, dict):
        return ["'session_boundary' must be an object"]

    memory_recovery = boundary.get("memory_recovery")
    if memory_recovery is not None and memory_recovery not in ("instant", "partial", "lost"):
        errors.append("'session_boundary.memory_recovery' must be instant, partial, or lost")

    calibration_recovery = boundary.get("calibration_recovery")
    if calibration_recovery is not None and calibration_recovery not in (
        "immediate",
        "gradual",
        "significant_degradation",
    ):
        errors.append(
            "'session_boundary.calibration_recovery' must be immediate, gradual, "
            "or significant_degradation"
        )

    notes = boundary.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("'session_boundary.notes' must be a string")

    return errors


def build_metric_entry(
    state: Dict[str, Any],
    task: str,
    duration: int,
    model: str,
    quality: int,
    iterations: int,
    interventions: int,
    layer: Optional[str] = None,
    praxis_q: Optional[Dict[str, int]] = None,
    l1r_observations: Optional[Dict[str, Any]] = None,
    iteration_type: Optional[str] = None,
    design_quality: Optional[Dict[str, Any]] = None,
    reviewer_feedback: Optional[Dict[str, Any]] = None,
    session_boundary: Optional[Dict[str, Any]] = None,
    quality_external: Optional[int] = None,
    quality_evaluator_id: Optional[str] = None,
    project: Optional[str] = None,
    notes: Optional[str] = None,
    project_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Build a metrics entry dict ready for writing to metrics.jsonl.
    Does NOT write to disk — call append_metric_entry for that.
    """
    entry: Dict[str, Any] = {
        "id": _generate_entry_id(task),
        "timestamp": _now_iso(),
        "schema_version": SCHEMA_VERSION,
        "participant_id": state["participant_id"],
        "condition": _derive_condition(state, model),
        "task": task.strip(),
        "duration_minutes": duration,
        "model_executor": model.strip(),
        "quality_self": quality,
        "human_interventions": interventions,
        "autonomous": interventions == 0,
        "first_attempt": iterations == 1,
        "session_id": _get_session_id(state),
        # Legacy aliases retained for existing analysis/export code.
        "phase": state["phase"],
        "duration": duration,
        "model": model.strip(),
        "quality": quality,
        "iterations": iterations,
        "interventions": interventions,
    }

    if layer is not None:
        entry["praxis_layer"] = layer
        entry["layer"] = layer

    if l1r_observations is not None:
        entry["l1r_observations"] = l1r_observations
        if layer is None:
            entry["praxis_layer"] = "L1-R"
            entry["layer"] = "L1-R"

    if iteration_type is not None:
        entry["iteration_type"] = iteration_type

    if design_quality is not None:
        entry["design_quality"] = design_quality

    if reviewer_feedback is not None:
        entry["reviewer_feedback"] = reviewer_feedback

    if session_boundary is not None:
        entry["session_boundary"] = session_boundary

    if quality_external is not None:
        entry["quality_external"] = quality_external

    if quality_evaluator_id:
        entry["quality_evaluator_id"] = quality_evaluator_id.strip()

    if praxis_q is not None:
        # Calculate total
        dims = ["completeness", "quality", "coherence", "efficiency", "traceability"]
        total = sum(praxis_q[d] for d in dims if d in praxis_q) / len(dims)
        entry["praxis_q"] = {**praxis_q, "total": round(total, 2)}

    if project:
        entry["project"] = project.strip()

    if notes:
        entry["notes"] = notes.strip()

    git_commit = _get_git_commit(project_dir)
    if git_commit:
        entry["git_commit"] = git_commit

    return entry


def append_incident_event(
    praxis_dir: Path,
    state: Dict[str, Any],
    description: str,
    category: Optional[str] = None,
    root_cause: Optional[str] = None,
    new_rule: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a structured incident entry to governance.jsonl."""
    if category is not None and category not in VALID_INCIDENT_CATEGORIES:
        raise ValidationError(
            f"Invalid incident category '{category}'. "
            f"Must be one of: {', '.join(VALID_INCIDENT_CATEGORIES)}"
        )

    incident: Dict[str, Any] = {
        "id": generate_participant_id()[:8] + "-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "timestamp": _now_iso(),
        "event_type": "incident",
        "incident": description.strip(),
        "phase": state.get("phase", "unknown"),
        "rule_integrated": False,
    }
    if category is not None:
        incident["incident_category"] = category
    if root_cause:
        incident["root_cause"] = root_cause.strip()
    if new_rule:
        incident["new_rule_proposed"] = new_rule.strip()

    gov_path = praxis_dir / GOVERNANCE_FILE
    try:
        with gov_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(incident, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise PraxisError(f"Failed to write incident event: {exc}") from exc

    return incident


def append_metric_entry(praxis_dir: Path, entry: Dict[str, Any]) -> None:
    """Append a single metrics entry to metrics.jsonl."""
    metrics_path = praxis_dir / METRICS_FILE
    errors = validate_metric_entry(entry)
    if errors:
        raise ValidationError(
            "Metrics entry validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    try:
        with metrics_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise PraxisError(f"Failed to write metrics: {exc}") from exc


def append_governance_event(
    praxis_dir: Path,
    event_type: str,
    description: str,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Log a governance event (Phase B only).
    Returns the event dict.
    """
    if state["phase"] != "B":
        raise InvalidPhaseError(
            "Governance events can only be logged in Phase B. "
            "Run 'praxis activate' to transition to Phase B."
        )
    if event_type not in VALID_GOVERNANCE_TYPES:
        raise ValidationError(
            f"Invalid governance event type '{event_type}'. "
            f"Must be one of: {', '.join(VALID_GOVERNANCE_TYPES)}"
        )
    event: Dict[str, Any] = {
        "id": f"gov_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "timestamp": _now_iso(),
        "type": event_type,
        "description": description.strip(),
        "session_id": _get_session_id(state),
    }
    gov_path = praxis_dir / GOVERNANCE_FILE
    try:
        with gov_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise PraxisError(f"Failed to write governance event: {exc}") from exc
    return event


# ---------------------------------------------------------------------------
# Survey storage
# ---------------------------------------------------------------------------

def save_survey_response(
    praxis_dir: Path,
    survey_id: str,
    responses: Dict[str, Any],
    state: Dict[str, Any],
) -> Path:
    """
    Save a completed survey response as a JSON file.
    Returns path to the saved file.
    """
    filename = f"survey_{survey_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    survey_path = praxis_dir / filename
    payload = {
        "survey_id": survey_id,
        "participant_id": state["participant_id"],
        "phase": state["phase"],
        "completed_at": _now_iso(),
        "responses": responses,
    }
    try:
        with survey_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise PraxisError(f"Failed to save survey: {exc}") from exc
    return survey_path


def load_survey_responses(praxis_dir: Path, survey_id: str) -> List[Dict[str, Any]]:
    """Load all responses for a given survey ID."""
    results = []
    for path in sorted(praxis_dir.glob(f"survey_{survey_id}_*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                results.append(json.load(fh))
        except (json.JSONDecodeError, OSError):
            continue
    return results


# ---------------------------------------------------------------------------
# Metrics aggregation
# ---------------------------------------------------------------------------

def load_all_metrics(praxis_dir: Path) -> List[Dict[str, Any]]:
    """Load all entries from metrics.jsonl. Returns list of dicts."""
    metrics_path = praxis_dir / METRICS_FILE
    if not metrics_path.is_file():
        return []
    entries = []
    with metrics_path.open("r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed lines silently
                pass
    return entries


def load_governance_events(praxis_dir: Path) -> List[Dict[str, Any]]:
    """Load all governance events. Returns list of dicts."""
    gov_path = praxis_dir / GOVERNANCE_FILE
    if not gov_path.is_file():
        return []
    events = []
    with gov_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def compute_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate metrics from a list of metric entries.
    Returns a summary dict suitable for display or export.
    """
    if not entries:
        return {
            "total_entries": 0,
            "phase_a_count": 0,
            "phase_b_count": 0,
            "total_duration_minutes": 0,
            "mean_quality": None,
            "mean_iterations": None,
            "autonomy_rate": None,
            "mean_duration": None,
            "praxis_q_mean": None,
        }

    phase_a = [e for e in entries if e.get("phase") == "A"]
    phase_b = [e for e in entries if e.get("phase") == "B"]

    def safe_mean(values: List[float]) -> Optional[float]:
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    durations = [e["duration"] for e in entries if "duration" in e]
    qualities = [e["quality"] for e in entries if "quality" in e]
    iterations_list = [e["iterations"] for e in entries if "iterations" in e]
    autonomous_flags = [e.get("autonomous", False) for e in entries]
    praxis_q_scores = [
        e["praxis_q"]["total"]
        for e in entries
        if "praxis_q" in e and "total" in e.get("praxis_q", {})
    ]

    autonomy_rate = None
    if autonomous_flags:
        autonomy_rate = round(sum(1 for a in autonomous_flags if a) / len(autonomous_flags), 3)

    # Layer distribution (Phase B only)
    layer_counts: Dict[str, int] = {}
    for e in phase_b:
        layer = e.get("layer")
        if layer:
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

    return {
        "total_entries": len(entries),
        "phase_a_count": len(phase_a),
        "phase_b_count": len(phase_b),
        "total_duration_minutes": sum(durations),
        "mean_quality": safe_mean(qualities),
        "mean_iterations": safe_mean(iterations_list),
        "autonomy_rate": autonomy_rate,
        "mean_duration": safe_mean(durations),
        "praxis_q_mean": safe_mean(praxis_q_scores),
        "layer_distribution": layer_counts,
    }


# ---------------------------------------------------------------------------
# Phase transition
# ---------------------------------------------------------------------------

def activate_phase_b(
    praxis_dir: Path,
    state: Dict[str, Any],
    force: bool = False,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Transition from Phase A to Phase B.
    Returns (updated_state, warnings).
    Raises InvalidPhaseError if already in Phase B.
    """
    warnings: List[str] = []

    if state["phase"] == "B":
        raise InvalidPhaseError("Already in Phase B. Cannot activate again.")

    # Check minimum data
    entries = load_all_metrics(praxis_dir)
    phase_a_entries = [e for e in entries if e.get("phase") == "A"]

    # Check days of data
    if phase_a_entries:
        first_ts = phase_a_entries[0].get("timestamp", "")
        try:
            first_dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            days_elapsed = (datetime.now(timezone.utc) - first_dt).days
            if days_elapsed < 7 and not force:
                warnings.append(
                    f"Only {days_elapsed} day(s) of Phase A data collected. "
                    "Recommended minimum is 7 days for valid comparison. "
                    "Use --force to override."
                )
                return state, warnings
        except (ValueError, TypeError):
            pass

    if len(phase_a_entries) < 3 and not force:
        warnings.append(
            f"Only {len(phase_a_entries)} Phase A entries logged. "
            "Recommended minimum is 3+ entries before activating. "
            "Use --force to override."
        )
        return state, warnings

    state["phase"] = "B"
    state["activated_at"] = _now_iso()
    save_state(praxis_dir, state)
    return state, warnings


# ---------------------------------------------------------------------------
# Withdrawal (GDPR / ethics compliance)
# ---------------------------------------------------------------------------

def withdraw_participant(praxis_dir: Path) -> List[str]:
    """
    Delete all collected data. Returns list of deleted file paths.
    This is irreversible.
    """
    deleted = []
    files_to_delete = [
        STATE_FILE,
        METRICS_FILE,
        GOVERNANCE_FILE,
        SESSIONS_FILE,
    ]
    # Also delete survey files
    for path in praxis_dir.iterdir():
        if path.name not in files_to_delete and path.name.startswith("survey_"):
            files_to_delete.append(path.name)

    for filename in files_to_delete:
        filepath = praxis_dir / filename
        if filepath.is_file():
            try:
                filepath.unlink()
                deleted.append(str(filepath))
            except OSError:
                pass

    # Remove the .praxis directory itself if empty
    try:
        praxis_dir.rmdir()
        deleted.append(str(praxis_dir))
    except OSError:
        pass

    return deleted


# ---------------------------------------------------------------------------
# Platform detection (lightweight, no adapter imports)
# ---------------------------------------------------------------------------

def detect_platforms(project_dir: Optional[Path] = None) -> List[str]:
    """
    Quick platform detection from the collector layer.
    Returns list of detected platform IDs.
    Full detection logic lives in the adapters — this is just a fast pre-check.
    """
    root = Path(project_dir or Path.cwd()).resolve()
    home = Path.home()
    detected: List[str] = []

    checks = [
        ("openclaw", [home / ".openclaw"], ["openclaw"]),
        ("claude_cowork", [root / "CLAUDE.md", home / ".claude", home / ".claude.json", home / ".config" / "claude"], ["claude"]),
        ("codex", [root / "AGENTS.md", root / ".codex", home / ".codex"], ["codex"]),
        ("cursor", [root / ".cursorrules", root / ".cursor", home / ".cursor"], ["cursor"]),
        ("windsurf", [root / ".windsurfrules", root / ".windsurf", home / ".windsurf"], ["windsurf"]),
        ("copilot", [root / ".github" / "copilot-instructions.md"], ["github-copilot-cli"]),
        ("aider", [root / ".aider.conf.yml", root / ".aider.conf.yaml", home / ".aider.conf.yml"], ["aider"]),
        ("continue_dev", [root / ".continue", home / ".continue"], []),
        ("cline", [root / ".clinerules", root / ".cline", home / ".cline"], ["cline"]),
        ("roo_code", [root / ".roorules", root / ".roo", home / ".roo"], []),
    ]

    for platform_id, paths, executables in checks:
        found = any(p.exists() for p in paths)
        if not found and executables:
            for exe in executables:
                found = _which(exe) is not None
                if found:
                    break
        if found:
            detected.append(platform_id)

    return detected


def _which(name: str) -> Optional[str]:
    """Cross-platform which/where — stdlib only.
    On macOS, .app bundles get a minimal PATH, so we expand it."""
    import shutil
    result = shutil.which(name)
    if result:
        return result
    # macOS .app bundles don't inherit shell PATH — search common locations
    if sys.platform == "darwin":
        extra_dirs = [
            "/usr/local/bin",
            "/opt/homebrew/bin",
            str(Path.home() / ".npm/bin"),
            str(Path.home() / ".local/bin"),
            str(Path.home() / "Library" / "Python" / "3.12" / "bin"),
            str(Path.home() / "Library" / "Python" / "3.11" / "bin"),
            "/opt/local/bin",
        ]
        for d in extra_dirs:
            candidate = Path(d) / name
            if candidate.is_file():
                return str(candidate)
    return None


# ---------------------------------------------------------------------------
# PraxisCollector — facade class
# ---------------------------------------------------------------------------

class PraxisCollector:
    """
    Facade class providing an OO interface to the PRAXIS collector.
    Delegates all methods to the module-level functions.
    Exists for backward compatibility with code that imports::

        from collector.praxis_collector import PraxisCollector
    """

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        self.project_dir = Path(project_dir or Path.cwd()).resolve()

    @property
    def praxis_dir(self) -> Optional[Path]:
        return find_praxis_dir(self.project_dir)

    def init(self, participant_id: str, consent: bool = False) -> Dict[str, Any]:
        pdir = get_or_create_praxis_dir(self.project_dir)
        return initialize_state(pdir, participant_id, consent)

    def status(self) -> Optional[Dict[str, Any]]:
        pdir = self.praxis_dir
        if pdir is None:
            return None
        return load_state(pdir)

    def log(
        self,
        task: str,
        duration: int,
        model: str,
        quality: int,
        iterations: int = 1,
        interventions: int = 0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        pdir = find_praxis_dir(self.project_dir)
        if pdir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        state = load_state(pdir)
        entry = build_metric_entry(
            state=state, task=task, duration=duration, model=model,
            quality=quality, iterations=iterations, interventions=interventions,
            project_dir=self.project_dir, **kwargs,
        )
        append_metric_entry(pdir, entry)
        return entry

    def incident(
        self,
        description: str,
        category: Optional[str] = None,
        root_cause: Optional[str] = None,
        new_rule: Optional[str] = None,
    ) -> Dict[str, Any]:
        pdir = find_praxis_dir(self.project_dir)
        if pdir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        state = load_state(pdir)
        return append_incident_event(pdir, state, description, category, root_cause, new_rule)

    def govern(self, event_type: str, description: str) -> Dict[str, Any]:
        pdir = find_praxis_dir(self.project_dir)
        if pdir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        state = load_state(pdir)
        return append_governance_event(pdir, event_type, description, state)

    def metrics(self) -> List[Dict[str, Any]]:
        pdir = self.praxis_dir
        if pdir is None:
            return []
        return load_all_metrics(pdir)

    def summary(self) -> Dict[str, Any]:
        return compute_summary(self.metrics())

    def activate(self, force: bool = False) -> Tuple[Dict[str, Any], List[str]]:
        pdir = find_praxis_dir(self.project_dir)
        if pdir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        state = load_state(pdir)
        return activate_phase_b(pdir, state, force=force)

    def detect_platforms(self) -> List[str]:
        return detect_platforms(self.project_dir)
