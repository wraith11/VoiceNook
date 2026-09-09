# 🎙️ VoiceNook

**Ein leichter All-in-One Voice-Design- und Voice-Cloning-Server mit WebUI für macOS.**

VoiceNook bündelt zwei TTS-Modelle in **einem** lokalen Prozess mit einer zweisprachigen (de/en) Web-Oberfläche:

- **VoxCPM2** — Voice Design aus einer Beschreibung (ohne Referenz), Voice Cloning (mit/ohne Reftext), Streaming.
- **Higgs v3** — Alternative Engine für Emotions-/Stil-Steuerung über Inline-Tags, lange Texte via satzweisem Chunking.

Beide Modelle laufen **in-process** unter einem einzigen Port und laden **on-demand** — im Idle wird der RAM freigegeben.

> Nur auf macOS mit Apple Silicon getestet (M3 Ultra).

---

## Features

- **Voice Design** — erzeuge eine neue Stimme nur aus einer Beschreibung in natürlicher Sprache (z. B. *"A warm, calm male voice, slightly smiling"*).
- **Voice Cloning** — lade eine Referenzaufnahme (auch Handy-MP3) hoch; optional mit Reftext für höhere Ähnlichkeit.
- **Gemeinsame Stimmen-Bibliothek** — Stimmen anhören (Testsatz per Klick), löschen, speichern. Eine gespeicherte Stimme ist in **beiden** Engines nutzbar.
- **Mehrere Download-Formate** — WAV (verlustfrei, 16-bit mono) als Standard, optional MP3/FLAC/OPUS/OGG/AAC.
- **Generate & play / Generate only** — Button mit Dropdown, pro Sitzung umschaltbar (komplett generieren + manuell Play für langsamere Systeme).
- **Seed-Steuerung** und konfigurierbare Defaults (`cfg_value`, `inference_timesteps`).
- **Modell-Lifecycle** — beide Modelle laden on-demand, entladen sich nach Inaktivität, mit Status + Load/Unload-Buttons in der UI.
- **Ein-Port-Architektur** — Higgs wird als FastAPI-App unter `/higgs` in den Hauptserver gemountet (kein zweiter Port).

---

## Modell-Lifecycle & RAM

| Komponente | Zusätzlicher RAM |
|---|---|
| **VoxCPM2** (CoreML/ANE) | ~3,2 GB |
| **Higgs v3** (MLX, q6) | ~3–4 GB |

Beide Modelle werden **lazy** geladen — erst wenn sie tatsächlich genutzt werden. Nach **5 Minuten Inaktivität** (einstellbar mit `--idle-timeout`) werden sie automatisch **entladen**, wodurch der RAM wieder freigegeben wird. Der Server selbst bleibt dabei im Idle ultra-light.

In der UI zeigt ein **Statusindikator** je Modell (VoxCPM2 oben im Synthese-Tab, Higgs oben im Higgs-Tab), ob das Modell geladen ist. Ein Klick lädt bzw. entlädt das Modell manuell.

> **Schwache Systeme:** `--single-model` verhindert, dass beide Modelle gleichzeitig geladen sind — wird eines geladen, wird das andere zuvor entladen. `--no-higgs` blendet den Higgs-Tab komplett aus.

---

## Installation (macOS, Apple Silicon)

Voraussetzung: **Python 3.10–3.12** und **Homebrew** (für ffmpeg).

```bash
git clone https://github.com/wraith11/VoiceNook.git
cd VoiceNook
chmod +x install.sh run.sh
./install.sh
```

`install.sh` legt eine venv **im Projektordner** (`.venv`) an, installiert das Paket (editable) sowie `pydub` und `python-multipart`. Falls ffmpeg fehlt, wird es per `brew install ffmpeg` nachgezogen.

> Die VoxCPM2-Modelldateien werden beim ersten Start von HuggingFace geladen (`seba/VoxCPM2ANE-Preview`). Das Higgs-Modell (`whitelabel/mlx-q6-higgs-tts-3-4b`) wird on-demand geladen.

---

## Starten

```bash
./run.sh
```

- **WebUI:** http://127.0.0.1:8080

Ein Prozess, ein Port. Beide Modelle laden on-demand und entladen sich nach Inaktivität.

---

## Startparameter (`voicenook-server`)

| Parameter | Standard | Beschreibung |
|---|---|---|
| `--port`, `--host` | `8080` / `0.0.0.0` | WebUI-Port / Bind-Adresse |
| `--lang de\|en` | `en` | Sprache der WebUI |
| `--cfg-default <float>` | `2.0` | Standard-`cfg_value` |
| `--steps-default <int>` | `20` | Standard-`inference_timesteps` (z. B. `7` für langsamere Systeme) |
| `--no-higgs` | — | Higgs-Tab ausblenden, Higgs nie laden |
| `--single-model` | — | Nie beide Modelle gleichzeitig laden (schwache Systeme) |
| `--idle-timeout <min>` | `5` | Minuten Inaktivität bis Modelle entladen werden (`0` = nie) |
| `--higgs-model <name>` | `whitelabel/mlx-q6-higgs-tts-3-4b` | Higgs-Modell |

**VoxCPM2-Kernparameter** (vom Originalprojekt): `--lm-mode` (`single-length`/`preload`/`always-loaded`/`hot-swap`), `--lm-prefill-chunk-size` (`1`/`8`/`16`/`32`/`64`/`128`), `--model-dir`, `--repo-id`, `--embedding-path`, `--base-lm-splits`, `--base-lm-path`, `--vae-early-decode-steps`, `--vae-batch-decode-steps`, `--compile-and-save`, `--startup-warmup-repeats`, `--live-rtf`.

**Beispiele:**
```bash
# Standard (Port 8080, Englisch, beide Modelle on-demand)
voicenook-server

# Schwaches System: nur ein Modell gleichzeitig, Higgs aus, langsamere Defaults
voicenook-server --single-model --no-higgs --lang de --steps-default 7

# VoxCPM2-Optimierung
voicenook-server --lm-mode preload --lm-prefill-chunk-size 64
```

---

## Verwendung

1. **Stimmen-Bibliothek** → **"Stimme erstellen"**: Name + Audiodatei (mp3/wav/flac) + optionaler Reftext. Die Datei wird automatisch in 16 kHz Mono-WAV konvertiert und als Referenz gespeichert.
2. **VoxCPM2-Tab** → Modus wählen:
   - **Voice Design**: nur Beschreibung, keine Referenz → beschreibungsgetragene Stimme.
   - **Clone (Reference + Beschreibung)**: gewählte Stimme + optionale Beschreibung.
   - **Clone (High similarity, ohne Beschreibung)**: maximale Treue zur Referenz.
3. **Synthetisieren** → Button "Generate & play" streamt und spielt ab; über das Dropdown auf **Generate only** umschaltbar. Danach Download (WAV/MP3/…) oder **"Als Stimme speichern"**.
4. **Higgs-Tab** → Stimme wählen, optional **Steuertokens** (Emotion/Stil/Prosodie/SFX) einfügen, lange Texte synthetisieren. Der Higgs-Status zeigt den Ladezustand — ein Klick lädt/entlädt das Modell.

---

## Credits & Lizenzen

- **VoxCPM / VoxCPM2** — [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) (Apache-2.0)
- **VoxCPMANE / VoxCPMANE2** — [0seba/VoxCPMANE](https://github.com/0seba/VoxCPMANE) (MIT) — das Originalprojekt, aus dem die VoxCPM2-ANE-Runtime stammt
- **Higgs Audio v3** — [bosonai/higgs-tts-3-4b](https://huggingface.co/bosonai/higgs-tts-3-4b) und [Blaizzy/mlx-audio](https://github.com/Blaizzy/mlx-audio)

**Lizenz:** Dieses Projekt ist ein angepasster Fork von `0seba/VoxCPMANE` (MIT). Higgs-Modelle unterliegen der jeweils eigenen Lizenz (siehe Modell-Cards). Bitte beachte die Nutzungsbedingungen der einzelnen Modelle — insbesondere keine Voice-Clones ohne Einwilligung.

---

## Hinweis zur Entwicklung

Dieses Projekt wurde mittels Vibe Coding entwickelt. Die Codebasis wurde überwiegend KI-generiert und anschließend manuell geprüft und getestet.
