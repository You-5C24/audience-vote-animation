"""Soundtrack for one episode: music bed + your voice + sound effects on the visual beats.
Run via:  python <skill>/scripts/render.py EP audio   (puts audio_lib on the path)
Edit the SFX block to match this episode's beats; W(line, word) gives the time a word is spoken."""
import json, wave
import numpy as np
from audio_lib import *

TL = json.load(open("timeline.json", encoding="utf-8"))
DUR = TL["duration"]
L = {l["id"]: l for l in TL["lines"]}
LAST = TL["lines"][-1]["id"]
def T(i, word=None, part="start"):
    """time of line i (start/end), or of the first word starting with 'word'; NaN if the line doesn't exist (sfx() skips it)"""
    if i not in L: return float("nan")
    if word:
        for x in L[i]["words"]:
            if x["w"].lower().strip(".,?!").startswith(word): return x["s"]
    return L[i][part]
W = lambda i, w: T(i, w)

mix = Mixer(dur=DUR, bpm=100)
B = mix.beat

# ---- music: bouncy pluck progression C - G - Am - F, quiet bed under the voice
prog = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
roots = [48, 43, 45, 41]
bar = 4 * B
t = 0.0; j = 0
while t < T(LAST) - 0.05:
    ch, rt = prog[j % 4], roots[j % 4]
    for b in range(4):
        tb = t + b * B
        if tb >= T(LAST) - 0.05: break
        mix.add(bass(rt - 12, B * 0.8, drive=0.15), tb, g=0.22)
        for k, n in enumerate(ch):
            mix.add(pluck(n + (12 if b % 2 else 0), d=0.25, bright=3200, decay=10), tb + B / 2 + k * 0.012, g=0.07, pan=-0.3 + 0.3 * k, verb=0.25)
        mix.add(hat(), tb + B / 2, g=0.05, pan=0.3)
        if b % 2 == 1: mix.add(clap(), tb, g=0.06, verb=0.2)
    t += bar; j += 1
# end: big chord
for n in [60, 64, 67, 72]: mix.add(bell(n, d=1.6), T(LAST), g=0.12, verb=0.4)
mix.add(kick(big=True), T(LAST), g=0.35)

# ---- voice
w = wave.open("vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
mix.add(vo, 0.0, g=1.0)

# ---- sfx (EXAMPLE = Day 1's beats; rewrite for each episode. sfx() skips lines that don't exist)
def sfx(sig, t, **k):
    if t == t: mix.add(sig, t, **k)   # NaN != NaN -> skipped
sfx(blip(300, 900, d=0.18), T("L01"), g=0.25)
for d in (0.35, 1.4, 2.6): sfx(blip(1300, 1700, d=0.07, decay=30), T("L02") + d, g=0.22)
sfx(whoosh(0.35, 500, 3000), T("L03") - 0.1, g=0.25)
tt_ = np.arange(int(2.6 * SR)) / SR                       # fly buzz
fly = (np.sin(2 * np.pi * 210 * tt_) + 0.5 * np.sign(np.sin(2 * np.pi * 420 * tt_))) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tt_)) * np.minimum(1, tt_ * 4) * np.minimum(1, (2.6 - tt_) * 4)
sfx(filt(fly, "bandpass", [150, 2500]) * 0.5, T("L03") + 0.2, g=0.06, pan=-0.4)
sfx(blip(180, 700, d=0.45, decay=6), W("L04", "haircut"), g=0.25)
for i in range(7): sfx(tick(), T("L05") + i * 0.12 + 0.05, g=0.35, pan=0.4)
sfx(coin(), W("L05", "forty"), g=0.18)
sfx(blip(500, 800, d=0.12), T("L06") + 0.3, g=0.2)
sfx(blip(400, 1200, d=0.12), W("L06", "large"), g=0.2)
sfx(glitch(0.22), W("L06", "no") - 0.05, g=0.22)
sfx(impact(0.35), W("L06", "no"), g=0.25)
sfx(whoosh(0.4, 300, 4000, rev=True), W("L07", "you") - 0.4, g=0.25)
sfx(impact(0.4), W("L07", "you"), g=0.25)
sfx(whoosh(0.3, 3000, 500), T("L08") - 0.1, g=0.2)
sfx(kick(big=True), W("L08", "stays"), g=0.3); sfx(tick(), W("L08", "stays") + 0.03, g=0.3)
sfx(bell(76, d=0.8), T("L09"), g=0.12)
sfx(blip(600, 900, d=0.1), W("L09", "haircut"), g=0.2, pan=-0.4)
sfx(tick(), W("L09", "or"), g=0.3)
sfx(blip(700, 1000, d=0.1), W("L09", "takeout") - 0.2, g=0.2, pan=0.4)
sfx(coin(), T("L10"), g=0.15)
sfx(impact(0.5), W("L11", "one"), g=0.2)
sfx(bell(84, d=0.9), T("L11", part="end") + 0.2, g=0.1)

mix.write("soundtrack.wav", reverb=0.05, fade=0.4)
