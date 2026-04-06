"""
PRAXIS Adapter — Cline (Tier 3)
==================================
Detects: .clinerules file OR .cline/ directory in project root.
Injects: .clinerules (preferred) or .cline/instructions.md.

Cline is a VSCode extension (formerly Claude Dev) that reads .clinerules
from the project root as persistent instructions.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_CLINE_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# PRAXIS Governance Rules for Cline

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance study (Phase B). Rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`
> Log governance events: `praxis govern "description"`

"""


class ClineAdapter(PraxisAdapter):
    """PRAXIS adapter for Cline VSCode extension (Tier 3)."""

    PLATFORM_ID = "cline"

    def detect(self) -> bool:
        cwd = Path.cwd()
        return (
            (cwd / ".clinerules").is_file()
            or (cwd / ".cline").is_dir()
            or (cwd / ".cline" / "instructions.md").is_file()
        )

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        soul = self._soul(templates_dir)
        agents = self._agents(templates_dir)
        content = (
            _CLINE_HEADER
            + soul
            + "\n\n---\n\n## Operational Procedures\n\n"
            + agents
        )

        # Prefer .clinerules in project root
        clinerules = workspace_dir / ".clinerules"
        if clinerules.is_file():
            existing = clinerules.read_text(encoding="utf-8")
            if _MARKER not in existing:
                clinerules.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
                created.append(f"{clinerules} (updated)")
            return created

        # Try .cline/instructions.md
        cline_dir = workspace_dir / ".cline"
        if cline_dir.is_dir():
            instructions = cline_dir / "instructions.md"
            if instructions.is_file():
                existing = instructions.read_text(encoding="utf-8")
                if _MARKER not in existing:
                    instructions.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
                    created.append(f"{instructions} (updated)")
            else:
                _write_file(instructions, content)
                created.append(str(instructions))
            return created

        # Create .clinerules
        _write_file(clinerules, content)
        created.append(str(clinerules))
        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []

        for dest in [
            workspace_dir / ".clinerules",
            workspace_dir / ".cline" / "instructions.md",
        ]:
            if dest.is_file():
                text = dest.read_text(encoding="utf-8")
                if _MARKER in text:
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
            "name": "Cline",
            "tier": 3,
            "description": "Injects PRAXIS governance into .clinerules or .cline/instructions.md.",
            "governance_files": [".clinerules", ".cline/instructions.md"],
            "instructions": (
                "Cline reads .clinerules from project root. "
                "PRAXIS governance is now included as persistent instructions."
            ),
        }
