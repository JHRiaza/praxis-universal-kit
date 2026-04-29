"""
PRAXIS Adapter — Claude Cowork / Claude Code (Tier 2)
======================================================
Detects: CLAUDE.md in project root OR ~/.claude/ directory OR `claude` in PATH.
Injects: CLAUDE.md with PRAXIS governance block.

Claude Code reads CLAUDE.md from the project root as persistent project
instructions loaded on every session.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_CLAUDE_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# Project Instructions — PRAXIS Governance Active

> **PRAXIS Research Study**: This workspace is enrolled in the PRAXIS AI
> governance rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`
> Log governance events: `praxis govern "description"`

"""


class ClaudeCoworkAdapter(PraxisAdapter):
    """PRAXIS adapter for Claude Code / Claude Cowork (Tier 2)."""

    PLATFORM_ID = "claude_cowork"

    def detect(self) -> bool:
        cwd = Path.cwd()
        if (cwd / "CLAUDE.md").is_file():
            return True
        if (Path.home() / ".claude").is_dir():
            return True
        if shutil.which("claude") is not None:
            return True
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_HOME"):
            return True
        return False

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        dest = workspace_dir / "CLAUDE.md"

        creative_template = self._creative_claude(templates_dir, workspace_dir)
        if creative_template is not None:
            content = _CLAUDE_HEADER + creative_template
        else:
            soul = self._soul(templates_dir, workspace_dir)
            agents = self._agents(templates_dir, workspace_dir)
            content = _CLAUDE_HEADER + soul + "\n\n---\n\n## Operational Procedures\n\n" + agents

        if dest.is_file():
            existing = dest.read_text(encoding="utf-8")
            if _MARKER in existing:
                return []  # Already injected
            dest.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
            created.append(f"{dest} (updated)")
        else:
            _write_file(dest, content)
            created.append(str(dest))

        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []
        dest = workspace_dir / "CLAUDE.md"
        if not dest.is_file():
            return removed

        text = dest.read_text(encoding="utf-8")
        if _MARKER not in text:
            return removed

        # If the whole file is PRAXIS content, delete it
        if text.strip().startswith(_MARKER):
            result = _remove_file(dest)
            if result:
                removed.append(result)
        else:
            # File pre-existed — strip the PRAXIS block
            idx = text.find("\n\n" + _MARKER)
            if idx != -1:
                dest.write_text(text[:idx], encoding="utf-8")
                removed.append(f"{dest} (governance section removed)")

        return removed

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.PLATFORM_ID,
            "name": "Claude Cowork (Claude Code / Claude.ai)",
            "tier": 2,
            "description": "Injects PRAXIS governance into CLAUDE.md project instructions.",
            "governance_files": ["CLAUDE.md"],
            "instructions": (
                "CLAUDE.md has been created/updated with PRAXIS governance. "
                "Claude Code reads this automatically on every session. "
                "Edit it to add project-specific rules and governance principles."
            ),
        }
