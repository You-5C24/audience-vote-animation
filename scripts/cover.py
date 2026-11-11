"""Cover for one episode — designed, not sampled from the video.

  python cover.py EP                      -> EP/cover.png (1080x1920) + EP/cover_4x5.png
  python cover.py EP --t 41.5             -> base the artwork on the frame at t seconds
  python cover.py EP --no-video           -> artwork only, no still behind it

Design rules (same for every episode, so a grid of covers reads as one series):
  top-left    the serial stamp: 第 N 天 / 30
  middle      the artwork, and one object that makes the current state legible
  bottom      one line about his state right now — never a plot summary
  top-right   FIXED count once the first fix lands
The episodes look different because the line and the object change, not the template.
"""
import argparse, functools, http.server, json, os, socketserver, subprocess, sys, threading
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
ART_H = 1010          # where the artwork stops and the cream card begins
RED, INK, CREAM, WHITE = (232, 71, 58), (27, 27, 31), (232, 226, 212), (255, 255, 255)
YELLOW = (255, 210, 63)


def font(size, bold=True):
    """A CJK-capable font. PingFang ships with macOS; the rest are fallbacks for other machines."""
    cands = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 0),
    ]
    for path, idx in cands:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                if bold: return f
                return ImageFont.truetype(path, size, index=min(idx + 1, 20))
            except Exception:
                continue
    return ImageFont.load_default()


def load_line(ep, series):
    """The bottom line: <EP>/cover.txt if it exists, else series.json cover.<day>, else hero+day."""
    p = os.path.join(ep, "cover.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip().splitlines()[0]
    st = json.load(open(os.path.join(ep, "state.json"), encoding="utf-8"))
    covers = series.get("cover", {})
    line = covers.get(str(st.get("day", 1))) or covers.get("default")
    if line: return line.replace("{hero}", series.get("hero", "他"))
    return f"{series.get('hero', '他')}，{st.get('day', 1)} 岁。"


def _tokens(text):
    text = text.replace(" ", "")
    toks, buf = [], ""
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch in ".-%"):
            buf += ch
        else:
            if buf: toks.append(buf); buf = ""
            toks.append(ch)
    if buf: toks.append(buf)
    return toks


PUNCT = "，。！？、；：,.;"


def fit_lines(draw, text, fnt, max_w, max_lines=3):
    """Break a Chinese line the way a designer would: at punctuation first, then balanced.
    Greedy width filling produces orphans like 「…还住在小时 / 候的房间」; a comma break
    gives 「29岁，/ 还住在小时候的房间」, which reads correctly."""
    toks = _tokens(text)
    def width(ls): return [draw.textlength(l, font=fnt) for l in ls]
    def ok(ls): return max(width(ls)) <= max_w

    # candidate break indices: after a punctuation mark, then any position as fallback
    punct_idx = [i + 1 for i, t in enumerate(toks) if t in PUNCT]

    def split_at(idx):
        out, prev = [], 0
        for i in idx:
            out.append("".join(toks[prev:i])); prev = i
        out.append("".join(toks[prev:]))
        return out

    best = None
    # 1) one break at punctuation
    for i in punct_idx:
        ls = split_at([i])
        if len(ls) <= max_lines and ok(ls):
            spread = max(width(ls)) - min(width(ls))
            if best is None or spread < best[0]: best = (spread, ls)
    if best: return best[1]
    # 2) balanced greedy, only among layouts that fit
    cands = []
    for k in range(1, max_lines + 1):
        out, cur = [], ""
        for i, tk in enumerate(toks):
            if len(out) == k - 1: cur += tk; continue
            if draw.textlength(cur + tk, font=fnt) <= max_w: cur += tk
            else: out.append(cur); cur = tk
        out.append(cur)
        if ok(out):
            cands.append((len(out), max(width(out)) - min(width(out)), out))
    cands.sort(key=lambda c: (c[0], c[1]))
    return cands[0][2] if cands else [text]


def grab(ep, t, port=8853):
    """One frame of the artwork with the HUD and captions switched off (?cover=1)."""
    from playwright.sync_api import sync_playwright
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ep)
    h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = os.path.join("/tmp", "_cover_art.png")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome", headless=True)
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto(f"http://127.0.0.1:{port}/index.html?cover=1")
            pg.wait_for_function("window.READY === true", timeout=60000)
            pg.evaluate(f"window.renderAt({t})")
            pg.locator("canvas").screenshot(path=out)
            b.close()
    finally:
        srv.shutdown()
    if os.path.exists(out):
        return Image.open(out).convert("RGB")
    return None


def build(ep, t=None, still_bg=True):
    series = {}
    sp = os.path.join(os.path.dirname(ep), "series.json")
    if os.path.exists(sp):
        series = json.load(open(sp, encoding="utf-8"))
    st = json.load(open(os.path.join(ep, "state.json"), encoding="utf-8"))
    day, days = st.get("day", 1), st.get("days", 30)
    fixed = st.get("fixed", [])
    line = load_line(ep, series)

    # ---- base: the artwork, dimmed so the type owns the frame
    canvas = Image.new("RGB", (W, H), CREAM)
    if still_bg and t is not None:
        name = "".join(c for c in series.get("title", "episode") if c.isalnum())
        mp4 = os.path.join(ep, f"{name}_Day{day}.mp4")
        src = mp4 if os.path.exists(mp4) else None
        tmp = os.path.join("/tmp", "_cover_frame.png")
        shot = grab(ep, t)
        if shot: canvas = shot

    img = canvas.copy()
    d = ImageDraw.Draw(img, "RGBA")

    # ---- full-bleed artwork with a legibility scrim at the bottom.
    # No card, no rule: the drawing carries the frame and one line of type sits on it.
    d.rectangle([0, 0, W, H], fill=(16, 16, 20, 30))
    scrim = Image.new("RGBA", (W, 620), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(620):
        a = int(210 * (y / 620) ** 1.25)
        sd.rectangle([0, y, W, y + 1], fill=(12, 12, 16, a))
    base = img.convert("RGBA")
    base.alpha_composite(scrim.convert("RGBA"), (0, H - 620))
    img = base.convert("RGB")
    d = ImageDraw.Draw(img)

    # ---- top-left: serial stamp
    fb = font(72)
    stamp = f"第 {day} 天"
    bw = d.textlength(stamp, font=fb) + 84
    d.rounded_rectangle([48, 52, 48 + bw, 176], 62, fill=INK)
    d.text((48 + 42, 114), stamp, font=fb, fill=YELLOW, anchor="lm")
    d.text((48 + bw + 22, 114), f"/ {days}", font=font(54), fill=WHITE, anchor="lm")

    # ---- top-right: how many things are already fixed
    if fixed:
        fr = f"已改 {len(fixed)}"
        ff = font(44)
        w2 = d.textlength(fr, font=ff) + 60
        d.rounded_rectangle([W - 48 - w2, 70, W - 48, 158], 44, fill=RED)
        d.text((W - 48 - w2 / 2, 114), fr, font=ff, fill=WHITE, anchor="mm")

    # ---- the line: bottom-left, large, two lines max, with the day stamp above it
    fl = font(100)
    lines = fit_lines(d, line, fl, W - 176, max_lines=2)
    y = H - 230 - (len(lines) - 1) * 124
    for ln in lines:
        d.text((74, y), ln, font=fl, fill=WHITE, anchor="la")
        y += 128

    os.makedirs(ep, exist_ok=True)
    out1 = os.path.join(ep, "cover.png")
    out2 = os.path.join(ep, "cover_4x5.png")
    img.save(out1)
    _45 = img.crop((0, 0, W, 1350))         # keep the stamp and the artwork; 4:5 for the profile grid
    _45.save(out2)
    print("cover ->", out1)
    print("cover ->", out2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("--t", type=float, default=41.5)
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    build(os.path.abspath(a.ep), a.t, not a.no_video)


if __name__ == "__main__":
    main()
