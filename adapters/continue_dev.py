"""
PRAXIS Adapter — Continue.dev (Tier 3)
=======================================
Detects: .continue/ directory in project root.
Injects: .continue/rules/praxis.md + updates .continue/config.json.

Continue.dev is a VSCode/JetBrains AI coding extension that reads rules
from .continue/rules/*.md and configuration from .continue/config.json.

Python 3.8+. Zero external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import PraxisAdapter, _write_file, _remove_file

_MARKER = "<!-- PRAXIS-GOVERNANCE -->"
_SYS_MARKER = "PRAXIS-GOVERNANCE"

_RULES_HEADER = """\
<!-- PRAXIS-GOVERNANCE -->
# PRAXIS Governance Rules for Continue.dev

> **PRAXIS Research Study**: This workspace participates in the PRAXIS AI
> governance rules injected via `praxis activate`.
>
> Log tasks: `praxis log "desc" -d MIN -m MODEL -q 1-5 -i N -h N`

"""


class ContinueDevAdapter(PraxisAdapter):
    """PRAXIS adapter for Continue.dev VSCode/JetBrains extension (Tier 3)."""

    PLATFORM_ID = "continue_dev"

    def detect(self) -> bool:
        cwd = Path.cwd()
        return (
            (cwd / ".continue").is_dir()
            or (cwd / ".continue" / "config.json").is_file()
        )

    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        created: List[str] = []

        continue_dir = workspace_dir / ".continue"
        continue_dir.mkdir(parents=True, exist_ok=True)

        soul = self._soul(templates_dir, workspace_dir)
        agents = self._agents(templates_dir, workspace_dir)

        # 1. Create .continue/rules/praxis.md
        rules_dir = continue_dir / "rules"
        rules_dir.mkdir(exist_ok=True)
        rules_file = rules_dir / "praxis.md"

        if not rules_file.is_file():
            rules_content = (
                _RULES_HEADER
                + soul
                + "\n\n---\n\n## Operational Procedures\n\n"
                + agents
            )
            _write_file(rules_file, rules_content)
            created.append(str(rules_file))

        # 2. Update .continue/config.json systemMessage
        config_file = continue_dir / "config.json"
        config = self._load_json(config_file) or self._default_config()

        system_msg = config.get("systemMessage", "")
        if _SYS_MARKER not in system_msg:
            praxis_note = (
                f"\n\n[{_SYS_MARKER}]\n"
                "You are operating under the PRAXIS governance framework. "
                "See .continue/rules/praxis.md for full governance rules and "
                "operational procedures."
            )
            config["systemMessage"] = system_msg + praxis_note
            self._save_json(config_file, config)
            created.append(f"{config_file} (updated)")

        return created

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        removed: List[str] = []

        # Remove rules file
        rules_file = workspace_dir / ".continue" / "rules" / "praxis.md"
        result = _remove_file(rules_file)
        if result:
            removed.append(result)

        # Clean config.json systemMessage
        config_file = workspace_dir / ".continue" / "config.json"
        config = self._load_json(config_file)
        if config and _SYS_MARKER in config.get("systemMessage", ""):
            msg = config["systemMessage"]
            idx = msg.find(f"\n\n[{_SYS_MARKER}]")
            if idx != -1:
                config["systemMessage"] = msg[:idx]
                self._save_json(config_file, config)
                removed.append(f"{config_file} (governance section removed)")

        return removed

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.PLATFORM_ID,
            "name": "Continue.dev",
            "tier": 3,
            "description": "Injects PRAXIS governance into Continue.dev rules and config.",
            "governance_files": [
                ".continue/rules/praxis.md",
                ".continue/config.json",
            ],
            "instructions": (
                "PRAXIS governance has been added to .continue/rules/praxis.md. "
                ".continue/config.json system prompt has been updated. "
                "Continue.dev will apply these rules in every session."
            ),
        }

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> Optional[Dict[str, Any]]:
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
        return None

    @staticmethod
    def _save_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            "models": [],
            "systemMessage": "",
            "tabAutocompleteModel": None,
            "customCommands": [],
        }
