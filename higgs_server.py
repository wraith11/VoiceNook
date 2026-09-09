#!/usr/bin/env python3
"""Higgs v3 TTS-Server fuer VoiceNook (MLX/Metal, lazy-loading, CORS).

- liest die geteilte Stimmen-Bibliothek (~/.cache/ane_tts): name.wav + name.txt
- unterstuetzt lange Texte: satzweises Chunking + kontinuierlicher Stream
- laedt das Modell erst beim ersten Request (lazy) und haelt es dann warm
- CORS-freundlich fuer die VoiceNook-WebUI (Port 8005 -> ruft :8006)

Start: python -u higgs_server.py --port 8006
"""
import argparse
import io
import os
import re
import threading
import time
import warnings
import wave

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

warnings.filterwarnings("ignore")

VOICE_DIR = os.path.expanduser("~/.cache/ane_tts")
SR = 24000
HOP = 960
IDLE_TIMEOUT_SECONDS = 300  # Standard: 5 Minuten Inaktivitaet -> Auto-Stop

app = FastAPI(title="VoiceNook Higgs TTS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    expose_headers=["X-Sample-Rate"],
)

_model = None
_sessions = {}
_args = None
_LAST_ACTIVITY = time.time()


def _touch_activity():
    """Wird bei jedem Request aufgerufen, um den Idle-Timer zurückzusetzen."""
    global _LAST_ACTIVITY
    _LAST_ACTIVITY = time.time()


def _idle_watchdog():
    """Beendet den Server, wenn länger als IDLE_TIMEOUT keine Anfrage kam."""
    while True:
        time.sleep(10)
        if _model is not None and (time.time() - _LAST_ACTIVITY) > IDLE_TIMEOUT_SECONDS:
            print(f"[*] Higgs inaktiv fuer >{IDLE_TIMEOUT_SECONDS}s - Auto-Stop.", flush=True)
            os._exit(0)


def list_voices():
    if not os.path.isdir(VOICE_DIR):
        return []
    out = []
    for f in sorted(os.listdir(VOICE_DIR)):
        if f.endswith(".wav") and not f.endswith("_upload.wav"):
            out.append(f[:-4])
    return out


def voice_reftext(name):
    p = os.path.join(VOICE_DIR, name + ".txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return fh.read().strip()
    return ""


@app.get("/api/voices")
def api_voices():
    names = list_voices()
    return {
        "voices": names,
        "details": {n: voice_reftext(n) for n in names},
        "voice_dir": VOICE_DIR,
    }


def get_model():
    global _model
    if _model is None:
        from mlx_audio.tts import load
        print("[*] Lade Higgs-Modell (lazy) ...", flush=True)
        _model = load(_args.model)
        print("[warmup] Graph-Kompilierung ...", flush=True)
        list(_model.generate("Warmup.", temperature=1.0, max_new_tokens=16))
        print("[*] Higgs-Modell bereit.", flush=True)
    return _model


def get_session(voice):
    if voice in _sessions:
        return _sessions[voice]
    wav = os.path.join(VOICE_DIR, f"{voice}.wav")
    if not os.path.exists(wav):
        raise HTTPException(404, f"Stimme '{voice}' nicht gefunden")
    ref_text = voice_reftext(voice) or None
    model = get_model()
    sess = HiggsVoiceSession(model, ref_audio=wav, ref_text=ref_text)
    _sessions[voice] = sess
    return sess


def split_segments(text, max_chars=400):
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
    segs, cur = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if cur and len(cur) + len(p) + 1 > max_chars:
            segs.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        segs.append(cur)
    return segs or [text]


def audio_float_to_int16(audio):
    return (np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0) * 32767.0).astype(np.int16)


@app.post("/api/synthesize/stream")
def synthesize_stream(body: dict):
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Text leer")
    voice = (body.get("voice") or "").strip() or None
    if not voice:
        raise HTTPException(400, "Bitte eine Stimme waehlen (Higgs braucht eine Referenz)")
    sess = get_session(voice)

    kw = {}
    for k in ("temperature", "top_k", "top_p", "chunk_frames", "ctx_frames",
              "first_chunk_frames", "lookahead_frames", "seam_frames", "seed"):
        v = body.get(k)
        if v is not None:
            kw[k] = v
    kw.setdefault("max_frames", 2000)

    def gen():
        try:
            for i, seg in enumerate(split_segments(text)):
                print(f"[seg {i}] {len(seg)} Zeichen", flush=True)
                for chunk in sess.stream_turn(seg, **kw):
                    yield audio_float_to_int16(chunk).tobytes()
        except Exception as e:
            import traceback
            print("ERROR:", flush=True)
            traceback.print_exc()

    return StreamingResponse(
        gen(), media_type="application/octet-stream",
        headers={"X-Sample-Rate": str(SR)},
    )


@app.post("/api/synthesize")
def synthesize(body: dict):
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Text leer")
    voice = (body.get("voice") or "").strip() or None
    if not voice:
        raise HTTPException(400, "Bitte eine Stimme waehlen")
    sess = get_session(voice)
    kw = {}
    for k in ("temperature", "top_k", "top_p", "chunk_frames", "ctx_frames",
              "first_chunk_frames", "lookahead_frames", "seam_frames", "seed"):
        v = body.get(k)
        if v is not None:
            kw[k] = v
    kw.setdefault("max_frames", 2000)

    chunks = []
    for seg in split_segments(text):
        for c in sess.stream_turn(seg, **kw):
            chunks.append(c)
    audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    pcm = audio_float_to_int16(audio)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=higgs_out.wav"},
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": _model is not None,
        "voices": len(list_voices()),
        "sessions": list(_sessions.keys()),
    }


# ============================================================
#  HiggsVoiceSession (eingebettet)
# ============================================================
def _make_seam_joiner(xf_frames):
    xf = max(2, int(round(xf_frames * HOP)))
    hold = None

    def push(wav):
        nonlocal hold
        if hold is None or len(hold) == 0:
            if len(wav) <= xf:
                hold = wav.copy(); return np.zeros(0, dtype=np.float32)
            out = wav[:-xf]; hold = wav[-xf:].copy()
            n = min(xf, len(out))
            if n:
                out[:n] *= np.linspace(0.0, 1.0, n, dtype=np.float32)
            return out
        n = min(xf, len(wav), len(hold))
        ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)
        cross = hold[:n] * (1 - ramp) + wav[:n] * ramp
        rest = wav[n:]
        if len(rest) > xf:
            out = np.concatenate([cross, rest[:-xf]])
            hold = rest[-xf:].copy()
        else:
            out = cross
            hold = rest.copy()
        return out

    def flush(fade_frames=8.0):
        nonlocal hold
        if hold is None or len(hold) == 0:
            return np.zeros(0, dtype=np.float32)
        out = hold.copy()
        n = min(int(round(fade_frames * HOP)), len(out))
        if n:
            out[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)
        hold = None
        return out

    return push, flush


class HiggsVoiceSession:
    def __init__(self, model, ref_audio=None, ref_text=None):
        import mlx.core as mx
        self.model = model
        self.mx = mx
        self.cfg = model.config
        self.N = self.cfg.audio_num_codebooks
        self.ref_codes = None
        if ref_audio:
            self.ref_codes = model.encode_reference_audio(ref_audio)
        self.ref_text = ref_text
        self.prefix_cache_state = None
        self.prefix_len = 0
        if self.ref_codes is not None:
            self._prepare_prefix_cache()

    def _build_prefix_embeds(self):
        from mlx_audio.tts.models.higgs_audio_v3.prompt import ReferenceCodes
        refs = ([ReferenceCodes(codes=self.ref_codes, text=self.ref_text)]
                if self.ref_codes is not None else [])
        prompt = self.model._prompt_builder.build_prompt("", references=refs)
        pieces, cursor = [], 0
        for start, delayed_codes in prompt.audio_segments:
            pieces.append(self.model._text_embeddings(prompt.token_ids[cursor:start]))
            pieces.append(self.model._embed_audio_codes(delayed_codes))
            cursor = start + int(delayed_codes.shape[0])
        tail_ids = prompt.token_ids[cursor:]
        if tail_ids:
            tail_ids = tail_ids[:-1]
        pieces.append(self.model._text_embeddings(tail_ids))
        full = self.mx.concatenate([p for p in pieces if p.shape[0] > 0], axis=0)
        return full[None]

    def _prepare_prefix_cache(self):
        from mlx_audio.lm.models.cache import make_prompt_cache
        prefix_embeds = self._build_prefix_embeds()
        cache = make_prompt_cache(self.model.backbone)
        dummy = self.mx.zeros((1, prefix_embeds.shape[1]), dtype=self.mx.int32)
        self.model.backbone(dummy, cache=cache, input_embeddings=prefix_embeds)
        self.prefix_len = prefix_embeds.shape[1]
        self.prefix_cache_state = [c.state for c in cache]
        self.mx.eval(*[s for c in cache for s in (c.keys, c.values)])

    def _restore_prefix_cache(self):
        from mlx_audio.lm.models.cache import make_prompt_cache
        cache = make_prompt_cache(self.model.backbone)
        for c, state in zip(cache, self.prefix_cache_state):
            c.state = state
        return cache

    def _build_text_tail_embeds(self, text, refs):
        prompt = self.model._prompt_builder.build_prompt(text, references=refs)
        if not prompt.audio_segments:
            full, _ = self.model._build_prompt_embeddings(text, refs)
            return full[:, self.prefix_len:, :]
        last_start, last_codes = prompt.audio_segments[-1]
        tail_start = last_start + int(last_codes.shape[0])
        tail_ids = prompt.token_ids[tail_start:]
        tail_ids = tail_ids[1:]
        return self.model._text_embeddings(tail_ids)[None]

    def stream_turn(self, text, *, chunk_frames=24, ctx_frames=8,
                    first_chunk_frames=8, lookahead_frames=16,
                    max_frames=900, temperature=0.8, top_k=50, top_p=0.95,
                    seed=0, seam_frames=0.25):
        import mlx.core as mx
        from mlx_audio.tts.models.higgs_audio_v3.generation import (
            HiggsSamplerState, reverse_delay_pattern, step,
        )
        from mlx_audio.tts.models.higgs_audio_v3.prompt import ReferenceCodes

        if seed is not None:
            mx.random.seed(int(seed))
        refs = ([ReferenceCodes(codes=self.ref_codes, text=self.ref_text)]
                if self.ref_codes is not None else [])

        if self.prefix_cache_state is not None:
            cache = self._restore_prefix_cache()
            text_embeds = self._build_text_tail_embeds(text, refs)
            dummy = mx.zeros((1, text_embeds.shape[1]), dtype=mx.int32)
            hidden = self.model.backbone(dummy, cache=cache, input_embeddings=text_embeds)
            last_hidden = hidden[:, -1, :]
            mx.eval(last_hidden)
        else:
            from mlx_audio.lm.models.cache import make_prompt_cache
            cache = make_prompt_cache(self.model.backbone)
            prompt_embeds, _ = self.model._build_prompt_embeddings(text, refs)
            mx.eval(prompt_embeds)
            dummy = mx.zeros((1, prompt_embeds.shape[1]), dtype=mx.int32)
            hidden = self.model.backbone(dummy, cache=cache, input_embeddings=prompt_embeds)
            last_hidden = hidden[:, -1, :]
            mx.eval(last_hidden)

        cfg = self.cfg
        state = HiggsSamplerState(num_codebooks=cfg.audio_num_codebooks)
        delayed, base_f, emitted_frames = [], 0, 0
        lookahead = lookahead_frames
        MARGIN = self.N
        push, flush = _make_seam_joiner(seam_frames)

        def decode_new(start_f, end_f):
            nonlocal emitted_frames, base_f, delayed
            full = mx.stack(delayed, axis=0).astype(mx.int32)
            raw = reverse_delay_pattern(full)
            T = raw.shape[0]
            if emitted_frames == 0:
                end = min(end_f - base_f, T)
                codes = np.clip(np.array(raw[0:end]).astype(np.int32), 0, 1023)
                wav = _decode_codes(self.model, codes)
                emitted_frames = end_f
            else:
                a = max(0, (start_f - ctx_frames) - base_f)
                e = min(end_f + lookahead - base_f, T)
                codes = np.clip(np.array(raw[a:e]).astype(np.int32), 0, 1023)
                wav = _decode_codes(self.model, codes)
                drop = (start_f - base_f - a) * HOP
                n_t = (end_f - start_f) * HOP
                wav = wav[drop:drop + n_t]
                emitted_frames = end_f
            keep_from = max(base_f, emitted_frames - (ctx_frames + MARGIN))
            if keep_from > base_f:
                cut = keep_from - base_f
                delayed = delayed[cut:]
                base_f = keep_from
            return wav

        for _ in range(int(max_frames)):
            logits = self.model._audio_logits(last_hidden)[0]
            codes = step(logits, state, temperature=temperature, top_p=top_p,
                         top_k=top_k, boc_id=cfg.audio_boc_token_id,
                         eoc_id=cfg.audio_eoc_token_id)
            delayed.append(codes)
            done = state.generation_done
            available = (base_f + len(delayed)) - self.N + 1
            first = emitted_frames == 0
            threshold = first_chunk_frames if first else chunk_frames
            if done or (available - emitted_frames >= threshold):
                if available - emitted_frames > 0:
                    out = push(decode_new(emitted_frames, available))
                    if out.size:
                        yield out.astype(np.float32)
            if done:
                break
            next_embed = self.model._embed_audio_codes(codes)[None]
            decode_dummy = mx.zeros((1, 1), dtype=mx.int32)
            hidden = self.model.backbone(decode_dummy, cache=cache,
                                         input_embeddings=next_embed)
            last_hidden = hidden[:, -1, :]
            mx.eval(last_hidden)

        available = (base_f + len(delayed)) - self.N + 1
        if available - emitted_frames > 0:
            out = push(decode_new(emitted_frames, available))
            if out.size:
                yield out.astype(np.float32)
        tail = flush()
        if tail.size:
            yield tail.astype(np.float32)


def _decode_codes(model, codes_np):
    import mlx.core as mx
    codes = mx.array(codes_np, dtype=mx.int32)
    audio = model._codec.decode(codes)
    mx.eval(audio)
    return np.array(audio).astype(np.float32).reshape(-1)


def main():
    global _args, VOICE_DIR
    p = argparse.ArgumentParser(description="VoiceNook Higgs Server (lazy)")
    p.add_argument("--model", default="whitelabel/mlx-q6-higgs-tts-3-4b")
    p.add_argument("--voice-dir", default=VOICE_DIR,
                   help="Geteilte Stimmen-Bibliothek (name.wav + name.txt)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8006)
    _args = p.parse_args()
    VOICE_DIR = os.path.abspath(_args.voice_dir)
    print(f"[*] Higgs-Server (lazy) auf http://{_args.host}:{_args.port}", flush=True)
    print(f"[*] Stimmen-Bibliothek: {VOICE_DIR}", flush=True)
    uvicorn.run(app, host=_args.host, port=_args.port, log_level="info")


if __name__ == "__main__":
    main()