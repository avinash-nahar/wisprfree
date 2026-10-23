# PyInstaller spec starter. Validate native imports/resources on Apple Silicon.
from pathlib import Path
ROOT = Path.cwd()
block_cipher = None
datas = []
for candidate in (ROOT / "siri_avi.json", ROOT / "hud_siri.html", ROOT / "assets"):
    if candidate.is_file():
        datas.append((str(candidate), "assets"))
    elif candidate.is_dir():
        datas.append((str(candidate), "assets"))
a = Analysis([str(ROOT / "wispr_avi_hud.py")], pathex=[str(ROOT)], binaries=[], datas=datas,
    hiddenimports=["Quartz", "AppKit"], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter", "pytest"], noarchive=False, optimize=1)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="WisprFree", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    target_arch="arm64", codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="WisprFree")
app = BUNDLE(coll, name="WisprFree.app", icon=None, bundle_identifier="com.adbureau.wisprfree",
    info_plist={"CFBundleName":"WisprFree","CFBundleDisplayName":"WisprFree",
    "CFBundleShortVersionString":"0.1.0","CFBundleVersion":"1","LSMinimumSystemVersion":"13.0",
    "NSMicrophoneUsageDescription":"WisprFree uses your microphone only when you activate push-to-talk to transcribe speech."})
