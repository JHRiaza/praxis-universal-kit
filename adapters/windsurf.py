"""
PRAXIS Adapter — Windsurf (Tier 2)
====================================
Detects: .windsurf/ directory OR .windsurfrules file in project root.
Injects: .windsurfrules in the project root.

Windsurf (Codeium's AI IDE) reads .windsurfrules from the project root
as persistent instructions applied to every session.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_WINDSURF_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# PRAXIS Governance Rules for Windsurf

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`

"""


class WindsurfAdapter(PraxisAdapter):
    """PRAXIS adapter for Windsurf AI IDE (Tier 2)."""

    PLATFORM_ID = "windsurf"

    def detect(self) -> bool:
        cwd = Path.cwd()
        if (cwd / ".windsurfrules").is_file():
            return True
        if (cwd / ".windsurf").is_dir():
            return True
        return shutil.which("windsurf") is not None

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        dest = workspace_dir / ".windsurfrules"

        soul = self._soul(templates_dir, workspace_dir)
        agents = self._agents(templates_dir, workspace_dir)
        content = _WINDSURF_HEADER + soul + "\n\n---\n\n## Operational Procedures\n\n" + agents

        if dest.is_file():
            existing = dest.read_text(encoding="utf-8")
            if _MARKER in existing:
                return []
            dest.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
            created.append(f"{dest} (updated)")
        else:
            _write_file(dest, content)
            created.append(str(dest))

        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []
        dest = workspace_dir / ".windsurfrules"
        if not dest.is_file():
            return removed

        text = dest.read_text(encoding="utf-8")
        if _MARKER not in text:
            return removed

        if text.strip().startswith(_MARKER):
            result = _remove_file(dest)
            if result:
                removed.append(result)
        else:
            idx = text.find("\n\n" + _MARKER)
            if idx != -1:
                dest.write_text(text[:idx], encoding="utf-8")
                removed.append(f"{dest} (governance section removed)")

        return removed

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.PLATFORM_ID,
            "name": "Windsurf",
            "tier": 2,
            "description": "Injects PRAXIS governance into .windsurfrules.",
            "governance_files": [".windsurfrules"],
            "instructions": (
                "Windsurf reads .windsurfrules automatically. "
                "Customize the PRAXIS governance section to add project-specific rules."
            ),
        }
