"""
PRAXIS Universal Kit — Cowork/Claude Bridge Telemetry Adapter
==============================================================
Read-only adapter that captures telemetry from Claude Cowork sessions
dispatched through the .cowork-bridge/ inbox/outbox pattern.

Reads from:
- .cowork-bridge/in/ — dispatched task briefs
- .cowork-bridge/out/ — completed task responses

Zero external dependencies. Python 3.8+ compatible.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class CoworkAdapter:
    """Read-only telemetry adapter for Claude Cowork bridge sessions."""

    name = "cowork"

    def __init__(self, bridge_dir: Optional[Path] = None) -> None:
        # Default: look inside the OpenClaw workspace
        if bridge_dir is not None:
            self._bridge_dir = bridge_dir
        else:
            # Try workspace path first, then home-relative
            ws = Path(os.environ.get("OPENCLAW_WORKSPACE", "")).expanduser()
            if ws.is_dir() and (ws / ".cowork-bridge").is_dir():
                self._bridge_dir = ws / ".cowork-bridge"
            else:
                self._bridge_dir = Path.home() / ".openclaw" / "workspace" / ".cowork-bridge"

    def detect(self) -> bool:
        """Return True if the cowork-bridge directory exists."""
        return self._bridge_dir.is_dir()

    def capture_session_context(self) -> Dict[str, Any]:
        """Capture current Cowork bridge state (read-only).

        Returns:
            dict with: detected, bridge_exists, in_dir_exists, out_dir_exists,
            pending_count, completed_count, latest_task, total_in_bytes,
            total_out_bytes
        """
        result: Dict[str, Any] = {
            "detected": self.detect(),
            "bridge_exists": self._bridge_dir.is_dir(),
            "in_dir_exists": False,
            "out_dir_exists": False,
            "pending_count": 0,
            "completed_count": 0,
            "latest_task": None,
            "total_in_bytes": 0,
            "total_out_bytes": 0,
        }

        if not result["bridge_exists"]:
            return result

        in_dir = self._bridge_dir / "in"
        out_dir = self._bridge_dir / "out"

        result["in_dir_exists"] = in_dir.is_dir()
        result["out_dir_exists"] = out_dir.is_dir()

        # Scan inbox
        in_files: List[Dict[str, Any]] = []
        if in_dir.is_dir():
            for f in in_dir.iterdir():
                if f.is_file() and f.suffix == ".md":
                    stat = f.stat()
                    in_files.append({
                        "name": f.name,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    })
                    result["total_in_bytes"] += stat.st_size

        result["pending_count"] = len(in_files)

        # Scan outbox
        out_files: List[Dict[str, Any]] = []
        if out_dir.is_dir():
            for f in out_dir.iterdir():
                if f.is_file() and f.suffix == ".md":
                    stat = f.stat()
                    out_files.append({
                        "name": f.name,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    })
                    result["total_out_bytes"] += stat.st_size

        result["completed_count"] = len(out_files)

        # Find latest task (most recently modified across in+out)
        all_files = in_files + out_files
        if all_files:
            latest = max(all_files, key=lambda x: x.get("modified", ""))
            result["latest_task"] = {
                "name": latest["name"],
                "modified": latest.get("modified"),
                "size_bytes": latest.get("size_bytes", 0),
                "is_response": "-response" in latest.get("name", ""),
            }

        return result

    def capture_session_in_range(
        self,
        start_time: str,
        end_time: str,
    ) -> Optional[Dict[str, Any]]:
        """Find Cowork bridge tasks that were active within the given time range.

        Args:
            start_time: ISO timestamp for range start.
            end_time: ISO timestamp for range end.

        Returns:
            dict with matched tasks, or None if bridge not detected.
        """
        if not self.detect():
            return None

        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

        matched_in: List[Dict[str, Any]] = []
        matched_out: List[Dict[str, Any]] = []

        in_dir = self._bridge_dir / "in"
        out_dir = self._bridge_dir / "out"

        for f_list, target in [(matched_in, in_dir), (matched_out, out_dir)]:
            if not target.is_dir():
                continue
            for f in target.iterdir():
                if not f.is_file() or f.suffix != ".md":
                    continue
                try:
                    stat = f.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    if start_dt <= mtime <= end_dt:
                        f_list.append({
                            "name": f.name,
                            "size_bytes": stat.st_size,
                            "modified": mtime.isoformat(),
                        })
                except (OSError, ValueError):
                    continue

        if not matched_in and not matched_out:
            return None

        return {
            "time_range": {"start": start_time, "end": end_time},
            "dispatched_in_range": matched_in,
            "completed_in_range": matched_out,
            "dispatched_count": len(matched_in),
            "completed_count": len(matched_out),
        }
