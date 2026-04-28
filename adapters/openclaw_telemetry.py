"""
PRAXIS Telemetry Adapter - OpenClaw (read-only)
================================================
Captures lightweight OpenClaw workspace telemetry without modifying the host.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class OpenClawAdapter:
    """Read-only telemetry adapter for OpenClaw workspace activity."""

    name = "openclaw"

    def __init__(self, workspace_path: Optional[Path] = None):
        default_workspace = (Path.home() / ".openclaw" / "workspace").resolve()
        candidate = (workspace_path or default_workspace).resolve()
        if workspace_path is not None and not self._looks_like_workspace(candidate) and self._looks_like_workspace(default_workspace):
            candidate = default_workspace
        self._workspace = candidate

    def detect(self) -> bool:
        """Return True if OpenClaw workspace exists and appears active."""
        return self._looks_like_workspace(self._workspace)

    def capture_session_context(self) -> Dict[str, Any]:
        """Capture current OpenClaw context from the workspace."""
        session_state_path = self._workspace / "session_state.json"
        memory_path = self._workspace / "MEMORY.md"
        workspace_exists = self._workspace.is_dir()
        state = self._load_json(session_state_path)
        last_activity = self._find_last_activity()

        return {
            "detected": self.detect(),
            "workspace_exists": workspace_exists,
            "has_session_state": session_state_path.is_file(),
            "has_memory": memory_path.is_file(),
            "memory_size_bytes": memory_path.stat().st_size if memory_path.is_file() else None,
            "model_info": self._extract_model_info(state),
            "active_projects": self._active_projects(),
            "last_activity": self._to_iso(last_activity),
        }

    def estimate_turns(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Estimate turns by grouping file modifications into 60-second windows."""
        start_dt = self._parse_dt(start_time)
        end_dt = self._parse_dt(end_time)
        if start_dt is None or end_dt is None or end_dt < start_dt:
            return {"estimated_turns": 0, "files_modified": 0, "windows_detected": []}

        timestamps: List[datetime] = []
        for path in self._iter_workspace_files():
            try:
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if start_dt <= modified <= end_dt:
                timestamps.append(modified)

        timestamps.sort()
        windows: List[Dict[str, Any]] = []
        current_start: Optional[datetime] = None
        current_end: Optional[datetime] = None
        current_count = 0

        for ts in timestamps:
            if current_start is None:
                current_start = ts
                current_end = ts
                current_count = 1
                continue
            if (ts - current_end).total_seconds() <= 60:
                current_end = ts
                current_count += 1
                continue
            windows.append({
                "start": self._to_iso(current_start),
                "end": self._to_iso(current_end),
                "files": current_count,
            })
            current_start = ts
            current_end = ts
            current_count = 1

        if current_start is not None and current_end is not None:
            windows.append({
                "start": self._to_iso(current_start),
                "end": self._to_iso(current_end),
                "files": current_count,
            })

        return {
            "estimated_turns": len(windows),
            "files_modified": len(timestamps),
            "windows_detected": windows,
        }

    def _active_projects(self) -> List[str]:
        projects: List[str] = []
        if not self._workspace.is_dir():
            return projects

        seen = set()
        for path in sorted(self._workspace.glob("MS_*.md")):
            name = path.stem[3:]
            if name and name not in seen:
                seen.add(name)
                projects.append(name)

        excluded = {
            ".git",
            ".github",
            ".venv",
            "__pycache__",
            "build",
            "dist",
            "memory",
            "plans",
            "node_modules",
            "collector",
            "desktop",
            "export",
            "templates",
            "surveys",
            "config",
            "adapters",
        }
        for child in sorted(self._workspace.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if child.name.startswith(".") or child.name in excluded:
                continue
            if child.name not in seen:
                seen.add(child.name)
                projects.append(child.name)
        return projects[:25]

    def _find_last_activity(self) -> Optional[datetime]:
        latest: Optional[datetime] = None
        for path in self._iter_workspace_files():
            try:
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if latest is None or modified > latest:
                latest = modified
        return latest

    def _iter_workspace_files(self) -> Iterable[Path]:
        if not self._workspace.is_dir():
            return []
        excluded = {".git", ".venv", "__pycache__", "node_modules", "build", "dist"}
        files: List[Path] = []
        stack = [self._workspace]
        while stack:
            current = stack.pop()
            try:
                children = list(current.iterdir())
            except OSError:
                continue
            for child in children:
                if child.name in excluded:
                    continue
                if child.is_dir():
                    stack.append(child)
                elif child.is_file():
                    files.append(child)
        return files

    def _extract_model_info(self, state: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(state, dict):
            return None
        model_info: Dict[str, Any] = {}
        for key in (
            "model",
            "default_model",
            "fallback_model",
            "fallback_chain",
            "model_provider",
            "active_topics",
        ):
            value = state.get(key)
            if value not in (None, "", [], {}):
                model_info[key] = value
        discord = state.get("discord")
        if isinstance(discord, dict) and discord.get("status"):
            model_info["discord_status"] = discord.get("status")
        return model_info or None

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def _looks_like_workspace(self, path: Path) -> bool:
        return (path / "session_state.json").is_file() or (path / "MEMORY.md").is_file()

    def _parse_dt(self, value: str) -> Optional[datetime]:
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
