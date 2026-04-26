"""
PRAXIS Universal Kit — Governance Protocol Layer
=================================================
Injects/removes governance methodology into AI platform config files.
When PRAXIS is ON (Phase B), writes governance rules into CLAUDE.md,
.cursorrules, .github/copilot-instructions.md, etc.
When OFF (Phase A), removes them cleanly.

Every platform can respond to "PRAXIS?" with ON/OFF status.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Protocol Manifest
# ---------------------------------------------------------------------------

PROTOCOL_VERSION = "1.0"
PRAXIS_MARKER_START = "<!-- PRAXIS_PROTOCOL_START -->"
PRAXIS_MARKER_END = "<!-- PRAXIS_PROTOCOL_END -->"
PRAXIS_STATUS_LINE = "PRAXIS: {status} | Phase {phase} | {rules} rules active | v{version}"

# The core governance rules injected into every platform
GOVERNANCE_RULES = [
    {
        "id": "G01",
        "title": "Decision Logging",
        "rule": "Log every architectural, technical, or scope decision with rationale. Format: [DECISION] <what> because <why>",
        "checkpoint": False,
    },
    {
        "id": "G02",
        "title": "Human Review Gate",
        "rule": "Before finalizing any generated code, document, or artifact — pause and ask: 'Does this need human review?' If yes, flag it.",
        "checkpoint": True,
    },
    {
        "id": "G03",
        "title": "Confidence Rating",
        "rule": "Rate your confidence (1-5) on every non-trivial output. State uncertainties explicitly.",
        "checkpoint": False,
    },
    {
        "id": "G04",
        "title": "Intervention Escalation",
        "rule": "When you detect a governance violation (skipped review, undocumented decision, scope creep), flag it immediately with [GOVERNANCE_ALERT]",
        "checkpoint": False,
    },
    {
        "id": "G05",
        "title": "Sprint Boundary",
        "rule": "Mark sprint boundaries explicitly. At sprint end: summarize what was done, what was deferred, and any open decisions.",
        "checkpoint": True,
    },
]


def _build_manifest_text(phase: str = "B", rules: Optional[List[Dict[str, Any]]] = None) -> str:
    """Build the governance manifest text block."""
    active_rules = rules or GOVERNANCE_RULES
    lines = [
        PRAXIS_MARKER_START,
        f"# PRAXIS Governance Protocol v{PROTOCOL_VERSION}",
        f"# Phase: {phase} | Rules: {len(active_rules)} | Auto-injected by PRAXIS Kit",
        "",
        "## Status Query",
        "When the user asks 'PRAXIS?', 'praxis status', or 'is praxis on', respond with:",
        f'  "{PRAXIS_STATUS_LINE.format(status="ON", phase=phase, rules=len(active_rules), version=PROTOCOL_VERSION)}"',
        "",
        "## Governance Rules",
    ]
    for r in active_rules:
        checkpoint = " [CHECKPOINT]" if r.get("checkpoint") else ""
        lines.append(f"- **{r['id']}: {r['title']}**{checkpoint}")
        lines.append(f"  {r['rule']}")
    lines.extend([
        "",
        "## What 'PRAXIS ON' Means",
        "- You MUST follow the rules above during every interaction",
        "- You MUST log governance events when rules are triggered",
        "- You MUST respond to 'PRAXIS?' status queries",
        "- You MAY suggest improvements to governance rules",
        "",
        PRAXIS_MARKER_END,
    ])
    return "\n".join(lines)


def _build_claude_md(phase: str) -> str:
    """Build manifest formatted for CLAUDE.md (Claude Cowork)."""
    rules = GOVERNANCE_RULES
    lines = [
        PRAXIS_MARKER_START,
        f"## PRAXIS Governance Protocol v{PROTOCOL_VERSION}",
        f"Phase: {phase} | {len(rules)} rules active",
        "",
        "### Status",
        f"Respond to 'PRAXIS?', 'praxis status', 'is praxis on' with:",
        f'`{PRAXIS_STATUS_LINE.format(status="ON", phase=phase, rules=len(rules), version=PROTOCOL_VERSION)}`',
        "",
        "### Rules",
    ]
    for r in rules:
        checkpoint = " **[CHECKPOINT]**" if r.get("checkpoint") else ""
        lines.append(f"{r['id']}. **{r['title']}**{checkpoint}: {r['rule']}")
    lines.extend([
        "",
        "### Obligations",
        "- Follow rules above in every interaction",
        "- Log governance events when triggered",
        "- Respond to PRAXIS? queries",
        "- Suggest rule improvements when appropriate",
        "",
        PRAXIS_MARKER_END,
    ])
    return "\n".join(lines)


def _build_cursorrules(phase: str) -> str:
    """Build manifest formatted for .cursorrules (Cursor)."""
    return _build_manifest_text(phase)


def _build_copilot_instructions(phase: str) -> str:
    """Build manifest formatted for .github/copilot-instructions.md."""
    return _build_manifest_text(phase)


def _build_windsurfrules(phase: str) -> str:
    """Build manifest formatted for .windsurfrules (Windsurf/Codeium)."""
    return _build_manifest_text(phase)


def _build_claw_md(phase: str) -> str:
    """Build manifest formatted for CLAW.md or SOUL.md injection (OpenClaw)."""
    return _build_manifest_text(phase)


# ---------------------------------------------------------------------------
# Platform Adapters
# ---------------------------------------------------------------------------

class PlatformAdapter:
    """Base adapter for injecting/removing PRAXIS protocol from a platform config."""
    
    name: str = "unknown"
    filename: str = ""
    description: str = ""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def get_path(self) -> Path:
        return self.project_dir / self.filename
    
    def build_content(self, phase: str) -> str:
        raise NotImplementedError
    
    def is_injected(self) -> bool:
        path = self.get_path()
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        return PRAXIS_MARKER_START in content
    
    def inject(self, phase: str) -> bool:
        """Inject PRAXIS protocol. Returns True if successful."""
        path = self.get_path()
        manifest = self.build_content(phase)
        
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if PRAXIS_MARKER_START in content:
                # Already injected — update
                content = _remove_manifest(content)
            path.write_text(content.rstrip() + "\n\n" + manifest + "\n", encoding="utf-8")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(manifest + "\n", encoding="utf-8")
        return True
    
    def remove(self) -> bool:
        """Remove PRAXIS protocol. Returns True if successful."""
        path = self.get_path()
        if not path.is_file():
            return True
        content = path.read_text(encoding="utf-8")
        if PRAXIS_MARKER_START not in content:
            return True
        content = _remove_manifest(content)
        # Clean up empty file
        stripped = content.strip()
        if stripped:
            path.write_text(stripped + "\n", encoding="utf-8")
        else:
            path.unlink()
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get injection status for this platform."""
        return {
            "platform": self.name,
            "filename": self.filename,
            "path": str(self.get_path()),
            "injected": self.is_injected(),
            "file_exists": self.get_path().is_file(),
        }


class ClaudeAdapter(PlatformAdapter):
    name = "Claude Cowork"
    filename = "CLAUDE.md"
    description = "Claude Cowork / Claude Code project instructions"
    
    def build_content(self, phase: str) -> str:
        return _build_claude_md(phase)


class CursorAdapter(PlatformAdapter):
    name = "Cursor"
    filename = ".cursorrules"
    description = "Cursor AI rules file"
    
    def build_content(self, phase: str) -> str:
        return _build_cursorrules(phase)


class CopilotAdapter(PlatformAdapter):
    name = "GitHub Copilot"
    filename = ".github/copilot-instructions.md"
    description = "GitHub Copilot chat instructions"
    
    def build_content(self, phase: str) -> str:
        return _build_copilot_instructions(phase)


class WindsurfAdapter(PlatformAdapter):
    name = "Windsurf"
    filename = ".windsurfrules"
    description = "Windsurf/Codeium AI rules"
    
    def build_content(self, phase: str) -> str:
        return _build_windsurfrules(phase)


class CodexAdapter(PlatformAdapter):
    name = "OpenAI Codex"
    filename = "AGENTS.md"
    description = "Codex project instructions"
    
    def build_content(self, phase: str) -> str:
        return _build_manifest_text(phase)


class OpenClawAdapter(PlatformAdapter):
    """OpenClaw adapter — writes to ~/.openclaw/workspace/PRAXIS.md.
    
    OpenClaw doesn't use project-level config files. Instead it reads
    workspace governance files (SOUL.md, AGENTS.md). PRAXIS injects into
    a dedicated PRAXIS.md in the OpenClaw workspace, which gets loaded
    as project context automatically.
    """
    name = "OpenClaw"
    filename = "PRAXIS.md"
    description = "OpenClaw workspace governance (PRAXIS.md)"
    
    def __init__(self, project_dir: Path):
        # Override: OpenClaw lives in ~/.openclaw/workspace/, not project dir
        super().__init__(project_dir)
        self._openclaw_dir = Path.home() / ".openclaw" / "workspace"
    
    def get_path(self) -> Path:
        return self._openclaw_dir / self.filename
    
    def build_content(self, phase: str) -> str:
        return _build_manifest_text(phase)


# Registry of all supported platforms
PLATFORM_ADAPTERS: List[type] = [
    ClaudeAdapter,
    CursorAdapter,
    CopilotAdapter,
    WindsurfAdapter,
    CodexAdapter,
    OpenClawAdapter,
]


def get_adapters_for_project(project_dir: Path) -> List[PlatformAdapter]:
    """Get all platform adapters for a given project directory."""
    return [cls(project_dir) for cls in PLATFORM_ADAPTERS]


def detect_platforms(project_dir: Path) -> List[str]:
    """Detect which AI platforms are active in a project (have config files)."""
    detected = []
    for adapter_cls in PLATFORM_ADAPTERS:
        adapter = adapter_cls(project_dir)
        if adapter.get_path().is_file():
            detected.append(adapter.name)
    return detected


# ---------------------------------------------------------------------------
# Protocol Manager
# ---------------------------------------------------------------------------

class ProtocolManager:
    """Manages PRAXIS protocol injection across all platforms for a project."""
    
    def __init__(self, praxis_dir: Path):
        self._praxis_dir = praxis_dir
        self._project_dir = praxis_dir.parent
        self._adapters = get_adapters_for_project(self._project_dir)
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get injection status for all platforms."""
        return [a.get_status() for a in self._adapters]
    
    def get_injected_platforms(self) -> List[str]:
        """Get names of platforms where PRAXIS is currently injected."""
        return [a.name for a in self._adapters if a.is_injected()]
    
    def get_detected_platforms(self) -> List[str]:
        """Get names of platforms that have existing config files."""
        return [a.name for a in self._adapters if a.get_path().is_file()]
    
    def inject_all(self, phase: str) -> Dict[str, bool]:
        """Inject PRAXIS protocol into all platforms. Returns {name: success}."""
        results = {}
        for adapter in self._adapters:
            try:
                results[adapter.name] = adapter.inject(phase)
            except Exception:
                results[adapter.name] = False
        return results
    
    def remove_all(self) -> Dict[str, bool]:
        """Remove PRAXIS protocol from all platforms. Returns {name: success}."""
        results = {}
        for adapter in self._adapters:
            try:
                results[adapter.name] = adapter.remove()
            except Exception:
                results[adapter.name] = False
        return results
    
    def inject_platform(self, platform_name: str, phase: str) -> bool:
        """Inject into a specific platform."""
        for adapter in self._adapters:
            if adapter.name == platform_name:
                return adapter.inject(phase)
        return False
    
    def remove_platform(self, platform_name: str) -> bool:
        """Remove from a specific platform."""
        for adapter in self._adapters:
            if adapter.name == platform_name:
                return adapter.remove()
        return False
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary."""
        injected = self.get_injected_platforms()
        phase = "B" if injected else "A"
        count = len(injected)
        total = len(GOVERNANCE_RULES)
        return PRAXIS_STATUS_LINE.format(
            status="ON" if injected else "OFF",
            phase=phase,
            rules=total,
            version=PROTOCOL_VERSION,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _remove_manifest(content: str) -> str:
    """Remove the PRAXIS manifest block from content."""
    start_idx = content.find(PRAXIS_MARKER_START)
    end_idx = content.find(PRAXIS_MARKER_END)
    if start_idx == -1 or end_idx == -1:
        return content
    # Remove from start marker to end marker (inclusive)
    end_idx = end_idx + len(PRAXIS_MARKER_END)
    removed = content[:start_idx] + content[end_idx:]
    # Clean up excessive blank lines
    while "\n\n\n" in removed:
        removed = removed.replace("\n\n\n", "\n\n")
    return removed
