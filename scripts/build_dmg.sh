#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.1.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "Build this DMG on an Apple Silicon Mac or arm64 macOS runner." >&2
  exit 2
fi
python3 -m pip install -r requirements-dev.txt
python3 -m PyInstaller packaging/wisprfree.spec --clean --noconfirm
APP="dist/WisprFree.app"
[[ -d "$APP" ]] || { echo "Expected app bundle not found: $APP" >&2; exit 3; }
STAGE="dist/dmg-stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
DMG="dist/WisprFree-${VERSION}-macos-arm64.dmg"
rm -f "$DMG"
hdiutil create -volname "WisprFree ${VERSION}" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
shasum -a 256 "$DMG" > "${DMG}.sha256"
echo "Built $DMG. Signing/notarization are not performed by this script."
