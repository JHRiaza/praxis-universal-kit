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
from typing import Any, Dict, Iterable, List, Optional, Tuple


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

    def _soul(self, templates_dir: Path, workspace_dir: Optional[Path] = None) -> str:
        return _load_template(
            _select_template_dir(templates_dir, workspace_dir),
            "SOUL_TEMPLATE.md",
        )

    def _agents(self, templates_dir: Path, workspace_dir: Optional[Path] = None) -> str:
        return _load_template(
            _select_template_dir(templates_dir, workspace_dir),
            "AGENTS_TEMPLATE.md",
        )

    def _memory(self, templates_dir: Path, workspace_dir: Optional[Path] = None) -> str:
        return _load_template(
            _select_template_dir(templates_dir, workspace_dir),
            "MEMORY_TEMPLATE.md",
        )

    def _creative_claude(self, templates_dir: Path, workspace_dir: Path) -> Optional[str]:
        if detect_project_type(workspace_dir) != "creative":
            return None
        creative_template = _template_root(templates_dir) / "creative" / "CLAUDE_DESIGN_TEMPLATE.md"
        if creative_template.is_file():
            return creative_template.read_text(encoding="utf-8")
        return None


def _load_template(templates_dir: Path, filename: str) -> str:
    """Load a governance template file. Returns placeholder if not found."""
    path = templates_dir / filename
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"# {filename}\n\n[Template not found - see PRAXIS kit templates/governance/]\n"



def _template_root(templates_dir: Path) -> Path:
    """Normalize either /templates or /templates/governance to the templates root."""
    if templates_dir.name == "governance":
        return templates_dir.parent
    return templates_dir


def _select_template_dir(templates_dir: Path, workspace_dir: Optional[Path] = None) -> Path:
    """Resolve the best governance template directory for this workspace."""
    root = _template_root(templates_dir)
    if workspace_dir is not None and detect_project_type(workspace_dir) == "creative":
        creative_governance = root / "creative" / "governance"
        if creative_governance.is_dir():
            return creative_governance
    return root / "governance"


def detect_project_type(workspace_dir: Path) -> str:
    """Detect whether the project is primarily software or creative/design focused."""
    creative_score = _score_matches(workspace_dir, _creative_signals())
    software_score = _score_matches(workspace_dir, _software_signals())
    if creative_score > software_score:
        return "creative"
    return "software"


def _score_matches(workspace_dir: Path, signals: Iterable[Tuple[str, int]]) -> int:
    score = 0
    for relative_path, weight in signals:
        if _matches_signal(workspace_dir, relative_path):
            score += weight
    return score


def _matches_signal(workspace_dir: Path, relative_path: str) -> bool:
    if "*" in relative_path:
        return any(workspace_dir.glob(relative_path))
    return (workspace_dir / relative_path).exists()


def _creative_signals() -> Tuple[Tuple[str, int], ...]:
    return (
        ("project.godot", 5),
        ("*.godot", 4),
        ("game_design.md", 5),
        ("GAME_DESIGN.md", 5),
        ("GDD.md", 4),
        ("design_doc.md", 4),
        ("story_outline.md", 3),
        ("worldbuilding.md", 3),
        ("narrative", 2),
        ("design", 2),
        ("levels", 2),
        ("art_direction.md", 3),
        ("*.blend", 3),
        ("*.aseprite", 3),
        ("*.kra", 3),
    )


def _software_signals() -> Tuple[Tuple[str, int], ...]:
    return (
        ("pyproject.toml", 4),
        ("requirements.txt", 3),
        ("package.json", 4),
        ("Cargo.toml", 4),
        ("go.mod", 4),
        ("pom.xml", 4),
        ("build.gradle", 4),
        ("*.sln", 3),
        ("src", 2),
        ("tests", 2),
        (".github", 1),
    )


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
