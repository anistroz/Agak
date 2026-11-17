"""The "new version" notice: the version here is read from .git, GitHub is asked what is newer (a stand-in here,
so nothing leaves this machine), and only the owner is told."""
import json, os, sys, tempfile
from pathlib import Path
os.environ["CLIPKONTRAST_DATA"] = tempfile.mkdtemp(prefix="pc-upd-")
os.environ.update(CLIPKONTRAST_UPDATE_CHECK="1", DATABASE_URL="", CLIPKONTRAST_ACCOUNTS="0", CLIPKONTRAST_PUBLIC_URL="http://127.0.0.1:8765", CLIPKONTRAST_AI_KEY="", CLIPKONTRAST_AI_MODELS="")
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from studio import config, db, server, updates
db.init()
fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

# ---- which version is running: straight from .git, in each of the ways git keeps it
real_root = config.ROOT
fake = Path(tempfile.mkdtemp(prefix="pc-git-"))
config.ROOT = fake
check("no .git (a downloaded zip): the version is unknown", updates.current(), "")
(fake / ".git" / "refs" / "heads").mkdir(parents=True)
(fake / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
(fake / ".git" / "refs" / "heads" / "main").write_text("a" * 40 + "\n")
check("the branch's commit is read", updates.current(), "a" * 40)
(fake / ".git" / "refs" / "heads" / "main").unlink()
(fake / ".git" / "packed-refs").write_text("# pack-refs with: peeled\n" + "b" * 40 + " refs/heads/main\n")
check("...also when git has packed it away", updates.current(), "b" * 40)
(fake / ".git" / "HEAD").write_text("c" * 40 + "\n")
check("...and on a single commit", updates.current(), "c" * 40)
config.ROOT = real_root
check("this folder's own version is found", len(updates.current()), 40)

# ---- asking GitHub: one small question a minute, and the list of changes only when something is new
class R:
    def __init__(self, code, data=None, content=b""):
        self.status_code, self._d, self.content = code, data, content
    def json(self):
        return self._d
asked = []
gh = {"top": "", "refs_code": 200, "compare": None}
def refs(sha):
    return (b"001e# service=git-upload-pack\n0000015b" + sha.encode() + b" HEAD\x00multi_ack thin-pack\n003f"
            + sha.encode() + b" refs/heads/main\n0000")
def fake_get(url, timeout=None, headers=None, params=None):
    asked.append(url)
    if url.endswith("/info/refs"):
        return R(gh["refs_code"], content=refs(gh["top"]) if gh["top"] else b"")
    return gh["compare"] or R(403, {"message": "rate limit"})
updates.httpx.get = fake_get
here = updates.RUNNING
check("the version ClipKontrast started on is remembered", len(here), 40)
NEWER, NEWEST = "1" * 40, "2" * 40
two = R(200, {"ahead_by": 2, "commits": [
    {"sha": "aaaaaaa1", "commit": {"message": "Connect TikTok in one click\n\nlong text", "committer": {"date": "2026-11-15T10:00:00Z"}}},
    {"sha": NEWER, "commit": {"message": "Captions always in English", "committer": {"date": "2026-11-16T10:00:00Z"}}}]})

gh.update(top=here)
check("up to date: no notice", updates.check(force=True), None)
check("...and only the one small question was asked", [u.split("/")[-1] for u in asked], ["refs"])
check("it goes to the address git itself uses, not the API", asked[0], f"https://github.com/{updates.REPO}.git/info/refs")

asked.clear(); gh.update(top=NEWER, compare=two)
got = updates.check(force=True)
check("a new commit is noticed while ClipKontrast is running, with no restart", (got["behind"], got["latest"], got["current"], got["restart"]), (2, "1111111", here[:7], False))
check("newest change first, one line each, with its date", [(n["title"], n["date"]) for n in got["notes"]],
      [("Captions always in English", "2026-11-16"), ("Connect TikTok in one click", "2026-11-15")])
asked.clear()
for _ in range(5):
    updates.check(force=True)
check("the list of changes is asked for once per new commit, not every minute", sum("api.github.com" in u for u in asked), 0)
check("a look inside the same minute asks nothing at all", (asked.clear(), updates.check(), len(asked))[1:], (got, 0))

asked.clear(); gh.update(top=NEWEST, compare=None)
got = updates.check(force=True)
check("when the API will not say what changed, the notice still shows", (got["latest"], got["behind"], got["notes"]), ("2222222", None, []))

real_current = updates.current
updates.current = lambda: NEWEST                      # git pull was run: the folder has the new files
gh.update(compare=two)
updates._state["notes"] = None
got = updates.check(force=True)
check("after git pull, the notice asks for a restart instead", got["restart"], True)
updates.current = real_current

gh.update(compare=R(200, {"ahead_by": 0, "commits": []}), top="3" * 40)
check("a copy with its own newer commits is not told to update", updates.check(force=True), None)
gh.update(refs_code=404, top=NEWER)
check("a private or unknown repository: no notice, no error", updates.check(force=True), None)
gh.update(refs_code=200, top=NEWER, compare=two)
shown = updates.check(force=True)
def boom(*a, **k):
    raise OSError("offline")
updates.httpx.get = boom
check("offline for a moment: the notice stays, no error", updates.check(force=True), shown)

# ---- only the owner is told
updates.httpx.get = fake_get
c = TestClient(server.app, base_url="http://127.0.0.1:8765")
st = c.get("/api/status").json()
check("the owner's dashboard gets the notice", (st["update"] or {}).get("behind"), 2)
updates.ON = False
check("CLIPKONTRAST_UPDATE_CHECK=0: never asks, never tells", (updates.check(force=True), c.get("/api/status").json()["update"]), (None, None))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; db.engine.dispose(); shutil.rmtree(os.environ["CLIPKONTRAST_DATA"], ignore_errors=True); shutil.rmtree(fake, ignore_errors=True)
sys.exit(1 if fails else 0)
