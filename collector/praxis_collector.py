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
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KIT_VERSION = "0.9.3-pre"
SCHEMA_VERSION = "0.2"
PRAXIS_DIR = ".praxis"
STATE_FILE = "state.json"
METRICS_FILE = "metrics.jsonl"
GOVERNANCE_FILE = "governance.jsonl"
SESSIONS_FILE = "sessions.jsonl"
DEFAULT_AUTO_QUALITY = 3

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
VALID_GOVERNANCE_TAGS = (
    "context_loss",
    "override",
    "ai_off_track",
    "scope_creep",
    "model_switch",
    "none",
)


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


def append_session_record(praxis_dir: Path, record: Dict[str, Any]) -> None:
    """Append a passive session capture record to sessions.jsonl."""
    sessions_path = praxis_dir / SESSIONS_FILE
    try:
        with sessions_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise PraxisError(f"Failed to write session capture: {exc}") from exc


def load_session_records(praxis_dir: Path) -> List[Dict[str, Any]]:
    """Load passive session capture records from sessions.jsonl."""
    sessions_path = praxis_dir / SESSIONS_FILE
    if not sessions_path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with sessions_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _write_session_records(praxis_dir: Path, rows: List[Dict[str, Any]]) -> None:
    sessions_path = praxis_dir / SESSIONS_FILE
    try:
        with sessions_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise PraxisError(f"Failed to update session capture: {exc}") from exc


def get_open_session_record(praxis_dir: Path) -> Optional[Dict[str, Any]]:
    """Return the most recent open passive session, if any."""
    rows = load_session_records(praxis_dir)
    for row in reversed(rows):
        if row.get("status") == "open":
            return row
    return None


def _git_probe(project_dir: Optional[Path]) -> Dict[str, Any]:
    """Collect lightweight git context for passive capture."""
    root = Path(project_dir or Path.cwd())
    commit = _get_git_commit(root)
    payload: Dict[str, Any] = {
        "repo": bool(commit),
        "commit": commit,
        "branch": None,
        "dirty_files": None,
    }
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=5,
        )
        if branch.returncode == 0:
            payload["branch"] = branch.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=5,
        )
        if dirty.returncode == 0:
            payload["dirty_files"] = len([line for line in dirty.stdout.splitlines() if line.strip()])
    except (OSError, subprocess.TimeoutExpired):
        pass
    return payload


def _git_commit_delta(project_dir: Optional[Path], start_commit: Optional[str], end_commit: Optional[str]) -> int:
    """Return number of commits between start and end when available."""
    if not start_commit or not end_commit or start_commit == end_commit:
        return 0
    root = Path(project_dir or Path.cwd())
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{start_commit}..{end_commit}"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=5,
        )
        if result.returncode == 0:
            return max(0, int((result.stdout or "0").strip() or "0"))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return 0


def start_passive_session(
    praxis_dir: Path,
    state: Dict[str, Any],
    project_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Open a passive capture session used as the default logging path."""
    existing = get_open_session_record(praxis_dir)
    if existing is not None:
        return existing

    session_id = f"capture_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    project_root = Path(project_dir or praxis_dir.parent)
    record = {
        "id": session_id,
        "type": "passive_session",
        "status": "open",
        "participant_id": state.get("participant_id"),
        "phase": state.get("phase", "A"),
        "condition": state.get("condition") or ("A1" if state.get("phase", "A") == "A" else "B1"),
        "started_at": _now_iso(),
        "ended_at": None,
        "project_root": str(project_root),
        "platform_ids": detect_platforms(project_root),
        "git_start": _git_probe(project_root),
        "capture_mode": "passive_auto",
    }
    try:
        from adapters.plugin_loader import probe_all_adapters
        record["adapter_telemetry_start"] = probe_all_adapters(praxis_dir.parent)
    except Exception:
        pass
    append_session_record(praxis_dir, record)
    return record


def finish_passive_session(
    praxis_dir: Path,
    state: Dict[str, Any],
    project_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Close the most recent passive session and return the finalized record."""
    rows = load_session_records(praxis_dir)
    if not rows:
        return None

    target_index = None
    for idx in range(len(rows) - 1, -1, -1):
        if rows[idx].get("status") == "open":
            target_index = idx
            break
    if target_index is None:
        return None

    project_root = Path(project_dir or praxis_dir.parent)
    row = dict(rows[target_index])
    row["status"] = "closed"
    row["ended_at"] = _now_iso()
    row["phase"] = state.get("phase", row.get("phase", "A"))
    row["condition"] = state.get("condition") or row.get("condition") or ("A1" if state.get("phase", "A") == "A" else "B1")
    row["platform_ids"] = detect_platforms(project_root)
    row["git_end"] = _git_probe(project_root)
    try:
        from adapters.plugin_loader import probe_all_adapters
        row["adapter_telemetry_end"] = probe_all_adapters(project_root)
    except Exception:
        pass

    start_dt = datetime.fromisoformat(str(row.get("started_at", "")).replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(str(row.get("ended_at", "")).replace("Z", "+00:00"))
    row["duration_minutes"] = max(1, round((end_dt - start_dt).total_seconds() / 60.0))
    row["passive_signals"] = {
        "platform_count": len(row.get("platform_ids", [])),
        "git_repo_detected": bool((row.get("git_end") or {}).get("repo")),
        "dirty_files_end": (row.get("git_end") or {}).get("dirty_files"),
        "git_commit_delta": _git_commit_delta(
            project_root,
            (row.get("git_start") or {}).get("commit"),
            (row.get("git_end") or {}).get("commit"),
        ),
    }
    rows[target_index] = row
    _write_session_records(praxis_dir, rows)
    return row


def estimate_reliability(entry: Dict[str, Any]) -> float:
    """Estimate session-level reliability based on provenance richness."""
    score = 0.25
    capture_mode = entry.get("capture_mode")
    if capture_mode == "manual":
        score += 0.3
    elif capture_mode == "smart_checkout":
        score += 0.25
    elif capture_mode == "micro_checkout":
        score += 0.2
    elif capture_mode == "passive_auto":
        score += 0.05

    provenance = entry.get("field_provenance") or {}
    if provenance.get("duration") == "auto":
        score += 0.1
    if provenance.get("platforms") == "auto":
        score += 0.05
    if provenance.get("task") in ("manual_micro_checkout", "smart_checkout"):
        score += 0.1
    if provenance.get("quality") in ("manual_micro_checkout", "smart_checkout"):
        score += 0.1
    if provenance.get("interventions") in ("manual_micro_checkout", "smart_checkout"):
        score += 0.05
    if provenance.get("trust") in ("manual_micro_checkout", "smart_checkout"):
        score += 0.05
    if provenance.get("governance_tag") == "smart_checkout":
        score += 0.05
    if entry.get("reviewed"):
        score += 0.05
    return round(min(1.0, score), 2)


def get_session_checkout_context(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return display-ready passive session metadata for contextual checkout."""
    passive = dict(entry.get("passive_capture") or {})
    started_raw = passive.get("started_at")
    ended_raw = passive.get("ended_at")
    started = _format_clock(started_raw)
    ended = _format_clock(ended_raw)
    duration = int(entry.get("duration_minutes") or entry.get("duration") or 0)
    platforms = passive.get("platform_ids") or entry.get("platforms") or []
    platform_label = ", ".join(_humanize_platform(str(p)) for p in platforms) if platforms else "Unknown"
    signals = dict(passive.get("signals") or {})
    git_label = _build_git_summary(passive, signals)
    adapter_tel = entry.get("adapter_telemetry_start") or {}
    adapter_parts = []
    for adapter_name, adapter_data in adapter_tel.items():
        if adapter_data.get("detected"):
            adapter_parts.append(f"{adapter_name} ✓")
    return {
        "started": started,
        "ended": ended,
        "duration_minutes": duration,
        "platform_label": platform_label,
        "git_label": git_label,
        "adapter_summary": " | ".join(adapter_parts) if adapter_parts else "",
    }


def apply_smart_checkout(
    entry: Dict[str, Any],
    outcome: str,
    governance_tag: Optional[str] = None,
    task: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply the smart contextual checkout mapping to a passive session draft."""
    outcome_key = str(outcome or "").strip().lower()
    outcome_map = {
        "solved": {"quality": 5, "iterations": entry.get("iterations") or 1, "trust_clean": 6, "trust_tagged": 4},
        "partial": {"quality": 3, "iterations": entry.get("iterations") or 2, "trust_clean": 4, "trust_tagged": 3},
        "abandoned": {"quality": 1, "iterations": entry.get("iterations") or 3, "trust_clean": 2, "trust_tagged": 1},
    }
    if outcome_key not in outcome_map:
        raise ValidationError("Outcome must be one of: solved, partial, abandoned")

    tag = str(governance_tag or "none").strip().lower().replace("-", "_")
    if not tag:
        tag = "none"
    if tag not in VALID_GOVERNANCE_TAGS:
        raise ValidationError(f"Invalid governance tag: {tag}")

    mapping = outcome_map[outcome_key]
    has_governance = tag != "none"
    trust = mapping["trust_tagged"] if has_governance else mapping["trust_clean"]

    provenance = dict(entry.get("field_provenance") or {})
    provenance.update({
        "task": "smart_checkout",
        "quality": "smart_checkout",
        "interventions": "smart_checkout",
        "trust": "smart_checkout",
        "governance_tag": "smart_checkout",
    })

    l1r = dict(entry.get("l1r_observations") or {})
    l1r["trust_willingness"] = trust
    l1r["skepticism_activation"] = max(1, 8 - trust)

    # Complete L1-R: derive missing Likert dimensions from trust signal (Bug #2 fix)
    # These are informed estimates — higher trust correlates with higher perceived confidence/authority
    if "perceived_confidence" not in l1r or l1r.get("perceived_confidence") is None:
        l1r["perceived_confidence"] = min(7, trust + 1)
    if "perceived_authority" not in l1r or l1r.get("perceived_authority") is None:
        l1r["perceived_authority"] = min(7, trust + 1)
    if "perceived_warmth" not in l1r or l1r.get("perceived_warmth") is None:
        l1r["perceived_warmth"] = min(7, max(1, trust - 1))
    if "compliance_tendency" not in l1r or l1r.get("compliance_tendency") is None:
        l1r["compliance_tendency"] = trust >= 5
    if "personality_mismatch" not in l1r or l1r.get("personality_mismatch") is None:
        l1r["personality_mismatch"] = False

    summary = (task or "").strip() or "Reviewed auto-captured session"
    interventions = int(entry.get("interventions") or entry.get("human_interventions") or 0)
    if tag == "override":
        interventions = max(1, interventions)

    updated = dict(entry)
    updated.update({
        "task": summary,
        "quality_self": mapping["quality"],
        "quality": mapping["quality"],
        "iterations": int(mapping["iterations"]),
        "first_attempt": int(mapping["iterations"]) <= 1,
        "human_interventions": interventions,
        "interventions": interventions,
        "autonomous": interventions == 0,
        "reviewed": True,
        "capture_mode": "smart_checkout",
        "governance_tag": tag,
        "checkout_outcome": outcome_key,
        "l1r_observations": l1r,
        "field_provenance": provenance,
    })
    updated["reliability_score"] = estimate_reliability(updated)
    return updated


def _format_clock(raw_value: Optional[str]) -> str:
    if not raw_value:
        return "?"
    try:
        dt = datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return str(raw_value)[11:16] if len(str(raw_value)) >= 16 else str(raw_value)


def _humanize_platform(platform_id: str) -> str:
    label = platform_id.replace("_", " ").replace("-", " ").strip()
    mapping = {
        "claude": "Claude",
        "claude code": "Claude Code",
        "codex": "Codex",
        "openclaw": "OpenClaw",
        "cursor": "Cursor",
        "copilot": "Copilot",
        "windsurf": "Windsurf",
        "aider": "Aider",
    }
    return mapping.get(label.lower(), label.title() or platform_id)


def _build_git_summary(passive_capture: Dict[str, Any], signals: Dict[str, Any]) -> str:
    git_end = dict(passive_capture.get("git_end") or {})
    repo_detected = bool(git_end.get("repo") or signals.get("git_repo_detected"))
    if not repo_detected:
        return "No repo detected"
    commit_delta = int(signals.get("git_commit_delta") or 0)
    dirty_files = git_end.get("dirty_files")
    parts = [f"+{commit_delta} commits"]
    if dirty_files is not None:
        noun = "file" if int(dirty_files) == 1 else "files"
        parts.append(f"{int(dirty_files)} {noun} changed")
    branch = git_end.get("branch")
    if branch:
        parts.append(str(branch))
    return ", ".join(parts)


def build_auto_session_entry(
    state: Dict[str, Any],
    session_record: Dict[str, Any],
    project_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Turn a passive session capture into a draft sprint metric entry."""
    duration = int(session_record.get("duration_minutes") or 1)
    phase = state.get("phase", session_record.get("phase", "A"))
    platforms = session_record.get("platform_ids", [])
    entry: Dict[str, Any] = {
        "id": _generate_entry_id("passive_session"),
        "type": "sprint",
        "timestamp": session_record.get("started_at", _now_iso()),
        "schema_version": SCHEMA_VERSION,
        "participant_id": state.get("participant_id"),
        "condition": session_record.get("condition") or _derive_condition(state, "unknown"),
        "task": "(auto-captured session — add a short checkout summary)",
        "duration_minutes": duration,
        "duration": duration,
        "model_executor": "unknown",
        "model": "unknown",
        "quality_self": DEFAULT_AUTO_QUALITY,
        "quality": DEFAULT_AUTO_QUALITY,
        "human_interventions": 0,
        "interventions": 0,
        "autonomous": True,
        "first_attempt": True,
        "iterations": 1,
        "session_id": session_record.get("id") or _get_session_id(state),
        "phase": phase,
        "platforms": platforms,
        "reviewed": False,
        "capture_mode": "passive_auto",
        "source_session_id": session_record.get("id"),
        "field_provenance": {
            "task": "placeholder",
            "duration": "auto",
            "model": "unknown",
            "quality": "default",
            "interventions": "default",
            "platforms": "auto",
            "git": "auto",
        },
        "passive_capture": {
            "started_at": session_record.get("started_at"),
            "ended_at": session_record.get("ended_at"),
            "platform_ids": platforms,
            "git_start": session_record.get("git_start"),
            "git_end": session_record.get("git_end"),
            "signals": session_record.get("passive_signals", {}),
        },
        "notes": "Passive capture draft. Review with a quick checkout to improve reliability.",
    }
    # Extract model from adapter telemetry (Bug #1 fix)
    detected_model, detected_executor = _extract_model_from_telemetry(session_record)
    if detected_model and detected_model != "unknown":
        entry["model"] = detected_model
        entry["model_executor"] = detected_executor
        entry["field_provenance"]["model"] = "auto_telemetry"

    git_commit = _get_git_commit(project_dir)
    if git_commit:
        entry["git_commit"] = git_commit
    entry["reliability_score"] = estimate_reliability(entry)
    return entry


def _extract_model_from_telemetry(session_record: Dict[str, Any]) -> tuple:
    """Extract model name and executor from adapter telemetry.

    Returns (model_name, executor_name) where executor_name identifies
    the platform that provided the model info.
    """
    for tel_key in ("adapter_telemetry_start", "adapter_telemetry_end"):
        telemetry = session_record.get(tel_key)
        if not isinstance(telemetry, dict):
            continue

        # OpenClaw: model_info.model or model_info.default_model
        oc = telemetry.get("openclaw")
        if isinstance(oc, dict) and oc.get("detected"):
            model_info = oc.get("model_info")
            if isinstance(model_info, dict):
                for key in ("model", "default_model"):
                    m = model_info.get(key)
                    if isinstance(m, str) and m and _is_real_model_name(m):
                        return (m, "openclaw")

        # Codex: latest_session.model
        cx = telemetry.get("codex")
        if isinstance(cx, dict) and cx.get("detected"):
            latest = cx.get("latest_session")
            if isinstance(latest, dict):
                m = latest.get("model")
                if isinstance(m, str) and m and _is_real_model_name(m):
                    return (m, "codex")

        # Custom adapters: check for 'model' key at top level
        for adapter_name, adapter_data in telemetry.items():
            if adapter_name in ("openclaw", "codex"):
                continue
            if isinstance(adapter_data, dict) and adapter_data.get("detected"):
                m = adapter_data.get("model")
                if isinstance(m, str) and m and _is_real_model_name(m):
                    return (m, adapter_name)

    return ("unknown", "unknown")


# Generic provider names that are NOT real model identifiers
_PROVIDER_PLACEHOLDERS = frozenset({
    "openai", "anthropic", "google", "unknown", "azure", "aws", "meta",
    "mistral", "cohere", "xai", "deepseek", "local", "ollama",
})


def _is_real_model_name(name: str) -> bool:
    """Check if a model name is a concrete model ID, not a generic provider placeholder.

    Real model names contain specific identifiers like:
    - gpt-5.4, claude-sonnet-4, gemini-2.5-pro, zai/glm-5.1
    Generic placeholders like 'openai', 'anthropic' are rejected.
    """
    if not name or not name.strip():
        return False
    lowered = name.strip().lower()
    if lowered in _PROVIDER_PLACEHOLDERS:
        return False
    # Real model names typically contain /, -, or digits
    # Provider names are single words with no version info
    return True


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


def update_metric_entry(praxis_dir: Path, entry_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update one metric entry by id and return the updated row."""
    metrics_path = praxis_dir / METRICS_FILE
    if not metrics_path.is_file():
        return None
    rows: List[str] = []
    updated_row: Optional[Dict[str, Any]] = None
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            rows.append(raw)
            continue
        if row.get("id") == entry_id:
            row.update(updates)
            if "reliability_score" not in updates:
                row["reliability_score"] = estimate_reliability(row)
            updated_row = row
        rows.append(json.dumps(row, ensure_ascii=False))
    if updated_row is None:
        return None
    metrics_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return updated_row


def delete_metric_entry(praxis_dir: Path, entry_id: str) -> bool:
    """Delete one metric entry by id. Returns True if found and removed."""
    metrics_path = praxis_dir / METRICS_FILE
    if not metrics_path.is_file():
        return False
    rows: List[str] = []
    found = False
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            rows.append(raw)
            continue
        if row.get("id") == entry_id:
            found = True
            continue  # skip this row = delete it
        rows.append(json.dumps(row, ensure_ascii=False))
    if not found:
        return False
    metrics_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return True


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

    sprint_entries = [e for e in entries if e.get("type", "sprint") == "sprint"]
    phase_a = [e for e in sprint_entries if e.get("phase") == "A"]
    phase_b = [e for e in sprint_entries if e.get("phase") == "B"]

    def safe_mean(values: List[float]) -> Optional[float]:
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    durations = [e["duration"] for e in sprint_entries if "duration" in e]
    qualities = [e["quality"] for e in sprint_entries if "quality" in e]
    iterations_list = [e["iterations"] for e in sprint_entries if "iterations" in e]
    autonomous_flags = [e.get("autonomous", False) for e in sprint_entries]
    reliability_scores = [float(e.get("reliability_score")) for e in sprint_entries if isinstance(e.get("reliability_score"), (int, float))]
    praxis_q_scores = [
        e["praxis_q"]["total"]
        for e in sprint_entries
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
        "total_entries": len(sprint_entries),
        "raw_entries": len(entries),
        "phase_a_count": len(phase_a),
        "phase_b_count": len(phase_b),
        "total_duration_minutes": sum(durations),
        "mean_quality": safe_mean(qualities),
        "mean_iterations": safe_mean(iterations_list),
        "autonomy_rate": autonomy_rate,
        "mean_duration": safe_mean(durations),
        "praxis_q_mean": safe_mean(praxis_q_scores),
        "mean_reliability": safe_mean(reliability_scores),
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
        ("claude_cowork", [root / "CLAUDE.md", home / ".claude", home / ".claude.json", home / ".config" / "claude"], ["claude"], [home / "Applications" / "Claude.app", Path("/Applications/Claude.app")]),
        ("codex", [root / "AGENTS.md", root / ".codex", home / ".codex"], ["codex"]),
        ("cursor", [root / ".cursorrules", root / ".cursor", home / ".cursor"], ["cursor"]),
        ("windsurf", [root / ".windsurfrules", root / ".windsurf", home / ".windsurf"], ["windsurf"]),
        ("copilot", [root / ".github" / "copilot-instructions.md"], ["github-copilot-cli"]),
        ("aider", [root / ".aider.conf.yml", root / ".aider.conf.yaml", home / ".aider.conf.yml"], ["aider"]),
        ("continue_dev", [root / ".continue", home / ".continue"], []),
        ("cline", [root / ".clinerules", root / ".cline", home / ".cline"], ["cline"]),
        ("roo_code", [root / ".roorules", root / ".roo", home / ".roo"], []),
    ]

    for entry in checks:
        platform_id = entry[0]
        paths = entry[1]
        executables = entry[2]
        app_paths = entry[3] if len(entry) > 3 else []
        found = any(p.exists() for p in paths)
        if not found and executables:
            for exe in executables:
                found = _which(exe) is not None
                if found:
                    break
        if not found and app_paths:
            # Check for app bundles (macOS .app, etc.)
            found = any(p.exists() for p in app_paths)
        if found:
            detected.append(platform_id)

    return detected


def _which(name: str) -> Optional[str]:
    """Cross-platform which/where — stdlib only.
    On macOS, .app bundles get a minimal PATH, so we expand it."""
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
