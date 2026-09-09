#!/usr/bin/env bash
# VoiceNook — Ein-Setup-Installation
# Erstellt eine venv im Projektordner, installiert alle Abhängigkeiten
# (VoxCPM2 + Higgs in-process) und ffmpeg.
set -euo pipefail

# Projekt-Verzeichnis (wo dieses Skript liegt)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Standard-venv im Projektordner, per VENV_DIR ueberschreibbar
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> VoiceNook Installation"
echo "    venv:  $VENV_DIR"

# venv anlegen
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Lege venv an ..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    echo "==> venv existiert bereits."
fi
source "$VENV_DIR/bin/activate"

echo "==> Aktualisiere pip ..."
pip install --upgrade pip

echo "==> Installiere VoiceNook (editable) ..."
pip install -e "$SCRIPT_DIR"

echo "==> Installiere zusätzliche Abhängigkeiten (Upload/Convert) ..."
pip install pydub python-multipart

echo "==> Prüfe ffmpeg (für MP3-Konvertierung) ..."
if command -v ffmpeg >/dev/null 2>&1; then
    echo "    ffmpeg ist vorhanden."
else
    echo "    ffmpeg fehlt — installiere via Homebrew (benötigt Passwort):"
    brew install ffmpeg
fi

echo ""
echo "==> Fertig. Starte mit:"
echo "    ./run.sh"
echo "    Danach im Browser: http://127.0.0.1:8080"