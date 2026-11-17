"""ClipKontrast's folder: said plainly when its drive is full, and movable. A move is chosen in the dashboard and done at
the next start, before anything is open. Uses its own temporary folders; nothing else is touched."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
base = Path(tempfile.mkdtemp(prefix="pc-stor-"))
old, new, pointer = base / "old-data", base / "bigger drive" / "ClipKontrast", base / "storage.json"
os.environ.pop("CLIPKONTRAST_DATA", None); os.environ.pop("CLIPKONTRAST_MODELS", None)
os.environ.update(DATABASE_URL="", CLIPKONTRAST_STORAGE_FILE=str(pointer), CLIPKONTRAST_ACCOUNTS="0", CLIPKONTRAST_PUBLIC_URL="http://127.0.0.1:8765")
pointer.write_text(json.dumps({"path": str(old)}))
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from studio import config, db, load, server, storage
db.init()
fails = []
def check(n, got, want=True):
    if isinstance(want, tuple) and any(callable(w) for w in want):
        ok = len(got) == len(want) and all(w(g) if callable(w) else g == w for g, w in zip(got, want))
    else:
        ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

check("the folder chosen in the dashboard is the one in use", (config.DATA_DIR, config.DATA_FROM), (old, "chosen"))
(old / "users" / "u_local" / "jobs" / "job1").mkdir(parents=True)
(old / "users" / "u_local" / "jobs" / "job1" / "clip01.mp4").write_bytes(b"v" * 5000)
c = TestClient(server.app, base_url="http://127.0.0.1:8765")
ORIGIN = {"Origin": "http://127.0.0.1:8765"}

# ---- what the Storage page shows
storage._used["at"] = 0
s = c.get("/api/storage").json()
check("it shows the folder, how much ClipKontrast uses, and the room on the drive", (s["path"], storage.used_bytes(), s["free_gb"] > 0, s["fixed"], s["pending"]),
      (str(old.resolve()), lambda n: n >= 5000, True, False, ""))
check("a folder window is only offered on the computer ClipKontrast runs on", (s["local"], c.post("/api/storage/open", headers=ORIGIN).status_code), (False, 400))

# ---- a full drive is explained, not just refused
load._state.update(disk_free=0.4, at=10 ** 12)
load._started = True
r = c.post("/api/jobs", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, headers=ORIGIN)
check("a full drive says which drive, how much is left, and what to do", (r.status_code, all(x in r.json()["detail"] for x in ("almost full", "GB free", "Settings, Storage"))), (507, True))
check("the dashboard is told too", c.get("/api/status").json()["disk_full"], True)
load._state.update(disk_free=99.0)

# ---- choosing another folder
put = lambda body: c.put("/api/storage", json=body, headers=ORIGIN)  # noqa: E731
check("no folder given", put({"path": ""}).status_code, 400)
check("not a whole path", put({"path": "videos"}).status_code, 400)
check("the same folder", put({"path": str(old)}).status_code, 400)
check("a folder inside the current one", put({"path": str(old / "inner")}).status_code, 400)
check("from another website", c.put("/api/storage", json={"path": str(new)}, headers={"Origin": "https://evil.example"}).status_code, 403)
r = put({"path": str(new), "move": True})
check("a good folder is accepted for the next start", (r.status_code, r.json()["pending"], r.json()["path"]), (200, str(new.resolve()), str(old.resolve())))
check("nothing is moved while ClipKontrast is running", (old / "users" / "u_local" / "jobs" / "job1" / "clip01.mp4").is_file() and not (new / "users").exists())
check("undo forgets the choice", (put({"cancel": True}).json()["pending"], json.loads(pointer.read_text())), ("", {"path": str(old.resolve())}))
put({"path": str(new), "move": True})
db.engine.dispose()

# ---- the next start: everything moves, then ClipKontrast carries on from the new folder
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
code = "from studio import config; print('USING', config.DATA_DIR)"
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
check("the next start uses the new folder", f"USING {new.resolve()}" in out.stdout)
check("the clips were moved there", (new / "users" / "u_local" / "jobs" / "job1" / "clip01.mp4").read_bytes() == b"v" * 5000)
check("the database went with them", (new / "clipkontrast.db").is_file())
check("nothing is left in the old place", not old.exists() or not any(old.iterdir()))
check("the move is done once", json.loads(pointer.read_text()), {"path": str(new.resolve())})
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
check("a later start changes nothing", ("Moving" in out.stdout, f"USING {new.resolve()}" in out.stdout), (False, True))

# ---- CLIPKONTRAST_DATA in .env wins, and then the dashboard cannot change it
out = subprocess.run([sys.executable, "-c", "from studio import config, storage\ntry:\n    storage.change(r'" + str(base / "x") + "')\nexcept ValueError as e:\n    print(config.DATA_FROM, '|', e)"],
                     capture_output=True, text=True, env={**env, "CLIPKONTRAST_DATA": str(base / "from-env")}, encoding="utf-8", errors="replace")
check("a folder set in .env is left to .env", out.stdout.startswith("env |") and ".env" in out.stdout)

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; shutil.rmtree(base, ignore_errors=True)
sys.exit(1 if fails else 0)
