#!/usr/bin/env bash
# VoiceNook — startet VoxCPM2-Server (WebUI, Port 8005) und Higgs-Server (Port 8006)
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

# VoxCPM2-Server (WebUI) im Hintergrund starten
echo "==> Starte VoxCPM2-Server (WebUI) auf http://127.0.0.1:8005 ..."
voxcpmane2-server --host 0.0.0.0 --port 8005 \
    --lm-mode single-length --lm-prefill-chunk-size 64 &
VOX_PID=$!

# Higgs-Server starten (lädt lazy, Port 8006)
echo "==> Starte Higgs-Server auf http://127.0.0.1:8006 ..."
python -u higgs_server.py --port 8006 &
HIGGS_PID=$!

echo ""
echo "VoiceNook läuft:"
echo "  WebUI:  http://127.0.0.1:8005"
echo "  Higgs:  http://127.0.0.1:8006"
echo "  (Strg+C beendet beide)"

cleanup() {
    echo ""
    echo "==> Beende Server ..."
    kill "$VOX_PID" "$HIGGS_PID" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Im Vordergrund laufen lassen
wait