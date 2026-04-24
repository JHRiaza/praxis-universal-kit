"""
PRAXIS Adapter — GitHub Copilot (Tier 3)
=========================================
Detects: .github/copilot-instructions.md in project root.
Injects: .github/copilot-instructions.md with PRAXIS governance block.

GitHub Copilot reads custom instructions from this file automatically
in VS Code and JetBrains with the Copilot extension enabled.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_COPILOT_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# GitHub Copilot Custom Instructions — PRAXIS Governance Active

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance study (Phase B). Governance injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`

"""


class CopilotAdapter(PraxisAdapter):
    """PRAXIS adapter for GitHub Copilot (Tier 3)."""

    PLATFORM_ID = "copilot"

    def detect(self) -> bool:
        cwd = Path.cwd()
        # copilot-instructions.md is the strong signal; .github/ alone is too weak
        return (cwd / ".github" / "copilot-instructions.md").is_file()

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        github_dir = workspace_dir / ".github"
        github_dir.mkdir(parents=True, exist_ok=True)
        dest = github_dir / "copilot-instructions.md"

        soul = self._soul(templates_dir, workspace_dir)
        agents = self._agents(templates_dir, workspace_dir)
        content = _COPILOT_HEADER + soul + "\n\n---\n\n## Operational Procedures\n\n" + agents

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
        dest = workspace_dir / ".github" / "copilot-instructions.md"
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
            "name": "GitHub Copilot",
            "tier": 3,
            "description": "Injects PRAXIS governance into .github/copilot-instructions.md.",
            "governance_files": [".github/copilot-instructions.md"],
            "instructions": (
                ".github/copilot-instructions.md has been updated with PRAXIS governance. "
                "Copilot will use these instructions automatically in VS Code / JetBrains. "
                "Edit the file to add project-specific Copilot instructions."
            ),
        }
