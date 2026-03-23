# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['server_entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('../frontend/dist', 'frontend_dist'),  # React build — served to LAN browser clients
    ],
    hiddenimports=[
        # FastAPI / Starlette internals
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.loops.uvloop',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan.on',
        # SQLAlchemy dialects
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.sql.default_comparator',
        # Python-jose
        'jose',
        'jose.jwt',
        'jose.exceptions',
        # Pydantic
        'pydantic.deprecated.class_validators',
        'pydantic_settings',
        # Email validator
        'email_validator',
        # Multipart
        'multipart',
        # aiosqlite
        'aiosqlite',
        # bcrypt + cffi (native extensions — must be explicit for PyInstaller hooks to fire)
        'bcrypt',
        '_cffi_backend',
        'cryptography',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.primitives',
        # charset detection (fixes requests warning)
        'charset_normalizer',
        'charset_normalizer.md__mypyc',
        # openpyxl — APIS Excel import/export
        'openpyxl',
        'openpyxl.reader.excel',
        'openpyxl.reader.worksheet',
        'openpyxl.writer.excel',
        'openpyxl.writer.worksheet',
        'openpyxl.styles',
        'openpyxl.styles.stylesheet',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        'openpyxl.workbook',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._read_only',
        'openpyxl.worksheet.worksheet',
        'et_xmlfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
    ],
    noarchive=False,
    optimize=0,  # 0 = keep docstrings — pydantic v2 uses introspection that breaks with optimize=2
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='python-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
