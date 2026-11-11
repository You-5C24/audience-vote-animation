"""Next episode from yesterday's vote.

  python new_episode.py SERIES 2 --winner HAIRCUT      ep02 = ep01's state + the HAIRCUT fix
  python new_episode.py SERIES 5 --winner "comment: take a shower" --set '{"shower": true}' --ready 3
                                                      a top-comment fix that is not in fixes.json

What it does
  - state.json = previous state + the winner's 'set' fields, ready += gain, day = N, fixed += [winner]
    and 'before' = the old values of the changed fields (the engine draws them until FIX_AT)
  - copies the previous episode's index.html and audio.py (rewrite the SCENES part for the new story)
  - writes a script.json skeleton: result -> fix -> new problem -> vote -> comment -> end
"""
import argparse, json, os, shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("series"); ap.add_argument("n", type=int); ap.add_argument("--winner", required=True)
    ap.add_argument("--set", dest="setj"); ap.add_argument("--ready", type=int)
    a = ap.parse_args(); s = os.path.abspath(a.series)
    prev = os.path.join(s, f"ep{a.n - 1:02d}"); ep = os.path.join(s, f"ep{a.n:02d}")
    if not os.path.exists(os.path.join(prev, "state.json")): raise SystemExit(f"x no {prev}/state.json")
    if os.path.exists(ep): raise SystemExit(f"x {ep} already exists")
    fixes = json.load(open(os.path.join(s, "fixes.json"), encoding="utf-8"))
    st = json.load(open(os.path.join(prev, "state.json"), encoding="utf-8")); st.pop("before", None)
    key = a.winner.upper()
    if a.setj: fx = {"set": json.loads(a.setj), "ready": a.ready or 3}
    elif key in fixes: fx = fixes[key]
    else: raise SystemExit(f"x {key} not in fixes.json; add it there, or pass --set '{{...}}' --ready N")
    if key in st.get("fixed", []): raise SystemExit(f"x {key} was already fixed on an earlier day (fixed stays fixed)")
    before = {k: st.get(k) for k in fx["set"]}; before["ready"] = st.get("ready", 0)
    st.update(fx["set"]); st["ready"] = min(100, st.get("ready", 0) + fx.get("ready", 3))
    st["day"] = a.n; st["fixed"] = st.get("fixed", []) + [key]; st["before"] = before
    ser = os.path.join(s, "series.json")
    if os.path.exists(ser):
        serj = json.load(open(ser, encoding="utf-8"))
        st["lang"] = serj.get("lang", "en"); st["days"] = serj.get("days", st.get("days", 30))
        st["meter"] = serj.get("meter", st.get("meter"))
    os.makedirs(ep)
    json.dump(st, open(os.path.join(ep, "state.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for f in ("index.html", "audio.py"): shutil.copy(os.path.join(prev, f), ep)
    days_left = st.get("days", 30) - a.n + 1
    skel = {"lead": 0.5, "lines": [
        {"id": "L01", "scene": "result", "text": f"Day {a.n}. You picked {key.lower()}.", "gap": 0.35},
        {"id": "L02", "scene": "fix", "text": "(how the fix goes, one joke: why it is hard for him)", "gap": 0.4},
        {"id": "L03", "scene": "fix", "text": "(the moment it is done - set FIX_AT to a word in this line)", "gap": 0.4},
        {"id": "L04", "scene": "story", "text": "(a new problem, or a text from Mom / the date)", "gap": 0.45},
        {"id": "L05", "scene": "vote", "text": f"Day {a.n + 1}. (OPTION A), or (OPTION B)?", "gap": 0.5},
        {"id": "L06", "scene": "comment", "text": "Comment one word. The winner gets fixed tomorrow.", "gap": 0.45},
        {"id": "L07", "scene": "end", "text": f"{days_left} days to go.", "gap": 1.0}]}
    json.dump(skel, open(os.path.join(ep, "script.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ep{a.n:02d} -> {ep}\n  fixed: {st['fixed']}\n  ready: {before['ready']}% -> {st['ready']}%\n  before: {before}")


if __name__ == "__main__":
    main()
