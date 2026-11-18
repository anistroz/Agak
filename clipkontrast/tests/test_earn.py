"""Earn (paid clipping campaigns) against a throwaway ClipKontrast server. Usage: test_earn.py <base url> <project root> <python exe>"""
import io
import os
import subprocess
import sys
import time

import httpx

BASE, ROOT, PY = sys.argv[1], sys.argv[2], sys.argv[3]
ORIGIN = {"Origin": BASE}
fails = []


def check(name, got, want):
    ok = got == want if not callable(want) else want(got)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   got {got!r}"))
    if not ok:
        fails.append(name)


def client():
    return httpx.Client(base_url=BASE, timeout=30, follow_redirects=False)


def signup(email):
    c = client()
    r = c.post("/api/auth/signup", json={"email": email, "password": "test-pass-123", "name": email.split("@")[0]}, headers=ORIGIN)
    assert r.status_code == 200, r.text
    return c, r.json()["user"]


def py(code):
    return subprocess.run([PY, "-c", code], cwd=ROOT, env=os.environ, capture_output=True, text=True)


def x_id(when):          # an X post id made at a given time
    return str(int((when * 1000 - 1288834974657)) << 22)


def png(w=40, h=30):
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), (200, 240, 50)).save(b, "PNG")
    return b.getvalue()


anon = client()
boss, uboss = signup("earn-boss@example.com")
cl, ucl = signup("earn-clipper@example.com")
other, uother = signup("earn-other@example.com")
subprocess.run([PY, "-m", "studio.admin", "grant", "earn-boss@example.com"], cwd=ROOT, env=os.environ, capture_output=True, text=True)
for u in (uboss, ucl, uother):
    py(f"from studio import auth, db; db.init(); auth.mark_verified({u['id']!r})")

# ---- the public page and its numbers are open to everyone
check("anon can open /earn", anon.get("/earn").status_code, 200)
r = anon.get("/api/earn/public/overview")
check("anon can read the overview", r.status_code, 200)
check("no campaigns yet", r.json()["campaigns"], [])
check("anon cannot read /api/earn/me", anon.get("/api/earn/me").status_code, 401)

# ---- only admins can make campaigns
for who, c in (("anon", anon), ("clipper", cl)):
    check(f"{who} cannot open the Earn admin page", c.get("/admin/earn").status_code, 404)
    check(f"{who} cannot create a campaign", c.post("/api/admin/earn/campaigns", json={"title": "x"}, headers=ORIGIN).status_code, 404)
check("admin opens the Earn admin page", boss.get("/admin/earn").status_code, 200)
check("live without budget refused", boss.post("/api/admin/earn/campaigns", json={"title": "Bad", "status": "live"}, headers=ORIGIN).status_code, 400)
start = time.time() - 3600
r = boss.post("/api/admin/earn/campaigns", json={
    "title": "GTA 6 Launch", "creator_name": "Mizo", "tagline": "Clip the launch", "brief": "Clip GTA 6 streams.",
    "rules": "Hook in 2 seconds\nCredit the creator", "sources": "https://youtube.com/@creator/live",
    "platforms": ["youtube", "x", "tiktok", "instagram"], "required_tag": "@mizo", "rate_per_1k": 20, "min_views": 1000,
    "max_per_clip": 500, "budget": 1000, "hold_days": 7, "status": "live", "starts_at": start}, headers=ORIGIN)
check("admin creates a live campaign", r.status_code, 200)
camp = r.json()
check("slug made from the title", camp["slug"], "gta-6-launch")
r = boss.post("/api/admin/earn/campaigns", json={"title": "Secret draft", "rate_per_1k": 10, "budget": 100}, headers=ORIGIN)
draft = r.json()
check("drafts are hidden from the public", [c["title"] for c in anon.get("/api/earn/public/overview").json()["campaigns"]], ["GTA 6 Launch"])
check("a draft can't be opened by slug", anon.get(f"/api/earn/public/campaigns/{draft['slug']}").status_code, 400)
pub = anon.get(f"/api/earn/public/campaigns/{camp['slug']}").json()
check("public campaign has its budget", (pub["budget"], pub["remaining"], pub["open"]), (1000, 1000, True))
check("source links are for members only", "sources" in pub, False)
check("cover upload refuses junk", boss.post(f"/api/admin/earn/campaigns/{camp['id']}/cover", files={"file": ("a.png", b"not an image", "image/png")}, headers=ORIGIN).status_code, 400)
check("cover upload takes an image", boss.post(f"/api/admin/earn/campaigns/{camp['id']}/cover", files={"file": ("a.png", png(), "image/png")}, headers=ORIGIN).status_code, 200)
check("cover is served to anyone", anon.get(f"/earn/cover/{camp['id']}.jpg").headers.get("content-type"), "image/jpeg")

# ---- a clipper needs a profile before joining
check("join without profile refused", cl.post(f"/api/earn/campaigns/{camp['slug']}/join", headers=ORIGIN).status_code, 400)
check("bad UPI refused", cl.put("/api/earn/profile", json={"upi": "not a upi", "whatsapp": "9876543210"}, headers=ORIGIN).status_code, 400)
check("bad phone refused", cl.put("/api/earn/profile", json={"upi": "ravi@okaxis", "whatsapp": "123"}, headers=ORIGIN).status_code, 400)
r = cl.put("/api/earn/profile", json={"display_name": "Ravi <b>", "upi": "Ravi@OKAXIS", "whatsapp": "98765 43210",
                                      "x": "https://x.com/RaviClips", "tiktok": "@ravi.clips", "youtube": "youtube.com/@RaviShorts", "instagram": "@ravi_ig"}, headers=ORIGIN)
check("profile saved", r.status_code, 200)
p = r.json()
check("handles cleaned", (p["x"], p["tiktok"], p["youtube"], p["upi"], p["whatsapp"], p["display_name"]),
      ("@raviclips", "@ravi.clips", "@ravishorts", "ravi@okaxis", "+919876543210", "Ravi b"))
r = cl.post(f"/api/earn/campaigns/{camp['slug']}/join", headers=ORIGIN)
check("join works", r.status_code, 200)
check("members see the source links", r.json()["sources"], ["https://youtube.com/@creator/live"])

# ---- submitting links, and the cross-check
def submit(c, url, cid=None):
    return c.post("/api/earn/submissions", json={"campaign": cid or camp["id"], "url": url}, headers=ORIGIN)


now = time.time()
r = submit(cl, f"https://x.com/RaviClips/status/{x_id(now - 60)}?s=20")
check("X clip from own account accepted", r.status_code, 200)
s_x = r.json()
check("X: account matched automatically", s_x["checks"]["owner"], True)
check("X: posting time read from the id", s_x["checks"]["after_start"], True)
check("same clip twice refused", submit(cl, f"https://twitter.com/raviclips/status/{x_id(now - 60)}").status_code, 400)
r = submit(cl, f"https://x.com/someone_else/status/{x_id(now - 30)}")
check("X clip from someone else's account refused", (r.status_code, "isn't on the account" in r.text), (400, True))
r = submit(cl, f"https://x.com/RaviClips/status/{x_id(now - 86400 * 400)}")
check("clip posted before the campaign refused", (r.status_code, "before the campaign" in r.text), (400, True))
r = submit(cl, f"https://www.tiktok.com/@ravi.clips/video/{int(now - 100) << 32}")
check("TikTok clip accepted", r.status_code, 200)
r = submit(cl, "https://www.instagram.com/reel/C1abcDEFgh/?igsh=xyz")
check("Instagram reel accepted for manual check", r.status_code, 200)
s_ig = r.json()
check("Instagram: account checked by a person", s_ig["checks"]["owner"], None)
r = submit(cl, "https://youtube.com/shorts/dQw4w9WgXcQ?feature=share")
check("YouTube Short accepted (no API key: counted by hand)", r.status_code, 200)
s_yt = r.json()
check("bad link refused", submit(cl, "https://example.com/video").status_code, 400)
check("YouTube channel page refused", submit(cl, "https://youtube.com/@RaviShorts").status_code, 400)
check("other user can't submit without profile", submit(other, f"https://x.com/other/status/{x_id(now)}").status_code, 400)
check("unknown campaign refused", submit(cl, f"https://x.com/RaviClips/status/{x_id(now - 5)}", "nope").status_code, 400)

# ---- proof screenshots: only the owner (and admins) can add and see them
check("other user can't add proof", other.post(f"/api/earn/submissions/{s_ig['id']}/proof", files={"file": ("p.png", png(), "image/png")}, headers=ORIGIN).status_code, 400)
check("proof refuses junk", cl.post(f"/api/earn/submissions/{s_ig['id']}/proof", files={"file": ("p.png", b"<svg onload=alert(1)>", "image/png")}, headers=ORIGIN).status_code, 400)
check("owner adds a proof screenshot", cl.post(f"/api/earn/submissions/{s_ig['id']}/proof", files={"file": ("p.png", png(), "image/png")}, headers=ORIGIN).json()["has_proof"], True)
check("owner sees the proof", cl.get(f"/api/earn/proof/{s_ig['id']}").status_code, 200)
check("admin sees the proof", boss.get(f"/api/earn/proof/{s_ig['id']}").status_code, 200)
check("other user can't see the proof", other.get(f"/api/earn/proof/{s_ig['id']}").status_code, 400)
check("anon can't see the proof", anon.get(f"/api/earn/proof/{s_ig['id']}").status_code, 401)
check("other user can't withdraw someone's clip", other.delete(f"/api/earn/submissions/{s_yt['id']}", headers=ORIGIN).status_code, 400)

# ---- admin review: views, approve, budget, payouts
q = boss.get("/api/admin/earn/submissions?status=pending").json()
check("4 clips waiting for review", q["counts"]["pending"], 4)
check("review queue shows the clipper's UPI", q["items"][0]["clipper"]["upi"], "ravi@okaxis")
check("clipper can't review", cl.post(f"/api/admin/earn/submissions/{s_x['id']}", json={"action": "approve"}, headers=ORIGIN).status_code, 404)
r = boss.post(f"/api/admin/earn/submissions/{s_x['id']}", json={"action": "approve", "views": 12000}, headers=ORIGIN)
check("approve with 12,000 views = ₹240", (r.status_code, r.json().get("amount")), (200, 240.0))
check("approved views can't change", boss.post(f"/api/admin/earn/submissions/{s_x['id']}/views", json={"views": 99999}, headers=ORIGIN).status_code, 400)
r = boss.post(f"/api/admin/earn/submissions/{s_yt['id']}", json={"action": "approve", "views": 500}, headers=ORIGIN)
check("under the minimum views earns nothing", r.json()["amount"], 0)
r = boss.post(f"/api/admin/earn/submissions/{s_ig['id']}", json={"action": "approve", "views": 90000}, headers=ORIGIN)
check("capped at ₹500 per clip", r.json()["amount"], 500)
tt = [i for i in q["items"] if i["platform"] == "tiktok"][0]
r = boss.post(f"/api/admin/earn/submissions/{tt['id']}", json={"action": "approve", "views": 30000}, headers=ORIGIN)
check("last approval takes only what's left of the budget", r.json()["amount"], 260)
c2 = anon.get(f"/api/earn/public/campaigns/{camp['slug']}").json()
check("budget used up closes the campaign", (c2["remaining"], c2["status"], c2["open"]), (0, "ended", False))
check("no clips accepted after it closes", submit(cl, f"https://x.com/RaviClips/status/{x_id(time.time() - 5)}").status_code, 400)
check("leaderboard shows the clipper", c2["leaderboard"][0]["name"], "Ravi b")

me = cl.get("/api/earn/me").json()
check("clipper sees what's owed", me["totals"]["owed"], 1000)
owed = boss.get("/api/admin/earn/owed").json()["owed"]
check("admin sees one clipper owed ₹1,000", (len(owed), owed[0]["amount"], owed[0]["upi"]), (1, 1000, "ravi@okaxis"))
check("payout CSV downloads", "ravi@okaxis" in boss.get("/api/admin/earn/owed.csv").text, True)
r = boss.post("/api/admin/earn/payouts", json={"user_id": ucl["id"], "ref": "UTR123456"}, headers=ORIGIN)
check("mark paid", (r.status_code, r.json().get("amount")), (200, 1000))
check("nothing owed twice", boss.post("/api/admin/earn/payouts", json={"user_id": ucl["id"], "ref": "x"}, headers=ORIGIN).status_code, 400)
me = cl.get("/api/earn/me").json()
check("clipper sees it paid", (me["totals"]["paid"], me["totals"]["owed"], me["payouts"][0]["ref"]), (1000, 0, "UTR123456"))
check("clipper got a notification", any("UPI" in n["title"] for n in cl.get("/api/notifications").json()["items"]), True)
check("paid campaign can't be deleted", boss.delete(f"/api/admin/earn/campaigns/{camp['id']}", headers=ORIGIN).status_code, 400)
check("draft can be deleted", boss.delete(f"/api/admin/earn/campaigns/{draft['id']}", headers=ORIGIN).status_code, 200)
check("hero numbers count the payout", anon.get("/api/earn/public/overview").json()["overview"]["paid_out"], 1000)
check("YouTube key that isn't one is refused", boss.put("/api/admin/earn/settings", json={"youtube_key": "nope"}, headers=ORIGIN).status_code, 400)

print("ALL PASSED" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
