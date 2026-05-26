# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置文件"""

import os

block_cipher = None

# 项目根目录
ROOT_DIR = os.path.abspath('.')

# 需要打包的数据文件（源路径, 目标路径）
datas = [
    # 程序图标
    ('src/ui/应用图标.ico', 'ui'),
    ('src/ui/应用图标.png', 'ui'),  # gui.py 中加载窗口图标用
    # COSMIC 模板文件（目录页"打开模板"按钮需要）
    ('docs/test_data/模板/cosmic-自动填充-模板.xlsx', 'docs/test_data/模板'),
]

# 隐藏导入（PyInstaller 可能无法自动检测的模块）
hiddenimports = [
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'openpyxl',
    'pandas',
    'aiohttp',
    'requests',
    'PIL',
    'workbench',
]

a = Analysis(
    ['src/gui.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='COSMIC-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/ui/应用图标.ico',  # exe 图标（ICO 格式）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='COSMIC-GUI',
)
