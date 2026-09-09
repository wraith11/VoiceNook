#!/usr/bin/env bash
# VoiceNook — startet den Server (WebUI, Port 8080).
# Beide Modelle (VoxCPM2 + Higgs) laden on-demand und entladen sich nach
# Inaktivitaet selbst, damit der Server im Idle ultra-light ist.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Standard-venv im Projektordner, per VENV_DIR ueberschreibbar
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Fehler: venv nicht gefunden unter $VENV_DIR"
    echo "Führe zuerst ./install.sh aus."
    exit 1
fi
source "$VENV_DIR/bin/activate"

echo "==> Starte VoiceNook auf http://127.0.0.1:8080 ..."
echo "    VoxCPM2 + Higgs laden on-demand (Idle-Unload nach 5 min)."
exec voicenook-server --host 0.0.0.0 --port 8080 \
    --lm-mode single-length --lm-prefill-chunk-size 64 \
    "$@"