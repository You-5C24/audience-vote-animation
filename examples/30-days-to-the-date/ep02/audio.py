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

# ---- sfx (Day 2)
def sfx(sig, t, **k):
    if t == t: mix.add(sig, t, **k)   # NaN != NaN -> skipped
sfx(coin(), W("L01", "haircut"), g=0.2)
for i in range(9):                     # scissor snips while the barber works
    tt = T("L02") + 0.4 + i * 0.85
    if tt < W("L04", "look") - 0.3: sfx(tick(), tt, g=0.3, pan=-0.3 + 0.15 * (i % 4)); sfx(blip(2400, 1800, d=0.05, decay=40), tt + 0.03, g=0.12)
sfx(blip(500, 900, d=0.12), W("L03", "two"), g=0.18)
sfx(blip(600, 1000, d=0.12), W("L03", "three"), g=0.18)
sfx(blip(900, 2200, d=0.35, decay=8), W("L03", "bird"), g=0.25, pan=0.4)   # the bird
sfx(whoosh(0.5, 400, 5000, rev=True), W("L04", "look") - 0.65, g=0.3)
sfx(impact(0.5), W("L04", "look") - 0.15, g=0.3)
for n in [72, 76, 79, 84]: sfx(bell(n, d=0.9), W("L04", "look") - 0.1, g=0.08)
sfx(blip(1300, 1700, d=0.07, decay=30), W("L05", "who"), g=0.22)
sfx(blip(1300, 1700, d=0.07, decay=30), W("L06", "lily"), g=0.22)
sfx(glitch(0.2), W("L06", "cook"), g=0.15)
for i in range(7): sfx(tick(), T("L07") + i * 0.07, g=0.3, pan=0.4)
sfx(coin(), W("L07", "forty"), g=0.16)
sfx(bell(76, d=0.8), T("L08"), g=0.12)
sfx(blip(600, 900, d=0.1), W("L08", "throw"), g=0.2, pan=-0.4)
sfx(tick(), W("L08", "or"), g=0.3)
sfx(blip(700, 1000, d=0.1), W("L08", "learn"), g=0.2, pan=0.4)
sfx(coin(), T("L09"), g=0.15)
sfx(impact(0.4), W("L10", "to"), g=0.18)
sfx(bell(84, d=0.9), T("L10", part="end") + 0.2, g=0.1)

mix.write("soundtrack.wav", reverb=0.05, fade=0.4)
