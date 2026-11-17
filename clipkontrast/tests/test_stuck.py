"""Two things people hit: captions in another language drawn on top of each other, and one clip that hangs
keeping the whole video "in progress". Runs against the code directly, with its own empty data folder."""
import os, re, sys, tempfile, threading, time
os.environ["CLIPKONTRAST_DATA"] = tempfile.mkdtemp(prefix="pc-stuck-"); os.environ["DATABASE_URL"] = ""; os.environ["CLIPKONTRAST_CLIP_MINUTES"] = "0.03"
sys.path.insert(0, ".")
from concurrent.futures import ThreadPoolExecutor
from studio import brain, jobs, render, roman
fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)
def ws(text, gap=0.5):
    return [{"w": w, "s": i * gap, "e": i * gap + 0.4} for i, w in enumerate(text.split())]
def events(ass):
    out = []
    for l in ass.splitlines():
        m = re.match(r"Dialogue: \d+,(\d):(\d\d):(\d\d\.\d\d),(\d):(\d\d):(\d\d\.\d\d),Cap,", l)
        if m:
            a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]); b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
            out.append((a, b, l))
    return out

# ---- letters the caption fonts do not have
check("Russian-style letters are spelled in Roman letters", roman.to_roman("Привет, Москва"), "Privet, Moskva")
check("Greek too", roman.to_roman("Ελλάδα"), "Ellada")
check("Korean too", roman.to_roman("안녕하세요"), "annyeonghaseyo")
check("accented Latin letters are left alone and can be drawn", (roman.to_roman("niño été"), roman.drawable("niño été")), ("niño été", True))
check("Japanese cannot be drawn by the caption fonts", roman.drawable("こんにちは"), False)

ass = render.build_ass(ws("こんにちは 世界 今日は いい 天気 です"), 0, 6, "HOOK", "bounce", [], 300, 1380)
cap = events(ass)
check("a script the font lacks is drawn as whole centred lines, not word by word", all("\\q0" in l and "\\pos(540," in l for _, _, l in cap) and len(cap) >= 2)
check("...one line at a time, never two at once", all(cap[i][1] <= cap[i + 1][0] + 0.011 for i in range(len(cap) - 1)))

# ---- words whose times run into each other (a translation squeezed into a short line, a doubled transcript)
messy = [{"w": "one", "s": 0.0, "e": 2.5}, {"w": "two", "s": 0.3, "e": 2.6}, {"w": "three", "s": 0.6, "e": 2.7},
         {"w": "four", "s": 0.5, "e": 3.0}, {"w": "five", "s": 1.4, "e": 1.2}, {"w": "six", "s": 1.6, "e": 4.0}]
cap = events(render.build_ass(messy, 0, 5, "", "bounce", [], 300, 1380))
def shown_together(evs):
    """The most different caption groups (rows of words) on screen at any moment."""
    worst = 0
    for t in [a + 0.001 for a, _, _ in evs]:
        live = {re.search(r"\\pos\(\d+,(\d+)\)", l)[1] + "|" + str(round(min(a2 for a2, b2, l2 in evs if l2.split("}")[-1] == l.split("}")[-1]), 2))
                for a, b, l in evs if a <= t < b}
        words = {l.split("}")[-1] for a, b, l in evs if a <= t < b}
        worst = max(worst, len(words))
    return worst
check("overlapping word times never put more than one caption group on screen", shown_together(cap) <= 3)
out = brain._spread("this is a much longer english line than the time it was said in", 10.0, 10.4)
check("a long translation stays inside its own line's time", out[0]["s"] == 10.0 and out[-1]["e"] <= 10.4 + 0.31 and all(out[i]["e"] <= out[i + 1]["s"] + 0.011 for i in range(len(out) - 1)))

# ---- the Hindi and Urdu rule is only given to the AI for those videos
seen = []
def fake_ai(prompt, schema=None, purpose=""):
    seen.append(prompt); return [w for w in prompt.split("Words (")[1].splitlines()[1:] and ["Hello", "there", "friend."]], "m", 5
brain.ask_ai = fake_ai
brain.fix_caption_words(ws("hello there friend"), "", "en")
check("an English video's captions are tidied without the Hindi rule", "Hinglish" in seen[-1], False)
brain.ask_ai = lambda prompt, schema=None, purpose="": (seen.append(prompt), (["jo", "usko", "laga"], "m", 5))[1]
brain.fix_caption_words(ws("जो उसको लगा"), "", "hi")
check("a Hindi video's captions get it", "Hinglish" in seen[-1], True)

# ---- one clip that hangs
job = {"id": "job-12345678", "dir": os.environ["CLIPKONTRAST_DATA"], "creator": None, "user": "u_test01", "clips": []}
jobs.save = lambda j: None
clips = [{"id": f"clip0{i}", "status": "rendering", "title": f"Clip {i}"} for i in range(1, 5)]
began, release = {}, threading.Event()
def make(clip):
    began[clip["id"]] = time.time()
    if clip["id"] == "clip02":
        release.wait(30)                     # this one hangs
    clip["status"] = "done"
pool = ThreadPoolExecutor(2)
futures = [(pool.submit(make, c), c) for c in clips]
t0 = time.time()
jobs._wait_for_clips(job, futures, began, 2)
took = time.time() - t0
check("the video stops waiting for a clip that hangs", took < 10)
check("the hung clip is marked as failed, with what to do", (clips[1]["status"], "re-make" in clips[1].get("error", "")), ("error", True))
check("every other clip is finished", [c["status"] for c in clips if c["id"] != "clip02"], ["done", "done", "done"])
release.set(); pool.shutdown(wait=True)

# ---- clips end when a sentence ends
def talk(sentences, start=0.0, pause=0.15, punct=True):
    """Words for some sentences, half a second a word."""
    out, t = [], start
    for s in sentences:
        parts = s.split()
        for i, w in enumerate(parts):
            out.append({"w": w + ("." if punct and i == len(parts) - 1 else ""), "s": round(t, 2), "e": round(t + 0.4, 2)})
            t += 0.5
        t += pause
    return out
sents = ["so this is how the whole thing started", "nobody believed me when I said it", "and then the door opened and everyone screamed",
         "that was the craziest moment of my life", "anyway let us move on to the next part of the video", "first we need to set things up"]
w = talk(sents)                                   # sentence ends near 3.9, 7.55, 11.7, 15.85, 21.5, 25.15
lines = brain.make_lines(w)
s, e = brain._snap({"start": 0.0, "end": 13.4}, lines, w, 5, 60, 30)      # the AI stopped in the middle of sentence 4
check("an end in the middle of a sentence is moved to the end of that sentence", 15.8 <= e <= 16.2)
s, e = brain._snap({"start": 0.0, "end": 15.9}, lines, w, 5, 60, 30)
check("an end already on a sentence end stays there", 15.8 <= e <= 16.2)
check("...with a breath after it, but not into the next sentence", e < 16.1)          # the next sentence starts at 16.1
s, e = brain._snap({"start": 0.0, "end": 13.4}, lines, w, 5, 14, 30)      # no room to finish it: the sentence before
check("with no room to finish the sentence, the clip ends at the one before", 11.6 <= e <= 12.1)
w2 = talk(sents, pause=0.9, punct=False)          # YouTube's transcript: no punctuation, pauses between sentences
ends2 = brain.sentence_ends(w2)
s, e = brain._snap({"start": 0.0, "end": 14.0}, brain.make_lines(w2), w2, 5, 60, 40)
check("without punctuation, a pause counts as the end of a sentence", any(abs(e - x) < 0.5 for x in ends2) and len(ends2) == 6)
import numpy as np
db = np.zeros(30); db[13] = 9.0
brain.ask_ai = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("The AI is not set up on this server."))
clips, info = brain.find_clips(w, db, 30.0, max_clips=1, min_len=8, max_len=14, log=lambda m: None)
ends = brain.sentence_ends(w)
check("with no AI, a clip picked by loudness still ends on a sentence end", len(clips) == 1 and any(0 <= clips[0]["end"] - x <= 0.4 for x in ends))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; shutil.rmtree(os.environ["CLIPKONTRAST_DATA"], ignore_errors=True)
sys.exit(1 if fails else 0)
