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

echo "==> VoiceNook Installation"
echo "    venv:  $VENV_DIR"

# --- Passende Python-Version finden (3.10 - 3.12) ---
# VoiceNook braucht Python <3.13 (CoreML/mlx). Falls PYTHON_BIN gesetzt ist,
# wird dieser verwendet; sonst wird automatisch die beste verfuegbare Version gewaehlt.
find_python() {
    # 1) Explizit gesetzte Version (z.B. PYTHON_BIN=python3.12) zuerst
    if [ -n "${PYTHON_BIN:-}" ]; then
        command -v "$PYTHON_BIN" >/dev/null 2>&1 && { echo "$PYTHON_BIN"; return; }
    fi
    # 2) Bekannte Versionen durchprobieren
    for cand in python3.12 python3.11 python3.10; do
        if command -v "$cand" >/dev/null 2>&1; then
            echo "$cand"
            return
        fi
    done
    # 3) Homebrew-Pfad
    if command -v python3 >/dev/null 2>&1; then
        # prüfen ob system-python3 < 3.13 ist
        ver="$(python3 -c 'import sys; print(sys.version_info[:2])' 2>/dev/null || echo '')"
        case "$ver" in
            "(3, 10)"|"(3, 11)"|"(3, 12)")
                echo "python3"
                return
                ;;
        esac
    fi
    echo ""
}

PY="$(find_python)"

if [ -z "$PY" ]; then
    echo ""
    echo "FEHLER: Keine passende Python-Version gefunden (3.10 - 3.12)."
    echo "VoiceNook benoetigt Python <3.13. Bitte installiere z.B.:"
    echo "    brew install python@3.12"
    echo "oder setze PYTHON_BIN, z.B.:"
    echo "    PYTHON_BIN=python3.12 ./install.sh"
    exit 1
fi

echo "==> Verwende Python: $PY"

# venv anlegen (falls noetig; bestehende venv wird NICHT ueberschrieben)
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Lege venv an ..."
    "$PY" -m venv "$VENV_DIR"
else
    echo "==> venv existiert bereits."
fi
source "$VENV_DIR/bin/activate"

echo "==> Aktualisiere pip ..."
pip install --upgrade pip

echo "==> Installiere VoiceNook (editable) ..."
pip install -e "$SCRIPT_DIR"

echo "==> Installiere zusaetzliche Abhaengigkeiten (Upload/Convert) ..."
pip install pydub python-multipart

echo "==> Pruefe ffmpeg (fuer MP3-Konvertierung) ..."
if command -v ffmpeg >/dev/null 2>&1; then
    echo "    ffmpeg ist vorhanden."
else
    echo "    ffmpeg fehlt — installiere via Homebrew (benoetigt Passwort):"
    brew install ffmpeg
fi

echo ""
echo "==> Fertig. Starte mit:"
echo "    ./run.sh"
echo "    Danach im Browser: http://127.0.0.1:8080"