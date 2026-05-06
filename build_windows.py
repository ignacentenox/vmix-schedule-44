#!/usr/bin/env python3
"""
Build script for PyInstaller to crear .exe portátil
Uso: pyinstaller build_windows.spec
"""

import PyInstaller.config
import os

# Configuración
spec_name = 'vMix Schedule 44'
main_script = 'main.py'
output_dir = 'dist'

# Spec file content
spec_content = """# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ] + collect_submodules('PySide6'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vMix_Schedule_44',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico' if os.path.exists('app.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vMix_Schedule_44'
)
"""

with open('build_windows.spec', 'w') as f:
    f.write(spec_content)

print("✅ Archivo build_windows.spec creado")
print("\nPasos para crear el .exe:")
print("1. Instala PyInstaller: pip install pyinstaller")
print("2. Ejecuta: pyinstaller build_windows.spec")
print("3. El .exe estará en: dist/vMix_Schedule_44/vMix_Schedule_44.exe")
