#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python -m PyInstaller --noconfirm --windowed --name Spec-Graph \
  --osx-bundle-identifier org.specgraph.desktop \
  --paths . --collect-data spec_graph \
  --hidden-import webview.platforms.cocoa \
  scripts/desktop_entry.py
