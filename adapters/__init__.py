"""
PRAXIS Universal Kit — Adapters Package
========================================
Platform-specific adapters for PRAXIS governance injection.

Each adapter is a class that inherits from PraxisAdapter (base.py) and
implements:
    detect()                                          -> bool
    inject_governance(templates_dir, workspace_dir)   -> list[str]
    remove_governance(workspace_dir)                  -> list[str]
    get_info()                                        -> dict

Tier map:
  Tier 1 — Deep:    OpenClaw (cron, heartbeat, memory)
  Tier 2 — Medium:  Claude Cowork, Codex, Cursor, Windsurf
  Tier 3 — Light:   Copilot, Aider, Continue.dev, Cline, Roo Code
  Tier 4 — Generic: Any AI tool (plain markdown)
"""

from .base import PraxisAdapter

from .openclaw      import OpenClawAdapter
from .claude_cowork import ClaudeCoworkAdapter
from .codex         import CodexAdapter
from .cursor        import CursorAdapter
from .windsurf      import WindsurfAdapter
from .copilot       import CopilotAdapter
from .aider         import AiderAdapter
from .continue_dev  import ContinueDevAdapter
from .cline         import ClineAdapter
from .roo_code      import RooCodeAdapter
from .generic       import GenericAdapter

# Ordered by detection priority (highest tier first, generic last)
ALL_ADAPTERS: list = [
    OpenClawAdapter,
    ClaudeCoworkAdapter,
    CodexAdapter,
    CursorAdapter,
    WindsurfAdapter,
    CopilotAdapter,
    AiderAdapter,
    ContinueDevAdapter,
    ClineAdapter,
    RooCodeAdapter,
    GenericAdapter,
]

# Map platform_id → adapter class for O(1) lookup
ADAPTER_MAP: dict = {cls.PLATFORM_ID: cls for cls in ALL_ADAPTERS}

__all__ = [
    "PraxisAdapter",
    "OpenClawAdapter",
    "ClaudeCoworkAdapter",
    "CodexAdapter",
    "CursorAdapter",
    "WindsurfAdapter",
    "CopilotAdapter",
    "AiderAdapter",
    "ContinueDevAdapter",
    "ClineAdapter",
    "RooCodeAdapter",
    "GenericAdapter",
    "ALL_ADAPTERS",
    "ADAPTER_MAP",
]
