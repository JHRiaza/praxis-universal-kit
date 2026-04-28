"""
PRAXIS Telemetry Adapter - Codex (read-only)
============================================
Captures lightweight Codex session telemetry from local JSONL logs.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


class CodexAdapter:
    """Read-only telemetry adapter for Codex session logs."""

    name = "codex"

    def __init__(self, codex_dir: Optional[Path] = None):
        self._codex_dir = (codex_dir or Path.home() / ".codex" / "sessions").resolve()

    def detect(self) -> bool:
        """Return True if Codex sessions directory exists."""
        return self._codex_dir.is_dir()

    def capture_session_context(self) -> Dict[str, Any]:
        """Capture the latest Codex session summary."""
        session_files = self._session_files()
        latest = self._parse_session_file(session_files[0]) if session_files else None
        return {
            "detected": self.detect(),
            "sessions_dir_exists": self._codex_dir.is_dir(),
            "session_count": len(session_files),
            "latest_session": latest,
        }

    def capture_session_in_range(self, start_time: str, end_time: str) -> Optional[Dict[str, Any]]:
        """Find the latest session whose timeline overlaps the supplied range."""
        start_dt = self._parse_dt(start_time)
        end_dt = self._parse_dt(end_time)
        if start_dt is None or end_dt is None or end_dt < start_dt:
            return None

        for session_path in self._session_files():
            session = self._parse_session_file(session_path)
            if not session:
                continue
            session_start = self._parse_dt(session.get("started_at"))
            session_end = self._parse_dt(session.get("ended_at")) or session_start
            if session_start is None:
                continue
            if session_end is None:
                session_end = session_start
            if session_start <= end_dt and session_end >= start_dt:
                return session
        return None

    def _parse_session_file(self, session_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single Codex JSONL session file. Returns None on malformed input."""
        if not session_path.is_file():
            return None

        records: List[Dict[str, Any]] = []
        try:
            with session_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        records.append(item)
        except OSError:
            return None

        if not records:
            return None

        session_id = None
        model = None
        started_at = None
        ended_at = None
        turn_ids: Set[str] = set()
        files_touched: Set[str] = set()

        for record in records:
            record_ts = self._pick_timestamp(record)
            if record_ts:
                started_at = record_ts if started_at is None or record_ts < started_at else started_at
                ended_at = record_ts if ended_at is None or record_ts > ended_at else ended_at

            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            if session_id is None and isinstance(payload.get("id"), str):
                session_id = payload.get("id")
            candidate_model = self._extract_model(record)
            if self._model_score(candidate_model) > self._model_score(model):
                model = candidate_model

            turn_id = self._extract_turn_id(record)
            if turn_id:
                turn_ids.add(turn_id)

            files_touched.update(self._extract_paths(record))

        if session_id is None:
            session_id = session_path.stem

        return {
            "id": session_id,
            "model": model or "unknown",
            "turns": len(turn_ids),
            "files_touched": sorted(files_touched)[:50],
            "started_at": self._to_iso(started_at),
            "ended_at": self._to_iso(ended_at),
            "size_bytes": session_path.stat().st_size,
        }

    def _session_files(self) -> List[Path]:
        if not self._codex_dir.is_dir():
            return []
        files = [p for p in self._codex_dir.rglob("*.jsonl") if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files

    def _extract_model(self, record: Dict[str, Any]) -> Optional[str]:
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        for source in (payload, record):
            for key in ("model", "default_model", "model_provider"):
                value = source.get(key) if isinstance(source, dict) else None
                if isinstance(value, str) and value:
                    return value
        if isinstance(payload.get("base_instructions"), dict):
            provider = payload.get("model_provider")
            if isinstance(provider, str) and provider:
                return provider
        return None

    def _model_score(self, value: Optional[str]) -> int:
        if not value:
            return 0
        lowered = value.lower()
        if lowered in {"openai", "anthropic", "google", "unknown"}:
            return 1
        return 2

    def _extract_turn_id(self, record: Dict[str, Any]) -> Optional[str]:
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        if isinstance(payload.get("turn_id"), str):
            return payload.get("turn_id")
        if isinstance(record.get("turn_id"), str):
            return record.get("turn_id")
        if record.get("type") == "turn_context" and isinstance(payload.get("turn_id"), str):
            return payload.get("turn_id")
        return None

    def _extract_paths(self, value: Any) -> Set[str]:
        found: Set[str] = set()
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"path", "filePath", "workdir", "cwd"} and isinstance(item, str) and item:
                    found.add(item)
                elif key in {"paths", "files"} and isinstance(item, list):
                    for entry in item:
                        if isinstance(entry, str) and entry:
                            found.add(entry)
                else:
                    found.update(self._extract_paths(item))
        elif isinstance(value, list):
            for item in value:
                found.update(self._extract_paths(item))
        return found

    def _pick_timestamp(self, record: Dict[str, Any]) -> Optional[datetime]:
        for raw in (
            record.get("timestamp"),
            (record.get("payload") or {}).get("timestamp") if isinstance(record.get("payload"), dict) else None,
            (record.get("payload") or {}).get("started_at") if isinstance(record.get("payload"), dict) else None,
        ):
            dt = self._parse_dt(raw)
            if dt is not None:
                return dt
        return None

    def _parse_dt(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _to_iso(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.astimezone(timezone.utc).isoformat()
