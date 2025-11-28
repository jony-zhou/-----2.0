# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# 將專案根目錄加入匯入路徑
PROJECT_ROOT = Path(SPEC).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.version import VERSION  # noqa: E402  # 在插入路徑後匯入

block_cipher = None

assets_path = PROJECT_ROOT / "assets"
assets_data = []
if assets_path.exists():
    assets_data.append((str(assets_path), "assets"))

hidden_imports = ["customtkinter", "PIL._tkinter_finder"] + collect_submodules("PIL.ImageTk")

analysis = Analysis(
    ["app.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=assets_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    analysis.pure,
    analysis.zipped_data,
    cipher=block_cipher,
)

icon_file = assets_path / "icon.ico"
icon_path = str(icon_file) if icon_file.exists() else None

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=f"overtime-assistant-{VERSION}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f"overtime-assistant-{VERSION}",
)
