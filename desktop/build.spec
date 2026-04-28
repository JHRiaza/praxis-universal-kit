# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for PRAXIS Kit Desktop."""

import sys
from pathlib import Path

# Resolve paths relative to this spec file
spec_dir = Path(SPECPATH)
kit_root = spec_dir.parent

block_cipher = None

a = Analysis(
    [str(kit_root / "desktop" / "app.py")],
    pathex=[
        str(kit_root),
        str(kit_root / "collector"),
        str(kit_root / "export"),
        str(kit_root / "adapters"),
        str(kit_root / "desktop"),
    ],
    binaries=[],
    datas=[
        # Bundle collector, config, export, templates so the app can find them
        (str(kit_root / "collector"), "collector"),
        (str(kit_root / "adapters"), "adapters"),
        (str(kit_root / "config"), "config"),
        (str(kit_root / "export"), "export"),
        (str(kit_root / "templates"), "templates"),
        # Bundle the desktop package itself (viewmodel, views/)
        (str(kit_root / "desktop" / "viewmodel.py"), "desktop"),
        (str(kit_root / "desktop" / "__init__.py"), "desktop"),
        (str(kit_root / "desktop" / "views"), "desktop/views"),
        # Bundle the surveys directory for PRAXIS-Q metadata
        (str(kit_root / "surveys"), "surveys"),
    ],
    hiddenimports=[
        # --- Third-party ---
        "customtkinter",

        # --- Stdlib modules used by collector, adapters, export, desktop ---
        "uuid",
        "hashlib",
        "json",
        "os",
        "platform",
        "re",
        "subprocess",
        "argparse",
        "textwrap",
        "abc",
        "shutil",
        "zipfile",
        "socket",
        "socketserver",
        "http",
        "http.server",
        "threading",
        "webbrowser",
        "urllib",
        "urllib.parse",
        "datetime",
        "pathlib",
        "typing",
        "collections",
        "copy",
        "io",
        "enum",
        "functools",
        "itertools",
        "contextlib",
        "importlib",
        "stat",
        "tempfile",
        "traceback",
        "statistics",
        "math",
        "csv",
        "dataclasses",
        "smtplib",
        "ssl",
        "email",
        "email.message",

        # --- Kit modules (imported via sys.path at runtime) ---
        "praxis_collector",
        "praxis_cli",
        "submit",
        "submission",
        "anonymize",
        "diagnostics",
        "adapters",
        "adapters.base",
        "adapters.openclaw",
        "adapters.openclaw_telemetry",
        "adapters.claude_cowork",
        "adapters.codex",
        "adapters.codex_telemetry",
        "adapters.cowork_telemetry",
        "adapters.cursor",
        "adapters.windsurf",
        "adapters.copilot",
        "adapters.aider",
        "adapters.continue_dev",
        "adapters.cline",
        "adapters.roo_code",
        "adapters.generic",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="praxis-desktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI mode — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: add icon
)
