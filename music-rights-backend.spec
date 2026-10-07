# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
)


datas = []
binaries = []
hiddenimports = []


# ============================
# Modules locaux services
# ============================

hiddenimports += collect_submodules(
    "services"
)


# ============================
# Playwright
# ============================

pw_datas, pw_binaries, pw_hiddenimports = (
    collect_all("playwright")
)

datas += pw_datas
binaries += pw_binaries
hiddenimports += pw_hiddenimports


# ============================
# Demucs
# ============================

demucs_datas, demucs_binaries, demucs_hiddenimports = (
    collect_all("demucs")
)

datas += demucs_datas
binaries += demucs_binaries
hiddenimports += demucs_hiddenimports


# ============================
# Torch / Torchaudio
# ============================

torch_datas, torch_binaries, torch_hiddenimports = (
    collect_all("torch")
)

datas += torch_datas
binaries += torch_binaries
hiddenimports += torch_hiddenimports


ta_datas, ta_binaries, ta_hiddenimports = (
    collect_all("torchaudio")
)

datas += ta_datas
binaries += ta_binaries
hiddenimports += ta_hiddenimports


# ============================
# FFmpeg / FFprobe Windows
# ============================
#
# Le workflow GitHub créera :
#
# tools/
#   ffmpeg.exe
#   ffprobe.exe
#
# avant de lancer PyInstaller.
#

binaries += [
    (
        "tools/ffmpeg.exe",
        "tools",
    ),
    (
        "tools/ffprobe.exe",
        "tools",
    ),
]


# ============================
# Analyse principale
# ============================

a = Analysis(
    ["backend_api.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(
    a.pure
)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="music-rights-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="music-rights-backend",
)