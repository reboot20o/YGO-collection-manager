# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_data = [
            ('assets\\initialize_database.sql', 'assets'),
            ('assets\\style.qss', 'assets'),
            ('assets\\images', 'assets/images')
            ]


a = Analysis(
    ['src\\qt\\qt.py'],
    pathex=['src'],
    binaries=[],
    datas=added_data,
    hiddenimports=[],
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
    name='YGOCollectionManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/yugioh.ico',
)