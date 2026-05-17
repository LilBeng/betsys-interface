block_cipher = None
name = "Betting System - Database"

a = Analysis(
    ['src/run_db.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'asyncpg.pgproto.pgproto',
        'qasync',
        'aiosqlite',
        'unicodedata'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    [],
    exclude_binaries=True,
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="resources/icons/icon.ico",
    contents_directory='resources',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=name,
)
