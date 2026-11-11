"""Narration for one episode: script.json -> voice/*.wav -> vo.wav + timeline.json (word timings) + mouth.json.

  python voice.py EP                      synthesize every line (cached), then align words
  python voice.py EP --provider edge      free placeholder voice (edge-tts), no keys needed
  python voice.py EP --test "One line."   synthesize a single test line -> EP/voice/test.mp3

Providers
  minimax MiniMax TTS (t2a_v2). Needs MINIMAX_API_KEY. The series can override the default clone with voice.voice_id.
        Optional MINIMAX_TTS_MODEL (default speech-2.8-hd) and MINIMAX_TTS_BASE_URL (default https://api.minimax.cn).
  volc  Volcano Engine voice clone (your own voice). Needs VOLC_API_KEY and VOLC_SPEAKER_ID (S_...).
        Keys for both are looked up in the environment, then in .env files from EP upward,
        then ~/.vote-series/.env. Never print or commit the keys.
  edge  edge-tts placeholder. Voice from series.json "voice.edge_voice" (default en-US-GuyNeural).

Words are aligned with faster-whisper on CPU (large-v3 if downloaded, else small).
"""
import argparse, base64, binascii, hashlib, json, os, subprocess, sys, uuid, wave
import urllib.request
import numpy as np

SR = 48000
FPS = 30


def load_series(ep):
    p = os.path.join(os.path.dirname(os.path.abspath(ep)), "series.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def env_lookup(ep):
    e = {}
    d = os.path.abspath(ep); paths = []
    while True:
        paths.append(os.path.join(d, ".env"))
        up = os.path.dirname(d)
        if up == d: break
        d = up
    paths.append(os.path.join(os.path.expanduser("~"), ".vote-series", ".env"))
    for p in reversed(paths):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8-sig"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    e[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("VOLC_API_KEY", "VOLC_SPEAKER_ID", "VOLC_RESOURCE_ID", "VOLC_APP_ID", "VOLC_ACCESS_TOKEN",
              "MINIMAX_API_KEY", "MINIMAX_TTS_MODEL", "MINIMAX_TTS_BASE_URL"):
        if os.environ.get(k): e[k] = os.environ[k]
    return e


def synth_minimax(text, e):
    """MiniMax t2a_v2. Returns mp3 bytes. The audio comes back hex-encoded (not base64),
    and failures still arrive with HTTP 200 — the real status is base_resp.status_code."""
    if not e.get("MINIMAX_API_KEY") or not e.get("MINIMAX_VOICE_ID"):
        raise SystemExit("x MiniMax requires an API key and voice ID.")
    base = (e.get("MINIMAX_TTS_BASE_URL") or "https://api.minimax.cn").rstrip("/")
    body = {"model": e.get("MINIMAX_TTS_MODEL") or "speech-2.8-hd", "text": text,
            "voice_setting": {"voice_id": e["MINIMAX_VOICE_ID"], "speed": 1.0, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1}}
    req = urllib.request.Request(f"{base}/v1/t2a_v2", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {e['MINIMAX_API_KEY']}",
                                          "Content-Type": "application/json"}, method="POST")
    r = json.load(urllib.request.urlopen(req, timeout=120))
    st = (r.get("base_resp") or {}).get("status_code")
    if st != 0:
        raise SystemExit(f"x MiniMax error {st}: {(r.get('base_resp') or {}).get('status_msg')}")
    audio = (r.get("data") or {}).get("audio")
    if not audio: raise SystemExit("x MiniMax returned no audio")
    out = binascii.unhexlify(audio)
    want = (r.get("extra_info") or {}).get("audio_size")
    if want and len(out) != want:
        raise SystemExit(f"x MiniMax audio size mismatch: got {len(out)}, expected {want}")
    return out


def synth_volc(text, e):
    if not e.get("VOLC_SPEAKER_ID") or not (e.get("VOLC_API_KEY") or e.get("VOLC_APP_ID")):
        raise SystemExit("x Volcano keys missing (VOLC_API_KEY + VOLC_SPEAKER_ID). Use --provider edge for a placeholder.")
    if e.get("VOLC_API_KEY"):
        auth = {"X-Api-Key": e["VOLC_API_KEY"]}
    else:
        auth = {"X-Api-App-Id": e["VOLC_APP_ID"], "X-Api-Access-Key": e["VOLC_ACCESS_TOKEN"]}
    headers = {**auth, "X-Api-Resource-Id": e.get("VOLC_RESOURCE_ID", "seed-icl-2.0"),
               "X-Api-Request-Id": str(uuid.uuid4()), "Content-Type": "application/json"}
    body = {"user": {"uid": "vote-series"}, "req_params": {"text": text, "speaker": e["VOLC_SPEAKER_ID"],
                                                            "audio_params": {"format": "mp3", "sample_rate": 24000}}}
    req = urllib.request.Request("https://openspeech.bytedance.com/api/v3/tts/unidirectional",
                                 data=json.dumps(body).encode(), headers=headers, method="POST")
    content = urllib.request.urlopen(req, timeout=120).read()
    chunks = []
    for line in content.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith("data:"): line = line[5:].strip()
        if not line.startswith("{"): continue
        d = json.loads(line)
        if d.get("code", 0) not in (0, 20000000):
            raise SystemExit(f"x synthesis error code={d.get('code')}: {d.get('message')}")
        if d.get("data"): chunks.append(base64.b64decode(d["data"]))
    if not chunks: raise SystemExit("x no audio returned")
    return b"".join(chunks)


def synth_edge(text, voice, out):
    import asyncio, edge_tts
    asyncio.run(edge_tts.Communicate(text, voice).save(out))


def to_wav(mp3, wav):
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", trim, "-ar", str(SR), "-ac", "1", wav], check=True)


def read_wav(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("--provider", choices=("minimax", "volc", "edge")); ap.add_argument("--test"); ap.add_argument("--model")
    a = ap.parse_args()
    ep = os.path.abspath(a.ep); series = load_series(ep)
    vcfg = series.get("voice", {})
    prov = a.provider or vcfg.get("provider", "minimax")
    if prov not in ("minimax", "volc", "edge"):
        ap.error(f"Unknown voice provider: {prov}")
    edge_voice = vcfg.get("edge_voice", "en-US-GuyNeural" if series.get("lang", "en") == "en" else "zh-CN-YunxiNeural")
    e = env_lookup(ep) if prov in ("volc", "minimax") else {}
    if prov == "minimax":
        e["MINIMAX_VOICE_ID"] = vcfg.get("voice_id") or "moss_audio_d44f4e69-dd85-11f1-8b0f-8efb672a2295"
        if not e.get("MINIMAX_API_KEY"):
            raise SystemExit("MiniMax requires MINIMAX_API_KEY.")
        print(f"Voice: MiniMax / {e['MINIMAX_VOICE_ID']}", flush=True)
    os.makedirs(os.path.join(ep, "voice"), exist_ok=True)
    # the cache key must include the voice, or switching voice_id silently reuses the old take
    vkey = {"minimax": e.get("MINIMAX_VOICE_ID", ""), "volc": e.get("VOLC_SPEAKER_ID", "")}.get(prov, edge_voice)

    def synth(text, mp3):
        if prov == "minimax": open(mp3, "wb").write(synth_minimax(text, e))
        elif prov == "volc": open(mp3, "wb").write(synth_volc(text, e))
        else: synth_edge(text, edge_voice, mp3)

    if a.test:
        out = os.path.join(ep, "voice", "test.mp3"); synth(a.test, out); print("ok", out); return

    S = json.load(open(os.path.join(ep, "script.json"), encoding="utf-8"))
    bad = [l["id"] for l in S["lines"] if "(" in l["text"] or "OPTION" in l["text"]]
    if bad: raise SystemExit(f"x script.json still has skeleton placeholders in {bad}; write the real lines first")
    for ln in S["lines"]:
        h = hashlib.md5(f"{prov}|{vkey}|{ln['text']}".encode()).hexdigest()[:8]
        mp3 = os.path.join(ep, "voice", f"{ln['id']}_{h}.mp3"); wav = os.path.join(ep, "voice", f"{ln['id']}.wav")
        if not os.path.exists(mp3):
            synth(ln["text"], mp3); print("synth", ln["id"], flush=True)
        to_wav(mp3, wav)

    from faster_whisper import WhisperModel
    hub = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    names = os.listdir(hub) if os.path.isdir(hub) else []
    model = a.model or ("large-v3" if any(n.endswith("faster-whisper-large-v3") for n in names) else "small")
    m = WhisperModel(model, device="cpu", compute_type="int8")
    lang = series.get("lang", "en")
    cur = S.get("lead", 0.6); parts = []; lines = []
    for ln in S["lines"]:
        a_ = read_wav(os.path.join(ep, "voice", f"{ln['id']}.wav")); dur = len(a_) / SR
        segs, _ = m.transcribe(a_[::3], language=lang, word_timestamps=True, initial_prompt=ln["text"])
        words = [{"w": x.word.strip(), "s": round(cur + x.start, 3), "e": round(cur + x.end, 3)} for s in segs for x in s.words]
        lines.append({**ln, "start": round(cur, 3), "end": round(cur + dur, 3), "words": words})
        parts.append((cur, a_)); cur += dur + ln.get("gap", 0.4)
    total = cur
    out = np.zeros(int(total * SR) + SR, np.float32)
    for t0, a_ in parts:
        i = int(t0 * SR); out[i:i + len(a_)] += a_
    out = out[:int(total * SR)]
    wv = wave.open(os.path.join(ep, "vo.wav"), "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); wv.close()
    json.dump({"duration": round(total, 3), "lines": lines}, open(os.path.join(ep, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hop = SR // FPS; n = int(total * FPS) + 1
    env = [float(np.sqrt(np.mean(out[i * hop:(i + 1) * hop] ** 2))) if i * hop < len(out) else 0.0 for i in range(n)]
    mx = max(env) or 1
    json.dump([round(min(1, x / mx * 1.6), 3) for x in env], open(os.path.join(ep, "mouth.json"), "w"))
    print(f"ok  {len(lines)} lines, {total:.1f}s  ({prov}, whisper {model})")
    for l in lines: print(" ", l["id"], l["start"], " ".join(w["w"] for w in l["words"]))


if __name__ == "__main__":
    main()
