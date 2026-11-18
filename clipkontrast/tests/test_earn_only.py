"""The Earn-only website: clip-making is off for everyone but admins. Starts its own server.
Usage: test_earn_only.py <project root>"""
import os, subprocess, sys, tempfile, time, urllib.request
import httpx
ROOT = sys.argv[1]
PORT = 8798
BASE = f"http://127.0.0.1:{PORT}"
ORIGIN = {"Origin": BASE}
fails = []


def check(name, got, want):
    ok = got == want if not callable(want) else want(got)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   got {got!r}"))
    if not ok:
        fails.append(name)


data = tempfile.mkdtemp(prefix="ck-earnonly-")
env = {**os.environ, "CLIPKONTRAST_DATA": data, "CLIPKONTRAST_PORT": str(PORT), "CLIPKONTRAST_PUBLIC_URL": BASE, "DATABASE_URL": "",
       "CLIPKONTRAST_ACCOUNTS": "1", "CLIPKONTRAST_EARN_ONLY": "1", "CLIPKONTRAST_VERIFY_EMAIL": "0", "CLIPKONTRAST_FETCH_MODEL": "0",
       "CLIPKONTRAST_UPDATE_CHECK": "0", "CLIPKONTRAST_AUTO_RELOAD": "0", "CLIPKONTRAST_DOWNLOAD_URL": "https://example.com/dl.zip"}
srv = subprocess.Popen([sys.executable, "-m", "studio.server"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/healthz", timeout=2); break
        except Exception:
            time.sleep(1)
    c = httpx.Client(base_url=BASE, timeout=30)
    r = c.post("/api/auth/signup", json={"email": "u@example.com", "password": "test-pass-123"}, headers=ORIGIN)
    check("sign up works", r.status_code, 200)
    check("/app sends clippers to Earn", (c.get("/app").status_code, c.get("/app").headers.get("location")), (303, "/earn#me"))
    check("starting a video is refused", c.post("/api/jobs", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, headers=ORIGIN).status_code, 403)
    check("uploading is refused", c.post("/api/upload/start", json={"name": "a.mp4", "size": 10}, headers=ORIGIN).status_code, 403)
    check("adding a creator is refused", c.post("/api/creators", json={"name": "x", "channel": "https://www.youtube.com/@x"}, headers=ORIGIN).status_code, 403)
    check("changing settings is refused", c.put("/api/settings", json={"discord_webhook": ""}, headers=ORIGIN).status_code, 403)
    check("test alerts are refused", c.post("/api/alerts/test", headers=ORIGIN).status_code, 403)
    check("marking notifications read still works", c.post("/api/notifications/read", json={}, headers=ORIGIN).status_code in (200, 204), True)
    check("Earn still works", c.put("/api/earn/profile", json={"upi": "ab@okaxis", "whatsapp": "9876543210", "x": "@a"}, headers=ORIGIN).status_code, 200)
    p = c.get("/api/public").json()
    check("public settings say Earn-only", (p["earn_only"], p["download_url"]), (True, "https://example.com/dl.zip"))
    check("landing carries the download link", "https://example.com/dl.zip" in c.get("/").text, True)
    subprocess.run([sys.executable, "-m", "studio.admin", "grant", "u@example.com"], cwd=ROOT, env=env, capture_output=True)
    c2 = httpx.Client(base_url=BASE, timeout=30)
    c2.post("/api/auth/login", json={"email": "u@example.com", "password": "test-pass-123"}, headers=ORIGIN)
    check("admins can still open the clip studio", c2.get("/app").status_code, 200)
finally:
    srv.terminate()
print("ALL PASSED" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
