# 🎙️ VoiceNook

**Ein leichter All-in-One Voice-Design- und Voice-Cloning-Server mit WebUI für macOS.**

VoiceNook bündelt zwei TTS-Modelle in einem lokalen Server mit einer einzigen, zweisprachigen (de/en) Web-Oberfläche:

- **VoxCPM2** — Voice Design aus einer Beschreibung (ohne Referenz), Voice Cloning (mit/ohne Reftext).
- **Higgs v3** — Alternative Engine für Emotions-/Stil-Steuerung über Inline-Tags, lange Texte via satzweisem Chunking.

> Nur auf macOS mit Apple Silicon M3 getestet.

---

## Features

- **Voice Design** — erzeuge eine neue Stimme nur aus einer Beschreibung in natürlicher Sprache (z. B. *"A warm, calm male voice, slightly smiling"*).
- **Voice Cloning** — lade eine Referenzaufnahme (auch Handy-MP3) hoch; optional mit Reftext für höhere Ähnlichkeit.
- **Gemeinsame Stimmen-Bibliothek** — Stimmen anhören (Testsatz per Klick), löschen, speichern. Eine gespeicherte Stimme ist in **beiden** Engines nutzbar.
- **Mehrere Download-Formate** — WAV (verlustfrei, 16-bit mono) als Standard, optional MP3/FLAC/OPUS/OGG/AAC.
- **Generate & play / Generate only** — der Synthese-Button streamt standardmäßig live (Generate & play); über ein Dropdown kann pro Sitzung auf **Generate only** umgestellt werden (komplett generieren, dann manuell Play drücken — nützlich für langsamere Systeme, die kein Echtzeit-Streaming schaffen).
- **Seed-Steuerung** für reproduzierbare Ausgabe.
- **Konfigurierbare Defaults** für `cfg_value` und `inference_timesteps` per Startparameter.
- **Higgs on-demand** — der Higgs-Server startet nur, wenn er gebraucht wird (Klick auf den Higgs-Status oder Generierungsanfrage) und stoppt sich nach Inaktivität selbst. Für RAM-schwache Systeme lässt er sich komplett deaktivieren.

---

## RAM-Hinweis

| Komponente | Zusätzlicher RAM |
|---|---|
| **VoxCPM2** (CoreML/ANE) | ~3,2 GB — **immer** geladen (WebUI) |
| **Higgs v3** (MLX, q6) | **~3–4 GB extra**, aber nur **während der Higgs aktiv ist** |

Higgs lädt das Modell **lazy**: Erst wenn der Higgs-Tab genutzt wird (oder der Higgs-Status geklickt wird), wird der Server gestartet und das Modell in den Speicher geladen. Nach **5 Minuten Inaktivität** (einstellbar) beendet sich der Higgs-Server selbst und gibt den Speicher wieder frei.

> **RAM-schwache Systeme:** Mit `--no-higgs` wird der Higgs-Tab komplett ausgeblendet und der Higgs-Server nie gestartet — dann wird nur VoxCPM2 (~3,2 GB) verwendet.

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
> (Repo `seba/VoxCPM2ANE-Preview`). Das Higgs-Modell (`whitelabel/mlx-q6-higgs-tts-3-4b`) lädt `higgs_server.py` **lazy** beim ersten Higgs-Request.

---

## Starten

```bash
./run.sh
```

- **WebUI:** http://127.0.0.1:8080

`run.sh` startet **nur** den VoxCPM2-Server. Der Higgs-Server wird bei Bedarf von der WebUI aus gestartet (Klick auf den Higgs-Status im Higgs-Tab oder Generierungsanfrage) und stoppt sich nach Inaktivität selbst.

---

## Startparameter (`voicenook-server`)

| Parameter | Standard | Beschreibung |
|---|---|---|
| `--lang de\|en` | `de` | Sprache der WebUI (Deutsch oder Englisch) |
| `--cfg-default <float>` | `2.0` | Standardwert für `cfg_value` in der WebUI |
| `--steps-default <int>` | `20` | Standardwert für `inference_timesteps` — für langsamere Systeme z. B. `7` |
| `--no-higgs` | — | Higgs-Tab ausblenden, Higgs-Server nie starten (RAM-schwache Systeme) |
| `--higgs-url <url>` | `http://127.0.0.1:8006` | Basis-URL des Higgs-Servers |
| `--port`, `--host` | `8000` / `0.0.0.0` | VoxCPM2-Server-Port/Host |

**Beispiele:**
```bash
# Englische UI, langsamere Defaults, Higgs deaktiviert
voicenook-server --host 0.0.0.0 --port 8000 \
    --lang en --cfg-default 2.0 --steps-default 7 --no-higgs

# Standard (deutsch, timesteps 20, Higgs on-demand)
voicenook-server --host 0.0.0.0 --port 8005
```
---

## Verwendung

1. **Stimmen-Bibliothek** → **"Stimme erstellen"**: Name + Audiodatei (mp3/wav/flac) + optionaler Reftext. Die Datei wird automatisch in 16 kHz Mono-WAV konvertiert und als Referenz gespeichert.
2. **VoxCPM2-Tab** → Modus wählen:
   - **Voice Design**: nur Beschreibung, keine Referenz → zufällige, aber beschreibungsgetragene Stimme.
   - **Clone (Reference + Beschreibung)**: gewählte Stimme + optionale Beschreibung.
   - **Clone (High similarity, ohne Beschreibung)**: maximale Treue zur Referenz.
3. **Synthetisieren** → Button "Generate & play" streamt und spielt ab. Über das Dropdown neben dem Button auf **Generate only** umschalten (komplett generieren, dann Play drücken). Danach Download (WAV/MP3/…) oder **"Als Stimme speichern"**.
4. **Higgs-Tab** → Stimme wählen, optional **Steuertokens** (Emotion/Stil/Prosodie/SFX) per Klick einfügen, lange Texte einfügen und synthetisieren. Der Higgs-Status oben zeigt, ob der Higgs-Server aktiv ist — ein Klick startet bzw. stoppt ihn.

---

## Danksagung

- **VoxCPM / VoxCPM2** — [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) (Apache-2.0)
- **VoxCPMANE / VoxCPMANE2** — [0seba/VoxCPMANE](https://github.com/0seba/VoxCPMANE) (MIT) — das Originalprojekt, aus dem die VoxCPM2-ANE-Runtime stammt
- **Higgs Audio v3** — [bosonai/higgs-tts-3-4b](https://huggingface.co/bosonai/higgs-tts-3-4b) und [Blaizzy/mlx-audio](https://github.com/Blaizzy/mlx-audio)
- **mlx-audio** — MLX/Metal-Port für Higgs

**Lizenz:** Dieses Projekt ist ein angepasster Fork von `0seba/VoxCPMANE` (MIT). Higgs-Modelle unterliegen der jeweils eigenen Lizenz (siehe Modell-Cards). Bitte beachte die Nutzungsbedingungen der einzelnen Modelle — insbesondere keine Voice-Clones ohne Einwilligung.

---

## Hinweis zur Entwicklung

Dieses Projekt wurde vollständig mit **DeepSeek v4 Flash** entwickelt.
Die KI generierte den Großteil des Codes; Review und Testing wurden manuell durchgeführt.
