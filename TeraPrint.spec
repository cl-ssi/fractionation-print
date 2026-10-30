# -*- mode: python ; coding: utf-8 -*-

hiddenimports = [
	'sys',
	'json',
    'win32print',
	'socket',
	'rut_chile',
	'logging',
	'traceback',
    'flask',
	'flask_cors',
	'subprocess',
	'threading',
	're',
    'jinja2',
    'werkzeug',
    'pkg_resources.py2_warn',
	'markupsafe',
	'itsdangerous',
	'click',
	'blinker'
	'colorama'
]

a = Analysis(
    ['tu_script.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
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
    name='TeraPrint',
	icon='print.ico',
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
)
