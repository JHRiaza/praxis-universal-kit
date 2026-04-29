"""
PRAXIS Adapter — Cursor (Tier 2)
=================================
Detects: .cursor/ directory OR .cursorrules file in project root.
Injects: .cursor/rules/praxis.md (preferred) or .cursorrules (legacy).

Cursor AI IDE reads .cursorrules from project root for older versions,
and .cursor/rules/*.md files for newer modular rule sets.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_RULES_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# PRAXIS Governance Rules for Cursor

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`

"""


class CursorAdapter(PraxisAdapter):
    """PRAXIS adapter for Cursor AI IDE (Tier 2)."""

    PLATFORM_ID = "cursor"

    def detect(self) -> bool:
        cwd = Path.cwd()
        if (cwd / ".cursor").is_dir():
            return True
        if (cwd / ".cursorrules").is_file():
            return True
        return shutil.which("cursor") is not None

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        soul = self._soul(templates_dir, workspace_dir)
        agents = self._agents(templates_dir, workspace_dir)
        content = _RULES_HEADER + soul + "\n\n---\n\n## Operational Procedures\n\n" + agents

        cursor_dir = workspace_dir / ".cursor"

        if cursor_dir.is_dir():
            # Prefer modular rules file for newer Cursor
            rules_dir = cursor_dir / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            dest = rules_dir / "praxis.md"
            if not dest.is_file():
                _write_file(dest, content)
                created.append(str(dest))
        else:
            # Fall back to flat .cursorrules
            dest = workspace_dir / ".cursorrules"
            if dest.is_file():
                existing = dest.read_text(encoding="utf-8")
                if _MARKER not in existing:
                    dest.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
                    created.append(f"{dest} (updated)")
            else:
                _write_file(dest, content)
                created.append(str(dest))

        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []

        # Remove modular rules file
        modular = workspace_dir / ".cursor" / "rules" / "praxis.md"
        result = _remove_file(modular)
        if result:
            removed.append(result)

        # Clean .cursorrules if PRAXIS-created
        cursorrules = workspace_dir / ".cursorrules"
        if cursorrules.is_file():
            text = cursorrules.read_text(encoding="utf-8")
            if text.strip().startswith(_MARKER):
                result = _remove_file(cursorrules)
                if result:
                    removed.append(result)

        return removed

    def get_info(self) -> Dict[str, Any]:
        cwd = Path.cwd()
        has_cursor_dir = (cwd / ".cursor").is_dir()
        return {
            "id": self.PLATFORM_ID,
            "name": "Cursor",
            "tier": 2,
            "description": "Injects PRAXIS governance into Cursor rules.",
            "governance_files": (
                [".cursor/rules/praxis.md"] if has_cursor_dir else [".cursorrules"]
            ),
            "instructions": (
                "Cursor will load PRAXIS governance rules automatically. "
                "Edit .cursor/rules/praxis.md (or .cursorrules) to add "
                "project-specific Cursor rules."
            ),
        }
