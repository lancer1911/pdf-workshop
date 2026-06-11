#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="LANCER1911 PDF Workshop"
ICON_FILE="assets/app.icns"

echo "==> Creating/using virtual environment"
python3 -m venv venv
./venv/bin/python -m pip install -U pip setuptools wheel
./venv/bin/python -m pip install -U -r requirements.txt pyinstaller

if [ ! -f "$ICON_FILE" ]; then
  echo "Missing icon: $ICON_FILE"
  exit 1
fi

echo "==> Cleaning old build files"
rm -rf build dist "${APP_NAME}.spec"

echo "==> Building macOS .app"
./venv/bin/pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --icon "$ICON_FILE" \
  --add-data "web:web" \
  --add-data "assets:assets" \
  --collect-submodules webview \
  --hidden-import fitz \
  --hidden-import pymupdf \
  --hidden-import proxy_tools \
  app.py

echo "==> Creating zip"
rm -f "dist/${APP_NAME}-macOS.zip"
ditto -c -k --sequesterRsrc --keepParent "dist/${APP_NAME}.app" "dist/${APP_NAME}-macOS.zip"

echo "Done: dist/${APP_NAME}.app"
echo "Zip : dist/${APP_NAME}-macOS.zip"


echo "DMG : run ./build_macos_dmg.sh to create dist/LANCER1911-PDF-Workshop-macOS.dmg"
