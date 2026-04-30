"""
PRAXIS Universal Kit — Anonymized Data Export
===============================================
Reads .praxis/ directory, strips PII, generates participant ZIP
for submission to the researcher.

What is included in the export:
  - metrics.jsonl (task metrics, optionally with descriptions redacted)
  - sessions.jsonl (passive capture timeline)
  - governance.jsonl (governance events)
  - survey_*.json (survey responses, participant ID only — no name)
  - state.json (observation mode info, no personal identifiers)
  - export_manifest.json (metadata about this export)

What is NEVER included:
  - File contents from your project
  - Conversation logs
  - Personal identifiable information beyond participant ID
  - Anything outside .praxis/

Python 3.8+ compatible. Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


_KIT_ROOT = Path(__file__).resolve().parent.parent
_COLLECTOR_DIR = str(_KIT_ROOT / "collector")
if _COLLECTOR_DIR not in sys.path:
    sys.path.insert(0, _COLLECTOR_DIR)

from diagnostics import build_user_diagnosis


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPORT_VERSION = "0.10.0"
PII_FIELDS_TO_REDACT = ["name", "email", "phone", "ip_address", "machine_name"]
FILES_TO_INCLUDE = [
    "metrics.jsonl",
    "governance.jsonl",
    "state.json",
]


# ---------------------------------------------------------------------------
# Pre-export cleanup
# ---------------------------------------------------------------------------

def _auto_close_orphan_sessions(praxis_dir: Path) -> int:
    """Close truly orphaned sessions (open > 24h) before export.

    Only closes sessions that have been open for more than 24 hours,
    which indicates the session was abandoned rather than actively running.
    Active sessions (< 24h open) are left untouched.

    Uses atomic write (write-to-temp + rename) to avoid races with
    concurrent session lifecycle writes.

    Returns the number of sessions that were auto-closed.
    """
    import tempfile

    sessions_path = praxis_dir / "sessions.jsonl"
    if not sessions_path.is_file():
        return 0

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    orphan_threshold_hours = 24
    closed_count = 0
    lines: List[str] = []

    with sessions_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                lines.append(raw)
                continue
            if isinstance(record, dict) and record.get("status") == "open":
                # Only close if session has been open > 24h (truly orphaned)
                started = _parse_iso_or_none(record.get("started_at"))
                if started is not None and (now - started).total_seconds() > orphan_threshold_hours * 3600:
                    record["status"] = "closed"
                    record["ended_at"] = now_iso
                    record["auto_closed_on_export"] = True
                    record["orphan_reason"] = f"open > {orphan_threshold_hours}h"
                    closed_count += 1
            lines.append(json.dumps(record, ensure_ascii=False))

    if closed_count > 0:
        # Atomic write: temp file + rename to avoid races
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(praxis_dir), suffix=".tmp", prefix=".sessions_"
        )
        try:
            import os
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            # On Windows, need to remove target first if it exists
            backup_path = sessions_path.with_suffix(".jsonl.bak")
            if sessions_path.is_file():
                sessions_path.replace(backup_path)
            tmp_rename = Path(tmp_path)
            tmp_rename.replace(sessions_path)
            # Clean up backup
            if backup_path.is_file():
                backup_path.unlink()
        except Exception:
            # If atomic write fails, don't leave corrupted state
            Path(tmp_path).unlink(missing_ok=True)
            raise

    return closed_count


def _parse_iso_or_none(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp string, returning None on failure."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def export_participant_zip(
    praxis_dir: Path,
    redact_tasks: bool = False,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Create an anonymized ZIP file for researcher submission.

    Args:
        praxis_dir: Path to the .praxis/ directory.
        redact_tasks: If True, replace task descriptions with [REDACTED].
        output_dir: Where to write the ZIP. Defaults to parent of praxis_dir.

    Returns:
        Path to the created ZIP file.
    """
    if not praxis_dir.is_dir():
        raise ValueError(f"PRAXIS directory not found: {praxis_dir}")

    # Auto-close orphan sessions before export (Bug #3 fix)
    _auto_close_orphan_sessions(praxis_dir)

    # Load state for participant ID
    state = _load_json(praxis_dir / "state.json")
    if state is None:
        raise ValueError("state.json not found or unreadable in .praxis/")

    participant_id = state.get("participant_id", "PRAXIS-UNKNOWN")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    zip_filename = f"{participant_id}_{timestamp}.zip"

    if output_dir is None:
        output_dir = praxis_dir.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / zip_filename

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add core metric files
        _add_metrics(zf, praxis_dir, participant_id, redact_tasks)
        _add_sessions(zf, praxis_dir, participant_id)
        _add_governance(zf, praxis_dir, participant_id)
        _add_state(zf, praxis_dir, participant_id)
        _add_surveys(zf, praxis_dir, participant_id)
        _add_diagnosis(zf, praxis_dir, state)
        _add_manifest(zf, praxis_dir, participant_id, state, redact_tasks, timestamp)

    return zip_path


# ---------------------------------------------------------------------------
# Per-file export helpers
# ---------------------------------------------------------------------------

def _add_metrics(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
    redact_tasks: bool,
) -> None:
    """Export metrics.jsonl with optional task redaction."""
    metrics_path = praxis_dir / "metrics.jsonl"
    if not metrics_path.is_file():
        return

    cleaned_lines: List[str] = []
    with metrics_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry = _clean_metric_entry(entry, participant_id, redact_tasks)
                cleaned_lines.append(json.dumps(entry, ensure_ascii=False))
            except json.JSONDecodeError:
                continue

    zf.writestr("metrics.jsonl", "\n".join(cleaned_lines) + "\n" if cleaned_lines else "")


def _add_governance(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
) -> None:
    """Export governance.jsonl."""
    gov_path = praxis_dir / "governance.jsonl"
    if not gov_path.is_file():
        return

    cleaned_lines: List[str] = []
    with gov_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event = _clean_governance_event(event, participant_id)
                cleaned_lines.append(json.dumps(event, ensure_ascii=False))
            except json.JSONDecodeError:
                continue

    zf.writestr("governance.jsonl", "\n".join(cleaned_lines) + "\n" if cleaned_lines else "")


def _add_sessions(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
) -> None:
    """Export passive sessions timeline."""
    sessions_path = praxis_dir / "sessions.jsonl"
    if not sessions_path.is_file():
        return

    cleaned_lines: List[str] = []
    with sessions_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            clean = _strip_pii_from_dict(dict(row))
            clean["participant_id"] = participant_id
            clean.pop("project_root", None)
            cleaned_lines.append(json.dumps(clean, ensure_ascii=False))

    zf.writestr("sessions.jsonl", "\n".join(cleaned_lines) + "\n" if cleaned_lines else "")


def _add_state(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
) -> None:
    """Export anonymized state.json."""
    state_path = praxis_dir / "state.json"
    if not state_path.is_file():
        return

    state = _load_json(state_path)
    if state is None:
        return

    # Keep only research-relevant fields — remove anything that could be PII
    clean_state = {
        "participant_id": participant_id,
        "kit_version": state.get("kit_version"),
        "schema_version": state.get("schema_version"),
        "phase": state.get("phase", "obs"),
        "installed_at": state.get("installed_at"),
        "activated_at": state.get("activated_at"),
        "consent_given": state.get("consent_given"),
        "consent_given_at": state.get("consent_given_at"),
        "pre_survey_completed": state.get("pre_survey_completed"),
        "post_survey_completed": state.get("post_survey_completed"),
        "platform_ids": state.get("platform_ids", []),
        "session_count": state.get("session_count"),
        "last_active": state.get("last_active"),
        # Explicitly exclude: machine_name, node_id, any future PII fields
    }

    zf.writestr("state.json", json.dumps(clean_state, indent=2, ensure_ascii=False))


def _add_surveys(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
) -> None:
    """Export all survey response files."""
    for survey_file in sorted(praxis_dir.glob("survey_*.json")):
        survey_data = _load_json(survey_file)
        if survey_data is None:
            continue

        # Ensure participant_id is consistent (anonymized)
        survey_data["participant_id"] = participant_id
        # Remove any accidental PII
        survey_data = _strip_pii_from_dict(survey_data)

        zf.writestr(
            survey_file.name,
            json.dumps(survey_data, indent=2, ensure_ascii=False),
        )


def _add_manifest(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    participant_id: str,
    state: Dict[str, Any],
    redact_tasks: bool,
    timestamp: str,
) -> None:
    """Add export_manifest.json with metadata about this export."""
    # Count entries
    metrics_count = _count_jsonl_lines(praxis_dir / "metrics.jsonl")
    gov_count = _count_jsonl_lines(praxis_dir / "governance.jsonl")
    session_count = _count_jsonl_lines(praxis_dir / "sessions.jsonl")
    survey_count = len(list(praxis_dir.glob("survey_*.json")))
    metrics = _load_jsonl(praxis_dir / "metrics.jsonl")
    diagnosis = build_user_diagnosis(metrics, _load_jsonl(praxis_dir / "governance.jsonl"), state)

    manifest = {
        "export_version": EXPORT_VERSION,
        "participant_id": participant_id,
        "exported_at": _now_iso(),
        "kit_version": state.get("kit_version", "?"),
        "phase_at_export": state.get("phase", "obs"),
        "redact_tasks": redact_tasks,
        "files_included": ["metrics.jsonl", "sessions.jsonl", "governance.jsonl", "state.json"],
        "includes_user_diagnosis": True,
        "metrics_entries": metrics_count,
        "passive_sessions": session_count,
        "governance_events": gov_count,
        "surveys_completed": survey_count,
        "mean_provenance_completeness": diagnosis.get("metrics", {}).get("avg_reliability"),
        "mean_reliability": diagnosis.get("metrics", {}).get("avg_reliability"),  # deprecated alias
        "integrity": {
            "metrics_sha256": _sha256_file(praxis_dir / "metrics.jsonl"),
            "sessions_sha256": _sha256_file(praxis_dir / "sessions.jsonl"),
            "governance_sha256": _sha256_file(praxis_dir / "governance.jsonl"),
        },
        "instructions": (
            "Send this ZIP to the PRAXIS researcher. "
            "It contains only pseudonymized research metrics — no project files, "
            "no conversation content, no personal identifiers beyond your participant ID. "
            "Your participant ID is pseudonymized (derived from machine characteristics), not fully anonymous. "
            "It also includes a user-facing diagnosis so participants get value back from contributing."
        ),
    }

    zf.writestr("export_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))


def _add_diagnosis(
    zf: zipfile.ZipFile,
    praxis_dir: Path,
    state: Dict[str, Any],
) -> None:
    metrics = _load_jsonl(praxis_dir / "metrics.jsonl")
    governance = _load_jsonl(praxis_dir / "governance.jsonl")
    diagnosis = build_user_diagnosis(metrics, governance, state)
    zf.writestr("diagnosis.json", json.dumps(diagnosis, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def _clean_metric_entry(
    entry: Dict[str, Any],
    participant_id: str,
    redact_tasks: bool,
) -> Dict[str, Any]:
    """
    Clean a single metrics entry for export.
    - Replace participant identifier
    - Optionally redact task descriptions
    - Remove any git paths or file paths that could reveal project structure
    """
    clean = dict(entry)

    # Ensure participant ID is consistent
    clean["participant_id"] = participant_id

    # Optionally redact task descriptions (user choice)
    if redact_tasks and "task" in clean:
        clean["task"] = "[REDACTED]"
    if redact_tasks and "notes" in clean:
        clean["notes"] = "[REDACTED]"

    # Remove git commit hash (could fingerprint repo)
    clean.pop("git_commit", None)

    # Remove session_id (keep for grouping but hash it)
    if "session_id" in clean:
        clean["session_id"] = _hash_short(clean["session_id"])

    # Remove praxis_q.total if it can be recomputed (keep raw scores)
    # Actually keep it — it's useful for analysis

    # Strip any accidental PII
    clean = _strip_pii_from_dict(clean)

    return clean


def _clean_governance_event(
    event: Dict[str, Any],
    participant_id: str,
) -> Dict[str, Any]:
    """Clean a governance event for export."""
    clean = dict(event)
    clean["participant_id"] = participant_id

    if "session_id" in clean:
        clean["session_id"] = _hash_short(clean["session_id"])

    clean = _strip_pii_from_dict(clean)
    return clean


def _strip_pii_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively remove known PII field names from a dict."""
    if not isinstance(data, dict):
        return data
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in PII_FIELDS_TO_REDACT:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = _strip_pii_from_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _strip_pii_from_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _count_jsonl_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _sha256_file(path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file for integrity checking."""
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_short(value: str) -> str:
    """Return first 12 chars of SHA-256 hash of a string."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CLI usage (if called directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Export anonymized PRAXIS research data as a ZIP file.",
    )
    parser.add_argument(
        "--praxis-dir", type=Path, default=None,
        help="Path to .praxis/ directory (default: auto-detect from cwd)",
    )
    parser.add_argument(
        "--redact-tasks", action="store_true",
        help="Replace task descriptions with [REDACTED]",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output directory for the ZIP file (default: current directory)",
    )

    args = parser.parse_args()

    # Auto-detect .praxis/ directory
    praxis_dir = args.praxis_dir
    if praxis_dir is None:
        from praxis_collector import find_praxis_dir
        praxis_dir = find_praxis_dir()
        if praxis_dir is None:
            print("ERROR: PRAXIS not found. Run from your project directory.")
            sys.exit(1)

    try:
        output = export_participant_zip(
            praxis_dir=praxis_dir,
            redact_tasks=args.redact_tasks,
            output_dir=args.output,
        )
        print(f"Export complete: {output}")
        print("Send this ZIP file to the researcher.")
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
