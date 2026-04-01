# -*- mode: python ; coding: utf-8 -*-
import glob, os, subprocess, sys

# Bundle sqlcipher3's native shared libraries so DB encryption works on the
# target machine without libsqlcipher installed system-wide.
#
# Two cases:
#  1. sqlcipher3-binary  — ships its own OpenSSL in sqlcipher3_binary.libs/
#  2. sqlcipher3 (system-linked) — libsqlcipher.so.0 must be found via ldd
#     and bundled explicitly; PyInstaller excludes it as an "unknown" lib.
_sqlcipher_bins = []
try:
    import sqlcipher3 as _sc
    _sc_ext = glob.glob(
        os.path.join(os.path.dirname(_sc.__file__), '_sqlite3*.so')
    )

    # Case 1: sqlcipher3-binary bundled libs
    _libs_dir = os.path.normpath(
        os.path.join(os.path.dirname(_sc.__file__), '..', 'sqlcipher3_binary.libs')
    )
    for _lib in glob.glob(os.path.join(_libs_dir, '*.so*')):
        _sqlcipher_bins.append((_lib, 'sqlcipher3_binary.libs'))

    # Case 2: system-linked — walk ldd output to find libsqlcipher.so
    if not _sqlcipher_bins and _sc_ext:
        try:
            _ldd = subprocess.check_output(['ldd', _sc_ext[0]], text=True)
            for _line in _ldd.splitlines():
                if 'libsqlcipher' in _line and '=>' in _line:
                    _path = _line.split('=>')[1].strip().split()[0]
                    if os.path.exists(_path):
                        _sqlcipher_bins.append((_path, '.'))
        except Exception:
            pass

    if _sqlcipher_bins:
        print(f'[spec] Bundling sqlcipher3 native libs: {_sqlcipher_bins}')
    else:
        print('[spec] WARNING: sqlcipher3 found but no native libs detected — encryption may fail at runtime')
except ImportError:
    print('[spec] sqlcipher3 not installed — DB encryption will be disabled in this build')

a = Analysis(
    ['server_entry.py'],
    pathex=[],
    binaries=_sqlcipher_bins,
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
        # sqlcipher3 — AES-256 SQLite encryption (must be explicit; loaded via importlib)
        'sqlcipher3',
        'sqlcipher3.dbapi2',
        # bcrypt + cffi (native extensions — must be explicit for PyInstaller hooks to fire)
        'bcrypt',
        '_cffi_backend',
        'cryptography',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.primitives',
        # WeasyPrint + PDF rendering dependencies
        # These are loaded lazily inside the /print endpoint but PyInstaller
        # must bundle them — PIL was previously in 'excludes' which broke PDF.
        'weasyprint',
        'weasyprint.text.fonts',
        'weasyprint.text.ffi',
        'cssselect2',
        'tinycss2',
        'tinycss2.color3',
        'pydyf',
        'fontTools',
        'fontTools.ttLib',
        'PIL',
        'PIL.Image',
        'PIL.ImageFile',
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
        # pyodbc — Windows MDB/Access file import via ODBC driver
        'pyodbc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        # NOTE: do NOT exclude PIL/Pillow — WeasyPrint uses it for image rendering in PDFs
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
    disable_windowed_traceback=True,  # crash → process exits (code 1) instead of showing a dialog
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
