#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="LANCER1911 PDF Workshop"
VOL_NAME="LANCER1911 PDF Workshop"
DMG_NAME="LANCER1911-PDF-Workshop-macOS.dmg"
APP_PATH="dist/${APP_NAME}.app"
DMG_ROOT="dist/dmg-root"

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found. DMG packaging must be run on macOS."
  exit 1
fi

if [ ! -d "$APP_PATH" ]; then
  echo "==> ${APP_PATH} not found. Building .app first..."
  chmod +x build_macos_app.sh
  ./build_macos_app.sh
fi

echo "==> Preparing DMG staging folder"
rm -rf "$DMG_ROOT"
mkdir -p "$DMG_ROOT"
ditto "$APP_PATH" "$DMG_ROOT/${APP_NAME}.app"
ln -s /Applications "$DMG_ROOT/Applications"

echo "==> Creating DMG"
rm -f "dist/${DMG_NAME}"
hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "dist/${DMG_NAME}"

rm -rf "$DMG_ROOT"

echo "Done: dist/${DMG_NAME}"
echo "Tip: This DMG is unsigned/not notarized unless you separately codesign and notarize the app."
