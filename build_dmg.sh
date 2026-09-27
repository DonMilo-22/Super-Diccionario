#!/bin/bash
set -e

APP_PATH="dist/Word Helper.app"
OUT_DIR="installer"
DMG_PATH="$OUT_DIR/Word-Helper-macOS.dmg"

if [ ! -d "$APP_PATH" ]; then
  echo "No se encontró $APP_PATH"
  exit 1
fi

mkdir -p "$OUT_DIR"
rm -f "$DMG_PATH"

STAGE_DIR="$(mktemp -d)"
cp -R "$APP_PATH" "$STAGE_DIR/Word Helper.app"
ln -s /Applications "$STAGE_DIR/Applications"

hdiutil create   -volname "Word Helper"   -srcfolder "$STAGE_DIR"   -ov   -format UDZO   "$DMG_PATH"

rm -rf "$STAGE_DIR"
