# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（唯一入口，由 build.bat 调用）。

注意：
  * win32com / pythoncom / pywintypes 在代码中是**惰性导入**，
    PyInstaller 的静态分析看不到，必须显式声明为 hiddenimports。
  * UPX 压缩对 PySide6 可执行文件容易被国产杀毒软件误报，
    因此显式关闭（upx=False）。
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    'win32com',
    'win32com.client',
    'pythoncom',
    'pywintypes',
    'PySide6.QtNetwork',
]
hiddenimports += collect_submodules('win32com')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore',
        'PySide6.QtCharts',
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'tkinter',
        'unittest',
    ],
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
    name='YG-DATA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources/app_icon.ico'],
)
