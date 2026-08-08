# -*- mode: python ; coding: utf-8 -*-
#
# Added 08-Aug-2026 - PyInstaller build recipe for desktop_app.py (the
# PySide6 dashboard, committed 14-Jul but never packaged as a runnable
# .exe until now). This spec file is tracked in git; build/ and dist/
# (the actual ~100MB .exe output) are NOT - see .gitignore.
#
# To build:
#   pip install pyinstaller
#   pyinstaller TURION_Desktop.spec
#   -> dist/TURION_Desktop.exe
#
# Run the .exe from the project root (D:\TURION_AI_Trader) or copy it
# there first - desktop_app.py reads reports/paper_portfolio.json via
# a relative path, same convention as every other script in this repo.

a = Analysis(
    ['desktop_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name='TURION_Desktop',
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
