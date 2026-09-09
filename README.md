# 🎙️ VoiceNook

**Ein leichter All-in-One Voice-Design- und Voice-Cloning-Server mit WebUI für macOS.**

VoiceNook bündelt zwei TTS-Modelle in einem lokalen Server mit einer einzigen, deutschen Web-Oberfläche:

- **VoxCPM2** — Voice Design aus einer Beschreibung (ohne Referenz), Voice Cloning (mit/ohne Reftext), Streaming, 48 kHz.
- **Higgs v3** — Alternative Engine für Emotions-/Stil-Steuerung über Inline-Tags, lange Texte (Hörbuch-artig) via satzweisem Chunking.

> Nur auf macOS mit Apple Silicon (M1/M2/M3/M4) getestet — entwickelt auf einem **M3 Ultra**.

---

## Features

- **Voice Design** — erzeuge eine neue Stimme nur aus einer Beschreibung in natürlicher Sprache (z. B. *"A warm, calm male voice, slightly smiling"*).
- **Voice Cloning** — lade eine Referenzaufnahme (auch Handy-MP3) hoch; optional mit Reftext für höhere Ähnlichkeit.
- **Gemeinsame Stimmen-Bibliothek** — Stimmen anhören (Testsatz per Klick), löschen, speichern. Eine gespeicherte Stimme ist in **beiden** Engines nutzbar.
- **Mehrere Download-Formate** — WAV (verlustfrei, 16-bit mono) als Standard, optional MP3/FLAC/OPUS/OGG/AAC.
- **Streaming-Wiedergabe** direkt im Browser, inkl. TTFB-Anzeige.
- **Erweiterbare Parameter** pro Engine (cfg, inference_timesteps, seed, temperature, …) in einem aufklappbaren **"Erweitert"**-Bereich.
- **Seed-Steuerung** für reproduzierbare Ausgabe.

---

## Installation (macOS, Apple Silicon)

Voraussetzung: **Python 3.10–3.12** und **Homebrew** (für ffmpeg).

```bash
# 1. Klonen
git clone https://github.com/wraith11/VoiceNook.git
cd VoiceNook

# 2. Installieren (eine venv, alle Abhängigkeiten + ffmpeg)
chmod +x install.sh run.sh
./install.sh
```

`install.sh` legt eine venv unter `~/Persona/voicenook-venv` an, installiert das Paket (editable) sowie `pydub`, `python-multipart` und `mlx-audio`. Falls ffmpeg fehlt, wird es per `brew install ffmpeg` nachgezogen.

> Die VoxCPM2-Modelldateien werden beim ersten Start automatisch von HuggingFace heruntergeladen
> (Repo `seba/VoxCPM2ANE-Preview`). Für den Higgs-Tab lädt `higgs_server.py` das MLX-Modell
> (`whitelabel/mlx-q6-higgs-tts-3-4b`) **lazy** beim ersten Higgs-Request.

---

## Starten

```bash
./run.sh
```

- **WebUI:** http://127.0.0.1:8005
- **Higgs-Server:** http://127.0.0.1:8006 (lazy, nur aktiv wenn genutzt)

`run.sh` startet beide Server aus derselben venv. Mit `Ctrl+C` werden beide beendet.

> **Hinweis:** Der Higgs-Tab benötigt den Higgs-Server auf Port 8006. Ist er nicht erreichbar,
> funktionieren VoxCPM2 und die Stimmen-Bibliothek trotzdem — nur die Higgs-Synthese ist dann nicht verfügbar.

---

## Verwendung

1. **Stimmen-Bibliothek** → **"Stimme erstellen"**: Name + Audiodatei (mp3/wav/flac) + optionaler Reftext. Die Datei wird automatisch in 16 kHz Mono-WAV konvertiert und als Referenz gespeichert.
2. **VoxCPM2-Tab** → Modus wählen:
   - **Voice Design**: nur Beschreibung, keine Referenz → zufällige, aber beschreibungsgetragene Stimme.
   - **Clone (Reference + Beschreibung)**: gewählte Stimme + optionale Beschreibung.
   - **Clone (High similarity, ohne Beschreibung)**: maximale Treue zur Referenz.
3. **Synthetisieren** → Audio wird gestreamt und abgespielt. Danach Download (WAV/MP3/…) oder **"Als Stimme speichern"** (verwendet den gecachten Text als Reftext).
4. **Higgs-Tab** → Stimme wählen, optional **Steuertokens** (Emotion/Stil/Prosodie/SFX) per Klick an der Cursor-Position einfügen, lange Texte einfügen und synthetisieren.

---

## Projektstruktur

```
VoiceNook/
├── install.sh              # eine venv + alle Abhängigkeiten + ffmpeg
├── run.sh                  # startet VoxCPM2- und Higgs-Server
├── higgs_server.py         # eigenständiger Higgs-v3-Server (MLX, lazy)
├── pyproject.toml
└── src/voxcpmane/          # VoxCPM2-Runtime (Original, angepasst)
    ├── server.py           # + Upload, Convert, Reftexts, geteilte Stimmen
    └── frontend/index.html # VoiceNook-WebUI (ersetzt das Original)
```

---

## Danksagung

- **VoxCPM / VoxCPM2** — [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) (Apache-2.0)
- **VoxCPMANE / VoxCPMANE2** — [0seba/VoxCPMANE](https://github.com/0seba/VoxCPMANE) (MIT) — das Originalprojekt, aus dem die VoxCPM2-ANE-Runtime stammt
- **Higgs Audio v3** — [bosonai/higgs-tts-3-4b](https://huggingface.co/bosonai/higgs-tts-3-4b) und [Blaizzy/mlx-audio](https://github.com/Blaizzy/mlx-audio)
- **mlx-audio** — MLX/Metal-Port für Higgs

**Lizenz:** Dieses Projekt ist ein angepasster Fork von `0seba/VoxCPMANE` (MIT). Higgs-Modelle unterliegen der jeweils eigenen Lizenz (siehe Modell-Cards). Bitte beachte die Nutzungsbedingungen der einzelnen Modelle — insbesondere keine Voice-Clones ohne Einwilligung.

---

*Erstellt mit **Vibe Code**.*