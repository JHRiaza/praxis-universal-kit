"""
PRAXIS Universal Kit — Custom Adapter Plugin Loader
====================================================
Auto-discovers adapter modules from ~/.praxis/adapters/*.py
Each adapter module should expose a class with:
  - name: str attribute
  - detect() -> bool
  - capture_session_context() -> dict
  - capture_session_in_range(start_time, end_time) -> dict or None (optional)

Adapters are loaded lazily and never crash the core collector.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_custom_adapters_dir() -> Path:
    """Return the custom adapters directory, creating it if needed."""
    d = Path.home() / ".praxis" / "adapters"
    d.mkdir(parents=True, exist_ok=True)
    return d


def discover_custom_adapters() -> List[Any]:
    """Discover and instantiate all custom adapters from ~/.praxis/adapters/.
    
    Returns list of instantiated adapter objects. Modules that fail to load
    are silently skipped.
    """
    adapters_dir = get_custom_adapters_dir()
    adapters: List[Any] = []
    
    if not adapters_dir.is_dir():
        return adapters
    
    for py_file in sorted(adapters_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                f"praxis_custom_adapter_{py_file.stem}",
                str(py_file),
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for adapter class — convention: first class with detect() method
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                    and hasattr(attr, "detect")
                    and hasattr(attr, "capture_session_context")):
                    instance = attr()
                    if hasattr(instance, "name"):
                        adapters.append(instance)
                    break
        except Exception:
            # Never crash on a bad custom adapter
            continue
    
    return adapters


def probe_all_adapters(workspace_path: Optional[Path] = None) -> Dict[str, Any]:
    """Probe all built-in and custom adapters. Returns {adapter_name: telemetry_dict}.
    
    Built-in adapters: openclaw, codex
    Custom adapters: discovered from ~/.praxis/adapters/
    """
    telemetry: Dict[str, Any] = {}
    
    # Built-in adapters
    try:
        from adapters.openclaw_telemetry import OpenClawAdapter
        adapter = OpenClawAdapter(workspace_path)
        if adapter.detect():
            telemetry[adapter.name] = adapter.capture_session_context()
    except Exception:
        pass
    
    try:
        from adapters.codex_telemetry import CodexAdapter
        adapter = CodexAdapter()
        if adapter.detect():
            telemetry[adapter.name] = adapter.capture_session_context()
    except Exception:
        pass
    
    # Custom adapters from ~/.praxis/adapters/
    for custom in discover_custom_adapters():
        try:
            if custom.detect():
                telemetry[custom.name] = custom.capture_session_context()
        except Exception:
            pass
    
    return telemetry


def get_custom_adapters_summary(telemetry: Dict[str, Any]) -> List[str]:
    """Build a list of adapter status strings for checkout display.
    Skips built-in adapters (handled separately).
    """
    built_in = {"openclaw", "codex"}
    parts = []
    for name, data in telemetry.items():
        if name in built_in:
            continue
        if data.get("detected"):
            parts.append(f"{name} ✓")
    return parts
