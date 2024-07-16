# webdav.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['webdaw.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates/*.html', 'templates'),  # Включаем все HTML шаблоны
        ('wsgidav/dir_browser/htdocs/*', 'wsgidav/dir_browser/htdocs'),  # Включаем файлы из htdocs
    ],
    hiddenimports=[
        'lxml', 'defusedxml.ElementTree'  # Добавляем скрытые зависимости
    ],
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
    [],
    exclude_binaries=True,
    name='webdaw',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='test'
)
