"""PRAXIS Desktop — View Model / Controller Layer

Bridges CustomTkinter views to praxis_collector functions.
No subprocess, no CLI parsing — direct Python imports.

Sprint 2 additions: background session timer, auto-save on close,
# Session management, auto-save, recovery.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Import resolver — works both as source and as PyInstaller bundle
# ---------------------------------------------------------------------------

def _resolve_kit_root() -> Path:
    """Find the PRAXIS Universal Kit root directory."""
    # 1. If running as source from repo root or desktop/
    #    __file__ = .../desktop/viewmodel.py  →  parent = .../desktop/  →  parent = kit root
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "collector" / "praxis_collector.py").is_file():
        return candidate

    # 2. If bundled by PyInstaller, _MEIPASS is set
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        me_root = Path(sys._MEIPASS)
        if (me_root / "collector" / "praxis_collector.py").is_file():
            return me_root

    # 3. Walk up from cwd
    cwd = Path.cwd().resolve()
    for d in [cwd] + list(cwd.parents):
        if (d / "collector" / "praxis_collector.py").is_file():
            return d

    raise FileNotFoundError(
        "Cannot locate PRAXIS kit root. Run from the repo directory or ensure collector/ is bundled."
    )


KIT_ROOT = _resolve_kit_root()

# Ensure collector/ and adapters/ are importable
_collector_dir = str(KIT_ROOT / "collector")
_adapters_dir = str(KIT_ROOT / "adapters")
for _p in (_collector_dir, _adapters_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Now import the real modules
import praxis_collector  # noqa: E402
from adapters.base import detect_project_type  # noqa: E402

# Re-export for convenience
from praxis_collector import (  # noqa: E402
    PraxisError,
    StateNotFoundError,
    ValidationError,
    append_metric_entry,
    build_auto_session_entry,
    build_metric_entry,
    compute_summary,
    detect_platforms,
    estimate_reliability,
    find_praxis_dir,
    finish_passive_session,
    generate_participant_id,
    get_or_create_praxis_dir,
    initialize_state,
    load_all_metrics,
    load_governance_events,
    load_session_records,
    load_state,
    touch_last_active,
    save_state,
    start_passive_session,
    update_metric_entry,
    delete_metric_entry,
)

# Export module
_export_dir = str(KIT_ROOT / "export")
if _export_dir not in sys.path:
    sys.path.insert(0, _export_dir)

from anonymize import export_participant_zip  # noqa: E402
from submission import get_submission_status, submit_export, submission_setup_template  # noqa: E402

# Protocol module removed — prescriptive injection is a post-thesis product
from diagnostics import build_user_diagnosis  # noqa: E402


class PraxisViewModel:
    """Controller layer — all UI↔data logic lives here."""

    def __init__(self) -> None:
        self._project_dir: Optional[Path] = None
        self._praxis_dir: Optional[Path] = None
        self._state: Optional[Dict[str, Any]] = None

        # Sprint 2: session timer state
        self._session_start: Optional[datetime] = None
        self._session_active: bool = False

        # Recording state
        self._praxis_mode_on: bool = False

    # ------------------------------------------------------------------
    # Project / state management
    # ------------------------------------------------------------------

    @property
    def project_dir(self) -> Optional[Path]:
        return self._project_dir

    @property
    def praxis_dir(self) -> Optional[Path]:
        return self._praxis_dir

    @property
    def state(self) -> Optional[Dict[str, Any]]:
        return self._state

    def is_initialized(self) -> bool:
        return self._state is not None

    def is_logging_active(self) -> bool:
        """Check if PRAXIS logging is currently active (not paused)."""
        if self._state is None:
            return False
        return self._state.get("logging_active", True)

    def start_logging(self) -> None:
        """Activate PRAXIS session logging."""
        if self._state is None or self._praxis_dir is None:
            return
        self._state["logging_active"] = True
        self._state["logging_started_at"] = praxis_collector._now_iso()
        save_state(self._praxis_dir, self._state)

    def stop_logging(self) -> None:
        """Pause PRAXIS session logging."""
        if self._state is None or self._praxis_dir is None:
            return
        self._state["logging_active"] = False
        save_state(self._praxis_dir, self._state)

    def set_project_dir(self, path: Path) -> None:
        """Set the project directory and try to load existing state."""
        self._project_dir = path.resolve()
        self._praxis_dir = find_praxis_dir(self._project_dir)
        if self._praxis_dir is not None:
            try:
                self._state = load_state(self._praxis_dir)
            except PraxisError:
                self._state = None
        else:
            self._state = None

    def initialize(
        self,
        project_dir: Path,
        consent_given: bool = True,
    ) -> Dict[str, Any]:
        """Initialize PRAXIS in the given project directory."""
        praxis_dir = get_or_create_praxis_dir(project_dir)
        participant_id = generate_participant_id()
        state = initialize_state(praxis_dir, participant_id, consent_given)
        self._project_dir = project_dir.resolve()
        self._praxis_dir = praxis_dir
        self._state = state
        return state

    def refresh_state(self) -> Optional[Dict[str, Any]]:
        """Reload state from disk."""
        if self._praxis_dir is None:
            return None
        try:
            self._state = load_state(self._praxis_dir)
        except PraxisError:
            self._state = None
        return self._state

    def touch_active(self) -> None:
        if self._praxis_dir is not None:
            touch_last_active(self._praxis_dir)

    # ------------------------------------------------------------------
    # Sprint 2: Session Timer & Auto-Save
    # ------------------------------------------------------------------

    def start_session(self) -> None:
        """Start a new background session timer."""
        self._session_start = datetime.now(timezone.utc)
        self._session_active = True
        if self._state is not None and self._praxis_dir is not None:
            try:
                start_passive_session(self._praxis_dir, self._state, self._project_dir)
            except PraxisError:
                pass

    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current session and return the auto-saved entry, or None."""
        if not self._session_active or self._session_start is None:
            return None
        entry = self._build_auto_session_entry()
        if entry and self._praxis_dir:
            append_metric_entry(self._praxis_dir, entry)
        self._session_active = False
        self._session_start = None
        return entry

    def discard_session(self) -> None:
        """Discard the current session without saving."""
        self._session_active = False
        self._session_start = None

    def get_session_elapsed_minutes(self) -> float:
        """Return elapsed minutes since session start, or 0 if no session."""
        if not self._session_active or self._session_start is None:
            return 0.0
        delta = datetime.now(timezone.utc) - self._session_start
        return max(0.0, delta.total_seconds() / 60.0)

    def is_session_active(self) -> bool:
        return self._session_active

    def get_session_start(self) -> Optional[datetime]:
        return self._session_start

    def set_session_start(self, start: datetime) -> None:
        """Resume a session from a given start time (for recovery)."""
        self._session_start = start
        self._session_active = True

    def _build_auto_session_entry(self) -> Optional[Dict[str, Any]]:
        """Build a passive-capture-backed auto session entry."""
        if self._session_start is None or self._praxis_dir is None or self._state is None:
            return None
        session = finish_passive_session(self._praxis_dir, self._state, self._project_dir)
        if session is None:
            duration = max(1, round((datetime.now(timezone.utc) - self._session_start).total_seconds() / 60.0))
            session = {
                "id": praxis_collector._generate_entry_id("capture"),
                "started_at": self._session_start.isoformat().replace("+00:00", "Z"),
                "ended_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "duration_minutes": duration,
                "platform_ids": detect_platforms(self._project_dir if self._project_dir else None),
                "condition": "obs",
            }
        return build_auto_session_entry(self._state, session, self._project_dir)

    def auto_save_session(self) -> Optional[Dict[str, Any]]:
        """Auto-save current session on close. Returns the entry or None."""
        return self.end_session()

    def recover_session(self, start_time: datetime) -> Optional[Dict[str, Any]]:
        """Recover an interrupted session and auto-save it."""
        self._session_start = start_time
        self._session_active = True
        entry = self._build_auto_session_entry()
        if entry and self._praxis_dir:
            append_metric_entry(self._praxis_dir, entry)
        self._session_active = False
        self._session_start = None
        return entry

    def is_praxis_mode_on(self) -> bool:
        return self._praxis_mode_on

    # ------------------------------------------------------------------
    # Sprint 2: Metrics helpers for Review/Edit view
    # ------------------------------------------------------------------

    def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent sprint entries, newest first."""
        if not self._praxis_dir:
            return []
        entries = load_all_metrics(self._praxis_dir)
        sprints = [e for e in entries if e.get("type") == "sprint"]
        sprints.reverse()  # newest first
        return sprints[:limit]

    def update_session_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a specific session entry in metrics.jsonl by id.
        Returns True if found and updated."""
        if not self._praxis_dir:
            return False
        updates = dict(updates)
        updates["reviewed"] = True
        if "reliability_score" not in updates:
            probe = dict(updates)
            probe["capture_mode"] = updates.get("capture_mode", "micro_checkout")
            probe["field_provenance"] = updates.get("field_provenance", {})
            updates["reliability_score"] = estimate_reliability(probe)
        return update_metric_entry(self._praxis_dir, entry_id, updates) is not None

    def get_unreviewed_count(self) -> int:
        """Count unreviewed sprint entries."""
        entries = self.get_recent_sessions(limit=1000)
        return sum(1 for e in entries if not e.get("reviewed", True))

    # ------------------------------------------------------------------
    # Dashboard data
    # ------------------------------------------------------------------

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Compute dashboard summary. Returns dict with all display fields."""
        if not self.is_initialized():
            return {"initialized": False}

        state = self._state or {}
        entries = load_all_metrics(self._praxis_dir) if self._praxis_dir else []
        summary = compute_summary(entries)

        # Days active
        installed_at = state.get("installed_at")
        days_active = 0
        if installed_at:
            from datetime import datetime, timezone
            try:
                installed_dt = datetime.fromisoformat(installed_at.replace("Z", "+00:00"))
                days_active = (datetime.now(timezone.utc) - installed_dt).days
            except (ValueError, TypeError):
                pass

        # Date range
        first_ts = entries[0].get("timestamp", "") if entries else ""
        last_ts = entries[-1].get("timestamp", "") if entries else ""

        # System-level platform detection (not just from saved state)
        platforms = detect_platforms(self._project_dir if self._project_dir else None)

        # If state has platforms but detection found more, merge
        saved_platforms = state.get("platform_ids", [])
        for p in saved_platforms:
            if p not in platforms:
                platforms.append(p)

        # Unreviewed count
        unreviewed_count = 0
        if self._praxis_dir:
            all_entries = load_all_metrics(self._praxis_dir)
            unreviewed_count = sum(
                1 for e in all_entries
                if e.get("type") == "sprint" and not e.get("reviewed", True)
            )

        diagnosis = build_user_diagnosis(
            entries,
            load_governance_events(self._praxis_dir) if self._praxis_dir else [],
            state,
        )
        sessions = load_session_records(self._praxis_dir) if self._praxis_dir else []

        return {
            "initialized": True,
            "participant_id": state.get("participant_id", "N/A"),
            "phase": state.get("phase", "obs"),
            "condition": state.get("condition", ""),
            "logging_active": state.get("logging_active", True),
            "days_active": days_active,
            "total_entries": summary.get("total_entries", 0),
            "session_count": summary.get("total_entries", 0),
            "avg_quality": summary.get("mean_quality"),
            "avg_duration": summary.get("mean_duration"),
            "total_duration": summary.get("total_duration_minutes", 0),
            "autonomy_rate": summary.get("autonomy_rate"),
            "first_entry": first_ts,
            "last_entry": last_ts,
            "platforms": platforms,
            "unreviewed_count": unreviewed_count,
            "passive_capture_count": len(sessions),
            "session_active": self._session_active,
            "session_elapsed_min": self.get_session_elapsed_minutes(),
            "praxis_mode_on": self._praxis_mode_on,
            "diagnosis": diagnosis,
            "git_available": state.get("git_available", True),
        }

    # ------------------------------------------------------------------
    # Log sprint
    # ------------------------------------------------------------------

    def log_sprint(
        self,
        task: str,
        duration: int,
        model: str,
        quality: int,
        iterations: int = 1,
        interventions: int = 0,
        iteration_type: Optional[str] = None,
        design_quality: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build and append a metric entry. Returns the entry dict."""
        if not self.is_initialized():
            raise StateNotFoundError("PRAXIS not initialized")

        entry = build_metric_entry(
            state=self._state,
            task=task,
            duration=duration,
            model=model,
            quality=quality,
            iterations=iterations,
            interventions=interventions,
            iteration_type=iteration_type,
            design_quality=design_quality,
            notes=notes,
            project_dir=self._project_dir,
        )
        entry["capture_mode"] = "manual"
        entry["reviewed"] = True
        entry["field_provenance"] = {
            "task": "manual",
            "duration": "manual",
            "model": "manual",
            "quality": "manual",
            "interventions": "manual",
        }
        entry["reliability_score"] = estimate_reliability(entry)
        append_metric_entry(self._praxis_dir, entry)
        self.touch_active()
        return entry

    # ------------------------------------------------------------------
    # Domain detection
    # ------------------------------------------------------------------

    def is_creative_project(self) -> bool:
        if self._project_dir is None:
            return False
        try:
            return detect_project_type(self._project_dir) == "creative"
        except Exception:
            return False

    # ------------------------------------------------------------------
    # PRAXIS-Q Survey
    # ------------------------------------------------------------------

    def save_praxis_q(
        self,
        scores: Dict[str, int],
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Save a PRAXIS-Q survey response as a metric entry with survey type."""
        if not self.is_initialized():
            raise StateNotFoundError("PRAXIS not initialized")

        import json
        from datetime import datetime, timezone

        entry = {
            "id": praxis_collector._generate_entry_id("praxis_q"),
            "timestamp": praxis_collector._now_iso(),
            "type": "praxis_q",
            "participant_id": self._state.get("participant_id"),
            "phase": self._state.get("phase", "obs"),
            "scores": scores,
            "notes": notes or {},
            "average": sum(scores.values()) / len(scores) if scores else 0,
            # Fields required by validator (PRAXIS-Q is a survey, not a sprint)
            "task": "PRAXIS-Q survey",
            "duration_minutes": 0,
            "quality_self": 3,
            "condition": "obs",
            "model": "n/a",
            "iterations": 0,
            "interventions": 0,
        }

        # Write directly to metrics.jsonl, bypass validation for survey type
        metrics_path = self._praxis_dir / "metrics.jsonl"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.touch_active()
        return entry

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_zip(self, redact_tasks: bool = False) -> Path:
        """Export anonymized ZIP to the project directory. Returns path to generated file."""
        if self._praxis_dir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        # Always export to the project directory (parent of .praxis/)
        output_dir = self._praxis_dir.parent if self._praxis_dir else self._project_dir
        return export_participant_zip(
            self._praxis_dir,
            redact_tasks=redact_tasks,
            output_dir=output_dir,
        )

    def submit_latest_export(self, redact_tasks: bool = False) -> Dict[str, Any]:
        if self._praxis_dir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        zip_path = self.export_zip(redact_tasks=redact_tasks)
        state = self._state or load_state(self._praxis_dir)
        diagnosis = build_user_diagnosis(
            load_all_metrics(self._praxis_dir),
            load_governance_events(self._praxis_dir),
            state,
        )
        result = submit_export(
            self._praxis_dir,
            zip_path,
            state.get("participant_id", "PRAXIS-UNKNOWN"),
            diagnosis,
        )
        result["zip_path"] = zip_path
        return result

    def get_export_info(self) -> Dict[str, Any]:
        """Get info about current data for export tab."""
        if not self.is_initialized():
            return {"initialized": False}

        entries = load_all_metrics(self._praxis_dir) if self._praxis_dir else []
        gov_events = load_governance_events(self._praxis_dir) if self._praxis_dir else []

        first_ts = entries[0].get("timestamp", "") if entries else ""
        last_ts = entries[-1].get("timestamp", "") if entries else ""
        diagnosis = build_user_diagnosis(entries, gov_events, self._state or {})
        submission = get_submission_status(self._praxis_dir)
        sessions = load_session_records(self._praxis_dir) if self._praxis_dir else []

        return {
            "initialized": True,
            "metrics_count": len(entries),
            "governance_count": len(gov_events),
            "session_capture_count": len(sessions),
            "first_entry": first_ts,
            "last_entry": last_ts,
            "diagnosis": diagnosis,
            "submission": submission,
        }

    def write_submission_template(self) -> Path:
        if self._praxis_dir is None:
            raise StateNotFoundError("PRAXIS not initialized")
        path = self._praxis_dir / "submission.json"
        path.write_text(submission_setup_template(), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Protocol Management
    # ------------------------------------------------------------------

    # Protocol injection methods removed — prescriptive injection is a post-thesis product.
