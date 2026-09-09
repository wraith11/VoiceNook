#!/usr/bin/env bash
# VoiceNook — Ein-Setup-Installation
# Erstellt eine venv, installiert alle Abhängigkeiten (VoxCPM2 + Higgs) und ffmpeg.
set -euo pipefail

# Projekt-Verzeichnis (wo dieses Skript liegt)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Konfigurierbare Ziele
VENV_DIR="${VENV_DIR:-$HOME/Persona/voicenook-venv}"
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

echo "==> Installiere VoiceNook (VoxCPM2-Runtime, editable) ..."
pip install -e "$SCRIPT_DIR"

echo "==> Installiere zusätzliche Abhängigkeiten (Upload/Convert, Higgs) ..."
pip install pydub python-multipart mlx-audio

echo "==> Prüfe ffmpeg (für MP3-Konvertierung) ..."
if command -v ffmpeg >/dev/null 2>&1; then
    echo "    ffmpeg ist vorhanden."
else
    echo "    ffmpeg fehlt — installiere via Homebrew (benötigt Passwort):"
    brew install ffmpeg
fi

echo ""
echo "==> Fertig. Starte beide Server mit:"
echo "    ./run.sh"
echo "    Danach im Browser: http://127.0.0.1:8005"