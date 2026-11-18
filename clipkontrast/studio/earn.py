"""Earn: paid clipping campaigns.

A creator or brand pays for a campaign with a fixed budget and a rate per 1,000 views. Clippers join, post clips
on their own accounts and send in each link. ClipKontrast cross-checks every link (is it really their account,
was it posted during the campaign, does the caption carry the required tag, has it been sent before), counts the
views (by itself for YouTube, by hand or from a screenshot for the others), and an admin approves the clips.
Approved money comes out of the budget; when the budget is used up the campaign closes by itself. Payouts are
sent by hand (UPI) and recorded here.

Everything is stored in the database (studio/db.py, the earn_* tables). Screenshots and campaign covers are kept
in the data folder, re-encoded so nothing but plain image pixels is ever stored or served."""
import calendar
import csv
import io
import json
import re
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import sqlalchemy as sa

from . import config, db

DIR = config.DATA_DIR / "earn"
COVERS = DIR / "covers"
PROOFS = DIR / "proofs"
SETTINGS = DIR / "settings.json"
PLATFORMS = {"youtube": "YouTube Shorts", "instagram": "Instagram Reels", "x": "X", "tiktok": "TikTok"}
STATUSES = ("draft", "live", "paused", "ended")
YT_API = "https://www.googleapis.com/youtube/v3"
_lock = threading.RLock()
_channels: dict = {}          # YouTube channel id -> (when looked up, "@handle" lower case)


class EarnError(Exception):
    """Something the person can fix, said in plain words."""


def _now() -> float:
    return time.time()


def _dirs():
    for d in (DIR, COVERS, PROOFS):
        d.mkdir(parents=True, exist_ok=True)


# ================================================================ settings (the YouTube key)
def settings() -> dict:
    try:
        s = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        s = {}
    return {"youtube_key": s.get("youtube_key", "")}


def youtube_key() -> str:
    return settings()["youtube_key"] or config.env("CLIPKONTRAST_YOUTUBE_API_KEY", "")


def public_settings() -> dict:
    k = youtube_key()
    return {"youtube_ready": bool(k), "youtube_from_env": bool(config.env("CLIPKONTRAST_YOUTUBE_API_KEY", "")) and not settings()["youtube_key"],
            "youtube_hint": ("…" + k[-4:]) if k else ""}


def save_settings(youtube_key_value: str) -> dict:
    _dirs()
    v = (youtube_key_value or "").strip()
    if v and not re.fullmatch(r"[\w\-]{20,60}", v):
        raise EarnError("That doesn't look like a YouTube API key. It is about 39 letters and numbers, starting with AIza.")
    if v:
        _yt_get("videos", {"part": "id", "id": "dQw4w9WgXcQ"}, key=v)      # proves the key works before keeping it
    tmp = SETTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps({"youtube_key": v}), encoding="utf-8")
    tmp.replace(SETTINGS)
    return public_settings()


# ================================================================ reading links
def _clean_handle(v: str, platform: str) -> str:
    """'@Name', 'name', 'https://instagram.com/name/' and 'youtube.com/@Name' all become '@name'.
    A YouTube channel id (UC...) is kept as it is."""
    v = (v or "").strip()
    if not v:
        return ""
    if "/" in v or "." in v.split("@")[0]:
        p = urlparse(v if "://" in v else "https://" + v)
        parts = [x for x in p.path.split("/") if x]
        if platform == "youtube" and parts[:1] == ["channel"] and len(parts) > 1:
            return parts[1]
        v = next((x for x in parts if x.startswith("@")), parts[0] if parts else "")
    v = v.lstrip("@")
    if platform == "youtube" and re.fullmatch(r"UC[\w\-]{22}", v):
        return v
    if not re.fullmatch(r"[\w.\-]{1,60}", v):
        raise EarnError(f"Your {PLATFORMS[platform].split()[0]} handle doesn't look right. Write it like @yourname.")
    return "@" + v.lower()


def parse_link(url: str) -> dict:
    """Which platform a clip link is on, the clip's own id, and the account name when the link shows it."""
    url = (url or "").strip()
    if not url:
        raise EarnError("Paste the link to your clip.")
    if len(url) > 400:
        raise EarnError("That link is too long.")
    p = urlparse(url if "://" in url else "https://" + url)
    host = (p.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    parts = [x for x in p.path.split("/") if x]
    if host in ("youtube.com", "youtu.be", "music.youtube.com"):
        vid = ""
        if host == "youtu.be" and parts:
            vid = parts[0]
        elif parts[:1] in (["shorts"], ["live"], ["embed"]) and len(parts) > 1:
            vid = parts[1]
        elif parts[:1] == ["watch"]:
            vid = (parse_qs(p.query).get("v") or [""])[0]
        if not re.fullmatch(r"[\w\-]{11}", vid):
            raise EarnError("That YouTube link doesn't point to a video. Copy the Share link of your Short.")
        return {"platform": "youtube", "id": vid, "handle": "", "url": f"https://www.youtube.com/shorts/{vid}"}
    if host in ("instagram.com", "instagr.am"):
        i = next((n for n, x in enumerate(parts) if x in ("reel", "reels", "p", "tv")), None)
        code = parts[i + 1] if i is not None and len(parts) > i + 1 else ""
        if not re.fullmatch(r"[\w\-]{5,40}", code):
            raise EarnError("That Instagram link doesn't point to a reel. Open the reel, tap Share, then Copy link.")
        handle = "@" + parts[0].lower() if i == 1 and parts[0] not in ("reel", "reels", "p", "tv") else ""
        return {"platform": "instagram", "id": code, "handle": handle, "url": f"https://www.instagram.com/reel/{code}/"}
    if host in ("x.com", "twitter.com", "mobile.twitter.com", "fxtwitter.com", "vxtwitter.com"):
        if len(parts) >= 3 and parts[1] == "status" and parts[2].isdigit():
            return {"platform": "x", "id": parts[2], "handle": "@" + parts[0].lower(), "url": f"https://x.com/{parts[0]}/status/{parts[2]}"}
        raise EarnError("That X link doesn't point to a post. Open the post, tap Share, then Copy link.")
    if host in ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com"):
        if len(parts) >= 3 and parts[0].startswith("@") and parts[1] == "video" and parts[2].isdigit():
            return {"platform": "tiktok", "id": parts[2], "handle": parts[0].lower(), "url": f"https://www.tiktok.com/{parts[0]}/video/{parts[2]}"}
        raise EarnError("Paste the full TikTok link (tiktok.com/@you/video/...). Short vm.tiktok.com links can't be checked.")
    raise EarnError("Links from YouTube, Instagram, X and TikTok are accepted.")


def _posted_from_id(platform: str, vid: str):
    """X and TikTok put the posting time inside the post's id, so it can be read without asking anyone."""
    try:
        if platform == "x":
            return ((int(vid) >> 22) + 1288834974657) / 1000
        if platform == "tiktok":
            return float(int(vid) >> 32)
    except ValueError:
        pass
    return None


# ================================================================ YouTube: views, channel, date, caption
def _yt_get(path: str, params: dict, key: str = ""):
    key = key or youtube_key()
    if not key:
        raise EarnError("No YouTube API key is set.")
    try:
        r = httpx.get(f"{YT_API}/{path}", params={**params, "key": key}, timeout=15)
    except httpx.HTTPError:
        raise EarnError("YouTube couldn't be reached. Try again in a minute.")
    if r.status_code == 403 and "quota" in r.text.lower():
        raise EarnError("Today's YouTube API quota is used up. It resets at midnight Pacific time.")
    if r.status_code in (400, 403):
        raise EarnError("YouTube refused the API key. Check it in Earn settings.")
    if r.status_code != 200:
        raise EarnError(f"YouTube answered with an error ({r.status_code}).")
    return r.json()


def _yt_videos(ids: list) -> dict:
    out = {}
    for i in range(0, len(ids), 50):
        d = _yt_get("videos", {"part": "snippet,statistics", "id": ",".join(ids[i:i + 50])})
        for it in d.get("items", []):
            sn, st = it.get("snippet", {}), it.get("statistics", {})
            published = None
            try:
                published = float(calendar.timegm(time.strptime(sn.get("publishedAt", "")[:19], "%Y-%m-%dT%H:%M:%S")))
            except ValueError:
                pass
            out[it["id"]] = {"views": int(st.get("viewCount") or 0), "channel_id": sn.get("channelId", ""),
                             "channel": sn.get("channelTitle", ""), "title": sn.get("title", ""),
                             "text": (sn.get("title", "") + "\n" + sn.get("description", "") + "\n" + " ".join(sn.get("tags") or [])),
                             "posted_at": published}
    return out


def _yt_handle(channel_id: str) -> str:
    got = _channels.get(channel_id)
    if got and _now() - got[0] < 86400:
        return got[1]
    d = _yt_get("channels", {"part": "snippet", "id": channel_id})
    h = ((d.get("items") or [{}])[0].get("snippet", {}).get("customUrl") or "").lower()
    if h and not h.startswith("@"):
        h = "@" + h
    _channels[channel_id] = (_now(), h)
    return h


# ================================================================ campaigns
_CAMP_FIELDS = {"title": 120, "creator_name": 120, "creator_url": 300, "tagline": 200, "brief": 6000, "rules": 4000,
                "sources": 4000, "required_tag": 80, "category": 40}


def _slug(title: str, taken: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "campaign"
    s, n = base, 2
    while s in taken:
        s, n = f"{base}-{n}", n + 1
    return s


def _num(v, name, lo=0.0, hi=1e9, integer=False):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise EarnError(f"{name} must be a number.")
    if not lo <= x <= hi:
        raise EarnError(f"{name} must be between {lo:g} and {hi:g}.")
    return int(x) if integer else round(x, 2)


def save_campaign(data: dict, cid: str = "") -> dict:
    vals = {}
    for k, n in _CAMP_FIELDS.items():
        if k in data:
            vals[k] = str(data.get(k) or "").strip()[:n]
    if "title" in vals and len(vals["title"]) < 3:
        raise EarnError("Give the campaign a name of at least 3 letters.")
    if "platforms" in data:
        pl = [p for p in (data["platforms"] if isinstance(data["platforms"], list) else str(data["platforms"]).split(",")) if p in PLATFORMS]
        if not pl:
            raise EarnError("Pick at least one platform.")
        vals["platforms"] = ",".join(dict.fromkeys(pl))
    for k, name, hi, integer in (("rate_per_1k", "Rate per 1,000 views", 100000, False), ("min_views", "Minimum views", 1e9, True),
                                 ("max_per_clip", "Most per clip", 1e8, False), ("budget", "Budget", 1e9, False),
                                 ("hold_days", "Days before views are counted", 60, True)):
        if k in data:
            vals[k] = _num(data[k], name, 0, hi, integer)
    for k in ("starts_at", "ends_at"):
        if k in data:
            vals[k] = float(data[k]) if data[k] not in (None, "", 0) else None
    if vals.get("starts_at") and vals.get("ends_at") and vals["ends_at"] <= vals["starts_at"]:
        raise EarnError("The end date must be after the start date.")
    if "status" in data:
        if data["status"] not in STATUSES:
            raise EarnError("Unknown status.")
        vals["status"] = data["status"]
    if "accent" in data and re.fullmatch(r"#[0-9a-fA-F]{6}", str(data["accent"])):
        vals["accent"] = data["accent"]
    if vals.get("creator_url") and not re.match(r"https?://", vals["creator_url"]):
        vals["creator_url"] = "https://" + vals["creator_url"]
    vals["updated_at"] = _now()
    c_ = db.earn_campaigns.c
    with db.engine.begin() as c:
        if cid:
            row = c.execute(sa.select(db.earn_campaigns).where(c_.id == cid)).first()
            if not row:
                raise EarnError("That campaign doesn't exist.")
            if vals.get("status") == "live" and not (vals.get("budget", row.budget) > 0 and vals.get("rate_per_1k", row.rate_per_1k) > 0):
                raise EarnError("Set a budget and a rate before going live.")
            c.execute(db.earn_campaigns.update().where(c_.id == cid).values(**vals))
        else:
            if not vals.get("title"):
                raise EarnError("Give the campaign a name.")
            if vals.get("status") == "live" and not (vals.get("budget", 0) > 0 and vals.get("rate_per_1k", 0) > 0):
                raise EarnError("Set a budget and a rate before going live.")
            taken = {r[0] for r in c.execute(sa.select(c_.slug))}
            cid = "cm_" + secrets.token_hex(6)
            c.execute(db.earn_campaigns.insert().values(id=cid, slug=_slug(vals["title"], taken), created_at=_now(), **vals))
    return campaign(cid, admin=True)


def delete_campaign(cid: str):
    with db.engine.begin() as c:
        paid = c.execute(sa.select(sa.func.count()).select_from(db.earn_submissions).where(
            db.earn_submissions.c.campaign_id == cid, db.earn_submissions.c.status == "paid")).scalar()
        if paid:
            raise EarnError("Clips in this campaign have already been paid, so it can't be deleted. End it instead.")
        ids = [r[0] for r in c.execute(sa.select(db.earn_submissions.c.id).where(db.earn_submissions.c.campaign_id == cid))]
        c.execute(db.earn_submissions.delete().where(db.earn_submissions.c.campaign_id == cid))
        c.execute(db.earn_members.delete().where(db.earn_members.c.campaign_id == cid))
        c.execute(db.earn_campaigns.delete().where(db.earn_campaigns.c.id == cid))
    for i in ids:
        (PROOFS / f"{i}.jpg").unlink(missing_ok=True)
    (COVERS / f"{cid}.jpg").unlink(missing_ok=True)


def _estimate(views: int, camp) -> float:
    if views < (camp.min_views or 0) or not camp.rate_per_1k:
        return 0.0
    amt = views / 1000 * camp.rate_per_1k
    if camp.max_per_clip:
        amt = min(amt, camp.max_per_clip)
    return round(amt, 2)


def _stats(c, ids: list) -> dict:
    s = db.earn_submissions.c
    out = {i: {"committed": 0.0, "paid": 0.0, "pending_est": 0.0, "clips": 0, "views": 0, "clippers": 0, "pending": 0} for i in ids}
    if not ids:
        return out
    for cid, status, n, amt, views in c.execute(sa.select(s.campaign_id, s.status, sa.func.count(), sa.func.sum(s.amount), sa.func.sum(s.views))
                                                .where(s.campaign_id.in_(ids)).group_by(s.campaign_id, s.status)):
        o = out[cid]
        if status != "rejected":
            o["clips"] += n
            o["views"] += int(views or 0)
        if status in ("approved", "paid"):
            o["committed"] += float(amt or 0)
        if status == "paid":
            o["paid"] += float(amt or 0)
        if status == "pending":
            o["pending"] += n
    for cid, n in c.execute(sa.select(db.earn_members.c.campaign_id, sa.func.count()).where(db.earn_members.c.campaign_id.in_(ids))
                            .group_by(db.earn_members.c.campaign_id)):
        out[cid]["clippers"] = n
    return out


def _camp_dict(r, st: dict, admin=False, member=False) -> dict:
    committed = round(st["committed"], 2)
    d = {"id": r.id, "slug": r.slug, "title": r.title, "creator_name": r.creator_name, "creator_url": r.creator_url,
         "tagline": r.tagline, "brief": r.brief, "rules": [x.strip() for x in r.rules.splitlines() if x.strip()],
         "platforms": [p for p in r.platforms.split(",") if p], "required_tag": r.required_tag, "category": r.category,
         "rate_per_1k": r.rate_per_1k, "min_views": r.min_views, "max_per_clip": r.max_per_clip, "budget": r.budget,
         "hold_days": r.hold_days, "status": r.status, "starts_at": r.starts_at, "ends_at": r.ends_at,
         "cover": f"/earn/cover/{r.id}.jpg?v={int(r.updated_at)}" if r.has_cover else "", "accent": r.accent,
         "committed": committed, "paid": round(st["paid"], 2), "remaining": round(max(0.0, r.budget - committed), 2),
         "used_pct": round(min(100.0, committed / r.budget * 100), 1) if r.budget else 0,
         "clips": st["clips"], "views": st["views"], "clippers": st["clippers"],
         "open": _is_open(r, committed), "member": member}
    if admin or member:
        d["sources"] = [x.strip() for x in r.sources.splitlines() if x.strip()]
    if admin:
        d.update(pending=st["pending"], created_at=r.created_at, raw_rules=r.rules, raw_sources=r.sources)
    return d


def _is_open(r, committed: float) -> bool:
    now = _now()
    return (r.status == "live" and r.budget - committed > 0.5 and (not r.starts_at or r.starts_at <= now)
            and (not r.ends_at or r.ends_at > now))


def campaigns(admin=False, uid: str = "") -> list:
    c_ = db.earn_campaigns.c
    q = sa.select(db.earn_campaigns)
    if not admin:
        q = q.where(c_.status != "draft")
    with db.engine.connect() as c:
        rows = c.execute(q.order_by(c_.created_at.desc())).all()
        st = _stats(c, [r.id for r in rows])
        mine = {r[0] for r in c.execute(sa.select(db.earn_members.c.campaign_id).where(db.earn_members.c.user_id == uid))} if uid else set()
    order = {"live": 0, "paused": 1, "draft": 2, "ended": 3}
    out = [_camp_dict(r, st[r.id], admin, r.id in mine) for r in rows]
    out.sort(key=lambda d: (not d["open"], order.get(d["status"], 9), -d["clippers"], -d["clips"], -d["remaining"]))
    return out


def campaign(key: str, admin=False, uid: str = "") -> dict:
    c_ = db.earn_campaigns.c
    with db.engine.connect() as c:
        r = c.execute(sa.select(db.earn_campaigns).where(sa.or_(c_.id == key, c_.slug == key))).first()
        if not r or (r.status == "draft" and not admin):
            raise EarnError("That campaign doesn't exist.")
        st = _stats(c, [r.id])[r.id]
        member = bool(uid and c.execute(sa.select(db.earn_members.c.user_id).where(
            db.earn_members.c.campaign_id == r.id, db.earn_members.c.user_id == uid)).first())
    d = _camp_dict(r, st, admin, member)
    d["leaderboard"] = leaderboard(r.id)
    return d


def _public_name(name: str, email: str) -> str:
    if name:
        return name
    e = (email or "clipper").split("@")[0]
    return e[:2] + "•" * max(2, min(5, len(e) - 2))


def leaderboard(cid: str = "", limit: int = 10) -> list:
    s, p, u = db.earn_submissions.c, db.earn_profiles.c, db.users.c
    earned = sa.func.sum(sa.case((s.status.in_(("approved", "paid")), s.amount), else_=0))
    q = (sa.select(s.user_id, sa.func.count(), sa.func.sum(s.views), earned, p.display_name, u.email)
         .select_from(db.earn_submissions.join(db.users, u.id == s.user_id).outerjoin(db.earn_profiles, p.user_id == s.user_id))
         .where(s.status != "rejected"))
    if cid:
        q = q.where(s.campaign_id == cid)
    q = q.group_by(s.user_id, p.display_name, u.email).order_by(sa.func.sum(s.views).desc()).limit(limit)
    with db.engine.connect() as c:
        return [{"name": _public_name(dn or "", email), "clips": n, "views": int(v or 0), "earned": round(float(e or 0), 2)}
                for _, n, v, e, dn, email in c.execute(q)]


def overview() -> dict:
    """The numbers at the top of the Earn page."""
    cs = campaigns()
    with db.engine.connect() as c:
        paid = c.execute(sa.select(sa.func.sum(db.earn_payouts.c.amount))).scalar() or 0
        clippers = c.execute(sa.select(sa.func.count(sa.distinct(db.earn_members.c.user_id)))).scalar() or 0
    live = [x for x in cs if x["open"]]
    return {"live": len(live), "live_budget": round(sum(x["remaining"] for x in live), 2), "paid_out": round(float(paid), 2),
            "clippers": int(clippers), "views": sum(x["views"] for x in cs)}


def save_cover(cid: str, data: bytes):
    _dirs()
    _image(data, COVERS / f"{cid}.jpg", 1600)
    with db.engine.begin() as c:
        c.execute(db.earn_campaigns.update().where(db.earn_campaigns.c.id == cid).values(has_cover=True, updated_at=_now()))


def _image(data: bytes, dest: Path, size: int):
    """Only plain pixels are kept: the picture is opened, checked and saved again as a JPEG."""
    from PIL import Image, ImageOps
    if len(data) > 8 * 1024 * 1024:
        raise EarnError("That image is too big. The limit is 8 MB.")
    try:
        im = Image.open(io.BytesIO(data))
        if im.format not in ("PNG", "JPEG", "WEBP"):
            raise EarnError("Use a PNG, JPG or WEBP image.")
        if im.width * im.height > 40_000_000:
            raise EarnError("That image is too large.")
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((size, size))
    except EarnError:
        raise
    except Exception:  # noqa: BLE001 - anything Pillow can't read is simply not an image
        raise EarnError("That file isn't an image ClipKontrast can read. Use a PNG or JPG.")
    tmp = dest.with_suffix(".tmp")
    im.save(tmp, "JPEG", quality=85, optimize=True)
    tmp.replace(dest)


# ================================================================ clippers: profile, joining
_PROFILE = ("display_name", "whatsapp", "upi", "youtube", "instagram", "x", "tiktok", "city")


def profile(uid: str) -> dict:
    with db.engine.connect() as c:
        r = c.execute(sa.select(db.earn_profiles).where(db.earn_profiles.c.user_id == uid)).first()
    d = {k: (getattr(r, k) if r else "") for k in _PROFILE}
    d["complete"] = bool(r and r.upi and r.whatsapp and any(getattr(r, p) for p in PLATFORMS))
    return d


def save_profile(uid: str, data: dict) -> dict:
    v = {}
    v["display_name"] = re.sub(r"[<>\"]", "", str(data.get("display_name", "")).strip())[:40]
    w = re.sub(r"[\s\-()]", "", str(data.get("whatsapp", "")))
    if w and not re.fullmatch(r"\+?\d{10,15}", w):
        raise EarnError("Write your WhatsApp number with the country code, like +91 98765 43210.")
    if re.fullmatch(r"\d{10}", w):
        w = "+91" + w
    v["whatsapp"] = w
    upi = str(data.get("upi", "")).strip().lower()
    if upi and not re.fullmatch(r"[a-z0-9.\-_]{2,60}@[a-z]{2,30}", upi):
        raise EarnError("That UPI ID doesn't look right. It looks like name@okaxis or 98xxxxxxxx@ybl.")
    v["upi"] = upi
    for p in PLATFORMS:
        v[p] = _clean_handle(str(data.get(p, "")), p)
    v["city"] = str(data.get("city", "")).strip()[:60]
    v["updated_at"] = _now()
    with db.engine.begin() as c:
        if c.execute(sa.select(db.earn_profiles.c.user_id).where(db.earn_profiles.c.user_id == uid)).first():
            c.execute(db.earn_profiles.update().where(db.earn_profiles.c.user_id == uid).values(**v))
        else:
            c.execute(db.earn_profiles.insert().values(user_id=uid, **v))
    return profile(uid)


def _camp_row(c, cid: str):
    r = c.execute(sa.select(db.earn_campaigns).where(sa.or_(db.earn_campaigns.c.id == cid, db.earn_campaigns.c.slug == cid))).first()
    if not r or r.status == "draft":
        raise EarnError("That campaign doesn't exist.")
    return r


def join(uid: str, cid: str) -> dict:
    if not profile(uid)["complete"]:
        raise EarnError("Finish your payout profile first: WhatsApp, UPI ID and at least one account handle.")
    with db.engine.begin() as c:
        r = _camp_row(c, cid)
        committed = _stats(c, [r.id])[r.id]["committed"]
        if not _is_open(r, committed):
            raise EarnError("This campaign isn't taking new clippers right now.")
        if not c.execute(sa.select(db.earn_members.c.user_id).where(db.earn_members.c.campaign_id == r.id, db.earn_members.c.user_id == uid)).first():
            c.execute(db.earn_members.insert().values(campaign_id=r.id, user_id=uid, joined_at=_now()))
    return campaign(r.id, uid=uid)


# ================================================================ submitting a clip, and the cross-check
def _check(camp, link: dict, prof: dict, info: dict = None) -> dict:
    """What can be proven automatically. True: checked and fine. False: checked and wrong. None: a person checks."""
    ch = {"owner": None, "owner_detail": "", "after_start": None, "tag": None, "found": None, "title": "", "channel": ""}
    want = prof.get(link["platform"], "")
    if link["platform"] in ("x", "tiktok") or link.get("handle"):
        ch["owner"] = bool(want) and link["handle"] == want
        ch["owner_detail"] = f"Link is from {link['handle']}, profile says {want or 'nothing'}"
    posted = _posted_from_id(link["platform"], link["id"])
    if info:
        ch.update(found=True, title=info["title"][:140], channel=info["channel"][:80])
        posted = info["posted_at"]
        try:
            handle = _yt_handle(info["channel_id"]) if info["channel_id"] else ""
        except EarnError:
            handle = ""
        if want == info["channel_id"] or (handle and want == handle):
            ch["owner"] = True
        elif handle or want.startswith("UC"):
            ch["owner"] = False
        ch["owner_detail"] = f"Posted by {handle or info['channel']}, profile says {want or 'nothing'}"
        if camp.required_tag:
            ch["tag"] = camp.required_tag.lower().lstrip("#@") in info["text"].lower()
    if posted and camp.starts_at:
        ch["after_start"] = posted >= camp.starts_at - 3600
    ch["posted_at"] = posted
    return ch


def submit(uid: str, cid: str, url: str, note: str = "") -> dict:
    link = parse_link(url)
    prof = profile(uid)
    if not prof["complete"]:
        raise EarnError("Finish your payout profile first: WhatsApp, UPI ID and at least one account handle.")
    if not prof.get(link["platform"]):
        raise EarnError(f"Add your {PLATFORMS[link['platform']]} handle to your profile first, so we can match the clip to you.")
    with db.engine.connect() as c:
        camp = _camp_row(c, cid)
        committed = _stats(c, [camp.id])[camp.id]["committed"]
    if not _is_open(camp, committed):
        raise EarnError("This campaign isn't taking clips right now.")
    if link["platform"] not in camp.platforms.split(","):
        raise EarnError(f"This campaign doesn't pay for {PLATFORMS[link['platform']]}. It pays for "
                        + ", ".join(PLATFORMS[p] for p in camp.platforms.split(",") if p) + ".")
    info = None
    if link["platform"] == "youtube" and youtube_key():
        try:
            info = _yt_videos([link["id"]]).get(link["id"])
        except EarnError:
            info = None                                    # YouTube is down or the quota is gone: a person checks instead
        else:
            if info is None:
                raise EarnError("YouTube can't find that video. Make sure it's public, then try again.")
    checks = _check(camp, link, prof, info)
    if checks["owner"] is False:
        raise EarnError("That clip isn't on the account in your profile (" + checks["owner_detail"] + "). Fix your handle or send a clip from your own account.")
    if checks["after_start"] is False:
        raise EarnError("That clip was posted before the campaign started, so it can't be paid.")
    key = f"{link['platform']}:{link['id'].lower() if link['platform'] != 'youtube' else link['id']}"
    row = {"campaign_id": camp.id, "user_id": uid, "platform": link["platform"], "url": link["url"], "video_key": key,
           "note": re.sub(r"[<>]", "", note or "").strip()[:300], "submitted_at": _now(), "posted_at": checks.pop("posted_at"),
           "checks": json.dumps(checks)}
    if info:
        row.update(views=info["views"], views_at=_now(), views_source="api")
    with db.engine.begin() as c:
        if c.execute(sa.select(db.earn_submissions.c.id).where(db.earn_submissions.c.campaign_id == camp.id,
                                                               db.earn_submissions.c.video_key == key)).first():
            raise EarnError("That clip has already been sent in for this campaign.")
        if not c.execute(sa.select(db.earn_members.c.user_id).where(db.earn_members.c.campaign_id == camp.id,
                                                                    db.earn_members.c.user_id == uid)).first():
            c.execute(db.earn_members.insert().values(campaign_id=camp.id, user_id=uid, joined_at=_now()))
        sid = c.execute(db.earn_submissions.insert().values(**row)).inserted_primary_key[0]
    return submission(sid)


def _sub_dict(r, camp=None, admin=False, extra=None) -> dict:
    checks = json.loads(r.checks or "{}")
    hold = (camp.hold_days if camp else 7) * 86400
    since = r.posted_at or r.submitted_at
    d = {"id": r.id, "campaign_id": r.campaign_id, "campaign": camp.title if camp else "", "platform": r.platform, "url": r.url,
         "note": r.note, "submitted_at": r.submitted_at, "posted_at": r.posted_at, "views": r.views, "views_at": r.views_at,
         "views_source": r.views_source, "checks": checks, "has_proof": r.has_proof, "status": r.status,
         "amount": r.amount, "estimate": _estimate(r.views, camp) if camp else 0, "review_note": r.review_note,
         "reviewed_at": r.reviewed_at, "ready_at": since + hold, "ready": _now() >= since + hold}
    if extra:
        d.update(extra)
    return d


def submission(sid: int, uid: str = "") -> dict:
    with db.engine.connect() as c:
        r = c.execute(sa.select(db.earn_submissions).where(db.earn_submissions.c.id == sid)).first()
        if not r or (uid and r.user_id != uid):
            raise EarnError("That clip doesn't exist.")
        camp = c.execute(sa.select(db.earn_campaigns).where(db.earn_campaigns.c.id == r.campaign_id)).first()
    return _sub_dict(r, camp)


def mine(uid: str) -> dict:
    s = db.earn_submissions.c
    with db.engine.connect() as c:
        rows = c.execute(sa.select(db.earn_submissions).where(s.user_id == uid).order_by(s.submitted_at.desc()).limit(500)).all()
        camps = {r.id: r for r in c.execute(sa.select(db.earn_campaigns))}
        joined = [r[0] for r in c.execute(sa.select(db.earn_members.c.campaign_id).where(db.earn_members.c.user_id == uid))]
        payouts = [{"id": p.id, "amount": p.amount, "ref": p.ref, "clips": p.clips, "created_at": p.created_at, "upi": p.upi}
                   for p in c.execute(sa.select(db.earn_payouts).where(db.earn_payouts.c.user_id == uid).order_by(db.earn_payouts.c.created_at.desc()))]
    subs = [_sub_dict(r, camps.get(r.campaign_id)) for r in rows]
    tot = {"pending_estimate": round(sum(x["estimate"] for x in subs if x["status"] == "pending"), 2),
           "owed": round(sum(x["amount"] for x in subs if x["status"] == "approved"), 2),
           "paid": round(sum(x["amount"] for x in subs if x["status"] == "paid"), 2),
           "views": sum(x["views"] for x in subs if x["status"] != "rejected"),
           "clips": len([x for x in subs if x["status"] != "rejected"])}
    return {"profile": profile(uid), "joined": joined, "submissions": subs, "totals": tot, "payouts": payouts}


def withdraw(uid: str, sid: int):
    with db.engine.begin() as c:
        r = c.execute(sa.select(db.earn_submissions).where(db.earn_submissions.c.id == sid, db.earn_submissions.c.user_id == uid)).first()
        if not r:
            raise EarnError("That clip doesn't exist.")
        if r.status != "pending":
            raise EarnError("Only clips that haven't been reviewed yet can be removed.")
        c.execute(db.earn_submissions.delete().where(db.earn_submissions.c.id == sid))
    (PROOFS / f"{sid}.jpg").unlink(missing_ok=True)


def save_proof(uid: str, sid: int, data: bytes, admin=False) -> dict:
    with db.engine.connect() as c:
        r = c.execute(sa.select(db.earn_submissions).where(db.earn_submissions.c.id == sid)).first()
    if not r or (r.user_id != uid and not admin):
        raise EarnError("That clip doesn't exist.")
    if r.status not in ("pending",) and not admin:
        raise EarnError("This clip has already been reviewed.")
    _dirs()
    _image(data, PROOFS / f"{sid}.jpg", 1800)
    with db.engine.begin() as c:
        c.execute(db.earn_submissions.update().where(db.earn_submissions.c.id == sid).values(has_proof=True))
    return submission(sid)


def proof_path(sid: int, uid: str, admin: bool) -> Path:
    with db.engine.connect() as c:
        r = c.execute(sa.select(db.earn_submissions.c.user_id).where(db.earn_submissions.c.id == sid)).first()
    p = PROOFS / f"{sid}.jpg"
    if not r or (r[0] != uid and not admin) or not p.is_file():
        raise EarnError("Not found.")
    return p


# ================================================================ admins: review, views, payouts
def review_queue(cid: str = "", status: str = "pending", q: str = "") -> dict:
    s, p, u = db.earn_submissions.c, db.earn_profiles.c, db.users.c
    query = (sa.select(db.earn_submissions, p.display_name, p.upi, p.whatsapp, p.youtube, p.instagram, p.x, p.tiktok, u.email)
             .select_from(db.earn_submissions.join(db.users, u.id == s.user_id).outerjoin(db.earn_profiles, p.user_id == s.user_id)))
    if cid:
        query = query.where(s.campaign_id == cid)
    if status in ("pending", "approved", "rejected", "paid"):
        query = query.where(s.status == status)
    if q:
        like = f"%{q.strip().lower()[:80]}%"
        query = query.where(sa.or_(sa.func.lower(u.email).like(like), sa.func.lower(p.display_name).like(like), sa.func.lower(s.url).like(like)))
    with db.engine.connect() as c:
        rows = c.execute(query.order_by(s.submitted_at.desc()).limit(1000)).all()
        camps = {r.id: r for r in c.execute(sa.select(db.earn_campaigns))}
        counts = dict(c.execute(sa.select(s.status, sa.func.count()).where(s.campaign_id == cid if cid else sa.true()).group_by(s.status)).all())
    items = []
    for r in rows:
        m = r._mapping
        items.append(_sub_dict(r, camps.get(r.campaign_id), admin=True, extra={
            "clipper": {"name": m["display_name"] or "", "email": m["email"], "upi": m["upi"] or "", "whatsapp": m["whatsapp"] or "",
                        "handle": m[r.platform] or ""}}))
    return {"items": items, "counts": {k: counts.get(k, 0) for k in ("pending", "approved", "rejected", "paid")}}


def set_views(sid: int, views: int) -> dict:
    views = _num(views, "Views", 0, 5e10, integer=True)
    with db.engine.begin() as c:
        r = c.execute(sa.select(db.earn_submissions.c.status).where(db.earn_submissions.c.id == sid)).first()
        if not r:
            raise EarnError("That clip doesn't exist.")
        if r[0] in ("approved", "paid"):
            raise EarnError("Views of an approved clip can't change. Move it back to review first.")
        c.execute(db.earn_submissions.update().where(db.earn_submissions.c.id == sid).values(views=views, views_at=_now(), views_source="manual"))
    return submission(sid)


def refresh_views(ids: list = None) -> int:
    """Ask YouTube for the current views of clips still waiting for review. Returns how many were updated."""
    if not youtube_key():
        return 0
    s = db.earn_submissions.c
    q = sa.select(s.id, s.url).where(s.platform == "youtube", s.status == "pending")
    if ids:
        q = q.where(s.id.in_(ids))
    else:
        q = q.where(s.submitted_at > _now() - 45 * 86400, sa.or_(s.views_at.is_(None), s.views_at < _now() - 3 * 3600))
    with db.engine.connect() as c:
        rows = c.execute(q.limit(2000)).all()
    if not rows:
        return 0
    vid = {r.id: parse_link(r.url)["id"] for r in rows}
    got = _yt_videos(list(set(vid.values())))
    n = 0
    with db.engine.begin() as c:
        for sid, v in vid.items():
            if v in got:
                c.execute(db.earn_submissions.update().where(s.id == sid).values(views=got[v]["views"], views_at=_now(), views_source="api"))
                n += 1
    return n


def _notify(uid, title, body, ref=None):
    try:
        from . import notices
        notices.add(uid, "earn", title, body, link="/earn#me", ref=ref)
    except Exception:  # noqa: BLE001 - a missed notification must never undo a review
        pass


def decide(sid: int, action: str, note: str = "", views=None) -> dict:
    """approve | reject | reopen one clip. Approving fixes the amount and takes it out of the budget."""
    note = re.sub(r"[<>]", "", note or "").strip()[:300]
    if views not in (None, ""):
        set_views(sid, views)
    s = db.earn_submissions.c
    with _lock, db.engine.begin() as c:
        r = c.execute(sa.select(db.earn_submissions).where(s.id == sid)).first()
        if not r:
            raise EarnError("That clip doesn't exist.")
        camp = c.execute(sa.select(db.earn_campaigns).where(db.earn_campaigns.c.id == r.campaign_id)).first()
        if r.status == "paid":
            raise EarnError("This clip has already been paid.")
        if action == "approve":
            if r.status == "approved":
                return _sub_dict(r, camp)
            committed = _stats(c, [camp.id])[camp.id]["committed"]
            est = _estimate(r.views, camp)
            remaining = max(0.0, camp.budget - committed)
            if est > 0 and remaining <= 0.5:
                raise EarnError("The budget for this campaign is used up. Raise the budget to approve more clips.")
            amount = round(min(est, remaining), 2)
            c.execute(db.earn_submissions.update().where(s.id == sid).values(status="approved", amount=amount, review_note=note, reviewed_at=_now()))
            if camp.status == "live" and remaining - amount <= 0.5:
                c.execute(db.earn_campaigns.update().where(db.earn_campaigns.c.id == camp.id).values(status="ended", updated_at=_now()))
            uid, msg = r.user_id, (f"Approved: ₹{amount:,.2f} for {r.views:,} views." if amount else f"Accepted, but under {camp.min_views:,} views, so it earns nothing.")
            title = f"Clip approved · {camp.title}"
        elif action == "reject":
            c.execute(db.earn_submissions.update().where(s.id == sid).values(status="rejected", amount=0, review_note=note or "Doesn't meet the campaign rules.", reviewed_at=_now()))
            uid, title, msg = r.user_id, f"Clip not approved · {camp.title}", note or "It doesn't meet the campaign rules."
        elif action == "reopen":
            c.execute(db.earn_submissions.update().where(s.id == sid).values(status="pending", amount=0, review_note="", reviewed_at=None))
            uid = None
        else:
            raise EarnError("Unknown action.")
    if uid:
        _notify(uid, title, msg)
    return submission(sid)


def owed() -> list:
    s, p, u = db.earn_submissions.c, db.earn_profiles.c, db.users.c
    q = (sa.select(s.user_id, sa.func.count(), sa.func.sum(s.amount), sa.func.sum(s.views), p.display_name, p.upi, p.whatsapp, u.email)
         .select_from(db.earn_submissions.join(db.users, u.id == s.user_id).outerjoin(db.earn_profiles, p.user_id == s.user_id))
         .where(s.status == "approved", s.amount > 0).group_by(s.user_id, p.display_name, p.upi, p.whatsapp, u.email)
         .order_by(sa.func.sum(s.amount).desc()))
    with db.engine.connect() as c:
        return [{"user_id": uid, "clips": n, "amount": round(float(a or 0), 2), "views": int(v or 0), "name": dn or "", "upi": upi or "",
                 "whatsapp": wa or "", "email": email} for uid, n, a, v, dn, upi, wa, email in c.execute(q)]


def mark_paid(user_id: str, ref: str, admin_id: str) -> dict:
    ref = re.sub(r"[^\w\-/ ]", "", ref or "").strip()[:80]
    s = db.earn_submissions.c
    with _lock, db.engine.begin() as c:
        rows = c.execute(sa.select(s.id, s.amount).where(s.user_id == user_id, s.status == "approved", s.amount > 0)).all()
        if not rows:
            raise EarnError("Nothing is owed to this clipper.")
        total = round(sum(r.amount for r in rows), 2)
        upi = c.execute(sa.select(db.earn_profiles.c.upi).where(db.earn_profiles.c.user_id == user_id)).scalar() or ""
        pid = c.execute(db.earn_payouts.insert().values(user_id=user_id, amount=total, ref=ref, upi=upi, clips=len(rows),
                                                        created_at=_now(), admin_id=admin_id)).inserted_primary_key[0]
        c.execute(db.earn_submissions.update().where(s.id.in_([r.id for r in rows])).values(status="paid", payout_id=pid))
    _notify(user_id, f"₹{total:,.2f} sent to your UPI", f"{len(rows)} clip{'s' if len(rows) != 1 else ''} paid" + (f". Reference {ref}." if ref else "."), ref=f"payout:{pid}")
    return {"id": pid, "amount": total, "clips": len(rows)}


def payouts() -> list:
    pt, p, u = db.earn_payouts.c, db.earn_profiles.c, db.users.c
    q = (sa.select(db.earn_payouts, p.display_name, u.email).select_from(
        db.earn_payouts.join(db.users, u.id == pt.user_id).outerjoin(db.earn_profiles, p.user_id == pt.user_id))
        .order_by(pt.created_at.desc()).limit(500))
    with db.engine.connect() as c:
        return [{"id": r.id, "amount": r.amount, "ref": r.ref, "upi": r.upi, "clips": r.clips, "created_at": r.created_at,
                 "name": r._mapping["display_name"] or "", "email": r._mapping["email"]} for r in c.execute(q)]


def _cell(v) -> str:
    """Text typed by clippers, made safe for Excel and Google Sheets: a cell starting with = + - @ (or a tab or
    carriage return) would be run as a formula when the file is opened, so it gets a leading apostrophe."""
    v = str(v or "")
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def owed_csv() -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Name", "Email", "WhatsApp", "UPI", "Clips", "Views", "Amount (INR)"])
    for o in owed():
        # WhatsApp is checked to be digits with an optional +, so it is left as it is for the phone column
        w.writerow([_cell(o["name"]), _cell(o["email"]), o["whatsapp"], _cell(o["upi"]), o["clips"], o["views"], f"{o['amount']:.2f}"])
    return out.getvalue()


def admin_summary() -> dict:
    s = db.earn_submissions.c
    with db.engine.connect() as c:
        counts = dict(c.execute(sa.select(s.status, sa.func.count()).group_by(s.status)).all())
        ready = c.execute(sa.select(sa.func.count()).select_from(db.earn_submissions).where(s.status == "pending")).scalar()
    o = owed()
    return {"counts": {k: counts.get(k, 0) for k in ("pending", "approved", "rejected", "paid")}, "pending": int(ready or 0),
            "owed_total": round(sum(x["amount"] for x in o), 2), "owed_people": len(o), "settings": public_settings(),
            "overview": overview()}


# ================================================================ background: keep YouTube views fresh
def _loop():
    while True:
        time.sleep(60)
        try:
            refresh_views()
        except Exception as e:  # noqa: BLE001 - tried again on the next round
            print(f"  Earn: couldn't refresh YouTube views ({e})", flush=True)
        time.sleep(20 * 60)


def start():
    _dirs()
    threading.Thread(target=_loop, daemon=True).start()
