# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop\\app.py'],
    pathex=['.', 'collector', 'export', 'adapters', 'desktop'],
    binaries=[],
    datas=[('collector', 'collector'), ('adapters', 'adapters'), ('config', 'config'), ('export', 'export'), ('templates', 'templates'), ('desktop\\views', 'desktop/views'), ('surveys', 'surveys')],
    hiddenimports=['customtkinter', 'smtplib', 'ssl', 'email', 'email.message', 'submission', 'diagnostics', 'adapters.openclaw_telemetry', 'adapters.codex_telemetry', 'adapters.plugin_loader'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='praxis-desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
