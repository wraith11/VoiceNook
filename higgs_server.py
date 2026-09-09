#!/usr/bin/env python3
"""VoiceNook — Higgs wird seit v0.2.0 IN-PROCESS in den Hauptserver gemountet.

Dieses Standalone-Skript ist nicht mehr der aktive Einstiegspunkt. Der Higgs-Teil
lebt jetzt als Modul unter src/voicenook/higgs_server.py und wird vom Hauptserver
unter /higgs eingebunden. Datei wird nur noch aus Kompatibilitaetsgruenden gefuehrt.

Zum Starten des kompletten VoiceNook-Servers verwende:
    voicenook-server
"""
import sys

if __name__ == "__main__":
    print("VoiceNook: Higgs laeuft jetzt in-process. Starte stattdessen 'voicenook-server'.", file=sys.stderr)
    sys.exit(1)