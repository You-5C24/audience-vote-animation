"""Start a series folder.

  python new_series.py SERIES                 empty series from templates (ep01 = the engine + a starter script)
  python new_series.py SERIES --from-example  copy the 30 Days to the Date example (ep01 renders straight away)

Checks: ffmpeg, Python playwright + Chrome, numpy/scipy/pillow, faster-whisper, edge-tts.
"""
import argparse, importlib, json, os, shutil, subprocess

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check():
    ok = True
    for mod in ("numpy", "scipy", "PIL", "playwright", "faster_whisper", "edge_tts"):
        try: importlib.import_module(mod); print("  ok  ", mod)
        except Exception: ok = False; print("  MISSING", mod, "-> pip install", {"PIL": "pillow", "faster_whisper": "faster-whisper", "edge_tts": "edge-tts"}.get(mod, mod))
    try: subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True); print("  ok   ffmpeg")
    except Exception: ok = False; print("  MISSING ffmpeg (on PATH)")
    return ok


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("series"); ap.add_argument("--from-example", action="store_true")
    a = ap.parse_args(); s = os.path.abspath(a.series)
    if os.path.exists(os.path.join(s, "series.json")): raise SystemExit(f"x {s} already has a series.json")
    os.makedirs(s, exist_ok=True)
    if a.from_example:
        src = os.path.join(SK, "examples", "30-days-to-the-date")
        shutil.copytree(src, s, dirs_exist_ok=True)
    else:
        for f in ("series.json", "fixes.json"): shutil.copy(os.path.join(SK, "templates", f), s)
        ep = os.path.join(s, "ep01"); os.makedirs(ep, exist_ok=True)
        shutil.copy(os.path.join(SK, "engine", "index.html"), ep)
        shutil.copy(os.path.join(SK, "templates", "audio.py"), ep)
        shutil.copy(os.path.join(SK, "templates", "state.json"), ep)
        shutil.copy(os.path.join(SK, "examples", "30-days-to-the-date", "ep01", "script.json"), ep)
    open(os.path.join(s, "log.md"), "a", encoding="utf-8").write("# Episode log\n\n| Day | Vote | Winner | Posted | Views | Comments |\n| --- | --- | --- | --- | --- | --- |\n")
    print("series ->", s); check()


if __name__ == "__main__":
    main()
