"""
PRAXIS Adapters — Base Class & Shared Utilities
================================================
Provides PraxisAdapter ABC and helper functions for platform adapters.

All adapters MUST also expose module-level functions for CLI compatibility:
  detect() -> bool
  inject_governance(templates_dir: Path) -> List[str]
  get_info() -> Dict[str, Any]

Class-based adapters delegate from these module-level functions to instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class PraxisAdapter(ABC):
    """Abstract base class for all PRAXIS platform adapters."""

    PLATFORM_ID: str = "unknown"

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this platform is present in the current environment."""

    @abstractmethod
    def inject_governance(
        self,
        templates_dir: Path,
        workspace_dir: Path,
    ) -> List[str]:
        """
        Inject PRAXIS governance files into the platform config location.
        Returns list of file paths that were created or modified.
        """

    def remove_governance(self, workspace_dir: Path) -> List[str]:
        """Remove previously injected PRAXIS governance. Optional."""
        return []

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return metadata about this platform and its governance integration."""

    # Template loading helpers
    def _soul(self, templates_dir: Path) -> str:
        return _load_template(templates_dir, "SOUL_TEMPLATE.md")

    def _agents(self, templates_dir: Path) -> str:
        return _load_template(templates_dir, "AGENTS_TEMPLATE.md")

    def _memory(self, templates_dir: Path) -> str:
        return _load_template(templates_dir, "MEMORY_TEMPLATE.md")


def _load_template(templates_dir: Path, filename: str) -> str:
    """Load a governance template file. Returns placeholder if not found."""
    path = templates_dir / filename
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"# {filename}\n\n[Template not found — see PRAXIS kit templates/governance/]\n"


def _write_file(path: Path, content: str) -> None:
    """Write content to path, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _remove_file(path: Path) -> Optional[str]:
    """Delete a file if it exists. Returns its path string if deleted."""
    if path.is_file():
        path.unlink()
        return str(path)
    return None
