#!/usr/bin/env bash
# VoiceNook — startet den VoxCPM2-Server (WebUI, Port 8005).
# Der Higgs-Server wird NICHT automatisch gestartet — er läuft on-demand
# (per Klick auf den Higgs-Status im Higgs-Tab) und stoppt sich nach
# Inaktivität selbst. So bleiben Ressourcen geschont.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${VENV_DIR:-$HOME/Persona/voicenook-venv}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Fehler: venv nicht gefunden unter $VENV_DIR"
    echo "Führe zuerst ./install.sh aus."
    exit 1
fi
source "$VENV_DIR/bin/activate"

echo "==> Starte VoxCPM2-Server (WebUI) auf http://127.0.0.1:8005 ..."
echo "    Higgs startet on-demand aus der WebUI."
exec voicenook-server --host 0.0.0.0 --port 8005 \
    --lm-mode single-length --lm-prefill-chunk-size 64 \
    "$@"