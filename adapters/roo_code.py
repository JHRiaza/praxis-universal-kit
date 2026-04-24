"""
PRAXIS Adapter — Roo Code (Tier 3)
=====================================
Detects: .roorules file OR .roo/ directory in project root.
Injects: .roorules (preferred) or .roo/rules.md.

Roo Code is a VSCode extension (fork of Cline) that reads .roorules
from the project root as persistent instructions.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"

_ROO_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# PRAXIS Governance Rules for Roo Code

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance study (Phase B). Rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`
> Log governance events: `praxis govern "description"`

"""


class RooCodeAdapter(PraxisAdapter):
    """PRAXIS adapter for Roo Code VSCode extension (Tier 3)."""

    PLATFORM_ID = "roo_code"

    def detect(self) -> bool:
        cwd = Path.cwd()
        return (
            (cwd / ".roorules").is_file()
            or (cwd / ".roo").is_dir()
            or (cwd / ".roo" / "rules.md").is_file()
        )

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []
        soul = self._soul(templates_dir, workspace_dir)
        agents = self._agents(templates_dir, workspace_dir)
        content = (
            _ROO_HEADER
            + soul
            + "\n\n---\n\n## Operational Procedures\n\n"
            + agents
        )

        # Prefer .roorules in project root
        roorules = workspace_dir / ".roorules"
        if roorules.is_file():
            existing = roorules.read_text(encoding="utf-8")
            if _MARKER not in existing:
                roorules.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
                created.append(f"{roorules} (updated)")
            return created

        # Try .roo/rules.md
        roo_dir = workspace_dir / ".roo"
        if roo_dir.is_dir():
            rules_file = roo_dir / "rules.md"
            if rules_file.is_file():
                existing = rules_file.read_text(encoding="utf-8")
                if _MARKER not in existing:
                    rules_file.write_text(existing.rstrip() + "\n\n" + content, encoding="utf-8")
                    created.append(f"{rules_file} (updated)")
            else:
                _write_file(rules_file, content)
                created.append(str(rules_file))
            return created

        # Create .roorules
        _write_file(roorules, content)
        created.append(str(roorules))
        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []

        for dest in [
            workspace_dir / ".roorules",
            workspace_dir / ".roo" / "rules.md",
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
            "name": "Roo Code",
            "tier": 3,
            "description": "Injects PRAXIS governance into .roorules or .roo/rules.md.",
            "governance_files": [".roorules", ".roo/rules.md"],
            "instructions": (
                "Roo Code reads .roorules from project root. "
                "PRAXIS governance is now included as persistent instructions."
            ),
        }
