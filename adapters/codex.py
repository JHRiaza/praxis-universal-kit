"""
PRAXIS Adapter — OpenAI Codex / Codex CLI (Tier 2)
===================================================
Detects: `codex` in PATH OR .codex/ directory in project root.
Injects: AGENTS.md in project root.

Codex reads AGENTS.md as a persistent instruction file for the sandbox agent.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_AGENTS_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# AGENTS.md — PRAXIS Governance Active

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance study (Phase B). Governance injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`
> Log governance events: `praxis govern "description"`

"""


class CodexAdapter(PraxisAdapter):
    """PRAXIS adapter for OpenAI Codex / Codex CLI (Tier 2)."""

    PLATFORM_ID = "codex"

    def detect(self) -> bool:
        cwd = Path.cwd()
        if (cwd / "AGENTS.md").is_file():
            return True
        if (cwd / ".codex").is_dir():
            return True
        if shutil.which("codex") is not None:
            return True
        if os.environ.get("OPENAI_API_KEY"):
            return True
        return False

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        dest = workspace_dir / "AGENTS.md"

        agents = self._agents(templates_dir, workspace_dir)
        soul = self._soul(templates_dir, workspace_dir)
        content = _AGENTS_HEADER + agents + "\n\n---\n\n## Governance Principles\n\n" + soul

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
        dest = workspace_dir / "AGENTS.md"
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
            "name": "OpenAI Codex / Codex CLI",
            "tier": 2,
            "description": "Injects PRAXIS governance into AGENTS.md for Codex sandbox.",
            "governance_files": ["AGENTS.md"],
            "instructions": (
                "AGENTS.md has been created/updated with PRAXIS governance. "
                "Codex reads this file automatically as agent instructions. "
                "Edit it to add project-specific agent rules."
            ),
        }
