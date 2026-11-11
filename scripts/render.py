"""Render one episode (EP = episode folder with index.html, timeline.json, mouth.json, state.json, audio.py).

  python render.py EP stills 0.5,3,8.2     still frames -> EP/stills/ + EP/stills/sheet.png (look at it!)
  python render.py EP frames [--from N]    every frame (30 fps, 1080x1920) -> EP/frames/
  python render.py EP audio                run EP/audio.py -> EP/soundtrack.wav (voice + music + sfx)
  python render.py EP encode               frames + soundtrack -> EP/<name>.mp4 (-14 LUFS) + cover jpg
  python render.py EP all                  frames + audio + encode
Needs: Python playwright + installed Chrome (or Edge: --channel msedge), ffmpeg, numpy, scipy, pillow.
"""
import argparse, functools, glob, http.server, json, os, runpy, shutil, socketserver, subprocess, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30


def serve(root, port):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def capture(ep, times=None, start=0, channel="chrome"):
    from playwright.sync_api import sync_playwright
    port = 8790 + (os.getpid() % 100)
    srv = serve(ep, port)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=channel, headless=True)
            pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            pg.on("pageerror", lambda e: print("pageerror:", e))
            pg.goto(f"http://127.0.0.1:{port}/index.html")
            pg.wait_for_function("window.READY === true", timeout=60000)
            dur = pg.evaluate("window.DUR")
            if times is not None:
                os.makedirs(os.path.join(ep, "stills"), exist_ok=True)
                for t in times:
                    pg.evaluate(f"window.renderAt({t})")
                    pg.locator("canvas").screenshot(path=os.path.join(ep, "stills", f"t{t:06.2f}.png"))
            else:
                out = os.path.join(ep, "frames"); os.makedirs(out, exist_ok=True)
                n = int(FPS * dur)
                for i in range(start, n):
                    pg.evaluate(f"window.renderAt({i / FPS})")
                    pg.locator("canvas").screenshot(path=os.path.join(out, f"{i:05d}.png"))
                    if i % 150 == 0: print(f"frame {i}/{n}", flush=True)
            b.close()
    finally:
        srv.shutdown()


def sheet(ep):
    from PIL import Image
    fs = sorted(glob.glob(os.path.join(ep, "stills", "t*.png")))
    if not fs: return
    ims = [Image.open(f).resize((270, 480)) for f in fs]
    cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (270 * cols, 480 * rows), "white")
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * 270, (i // cols) * 480))
    s.save(os.path.join(ep, "stills", "sheet.png")); print("sheet ->", os.path.join(ep, "stills", "sheet.png"))


def audio(ep):
    sys.path.insert(0, HERE); cwd = os.getcwd(); os.chdir(ep)
    try: runpy.run_path(os.path.join(ep, "audio.py"), run_name="__main__")
    finally: os.chdir(cwd)


def name_of(ep):
    s = os.path.join(os.path.dirname(ep), "series.json"); st = os.path.join(ep, "state.json")
    title = json.load(open(s, encoding="utf-8")).get("title", "episode") if os.path.exists(s) else "episode"
    day = json.load(open(st, encoding="utf-8")).get("day", 1) if os.path.exists(st) else 1
    return "".join(c for c in title if c.isalnum()) + f"_Day{day}"


def encode(ep):
    name = name_of(ep); mp4 = os.path.join(ep, name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(ep, "frames", "%05d.png"),
                    "-i", os.path.join(ep, "soundtrack.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-shortest", "-movflags", "+faststart", mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", mp4, "-frames:v", "1", os.path.join(ep, name + "_cover.jpg")], check=True)
    print("ok ->", mp4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("cmd", choices=["stills", "frames", "audio", "encode", "all"])
    ap.add_argument("times", nargs="?"); ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--channel", default="chrome")
    a = ap.parse_args(); ep = os.path.abspath(a.ep)
    if a.cmd == "stills":
        shutil.rmtree(os.path.join(ep, "stills"), ignore_errors=True)
        capture(ep, [float(x) for x in (a.times or "1,5,10").split(",")], channel=a.channel); sheet(ep)
    if a.cmd in ("frames", "all"):
        if a.start == 0: shutil.rmtree(os.path.join(ep, "frames"), ignore_errors=True)
        capture(ep, start=a.start, channel=a.channel)
    if a.cmd in ("audio", "all"): audio(ep)
    if a.cmd in ("encode", "all"): encode(ep)


if __name__ == "__main__":
    main()
