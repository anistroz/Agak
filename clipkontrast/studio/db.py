"""The database: accounts, sign-in sessions, notifications and the record of AI use.

PostgreSQL on a server (DATABASE_URL=postgresql+psycopg://...). With no DATABASE_URL it uses a SQLite file,
which is fine for one machine."""
import time

import sqlalchemy as sa

from . import config

_SQLITE = config.DATABASE_URL.startswith("sqlite")
engine = sa.create_engine(config.DATABASE_URL, pool_pre_ping=not _SQLITE, future=True, pool_size=20, max_overflow=40,
                          **({"connect_args": {"timeout": 30}} if _SQLITE else {}))

if _SQLITE:
    @sa.event.listens_for(engine, "connect")
    def _fast_sqlite(conn, _record):
        # WAL: people reading are never held up by someone writing. NORMAL: safe against crashes of the app,
        # without waiting for the disk on every single write.
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA busy_timeout=30000")
        cur.close()
meta = sa.MetaData()

users = sa.Table(
    "users", meta,
    sa.Column("id", sa.String(40), primary_key=True),
    sa.Column("email", sa.String(254), nullable=False, unique=True),          # always lower case
    sa.Column("name", sa.String(120), nullable=False, server_default=""),
    sa.Column("password_hash", sa.String(300)),                               # empty for Google-only accounts
    sa.Column("google_sub", sa.String(64), unique=True),
    sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("disabled", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("last_seen", sa.Float),
)
sessions = sa.Table(
    "sessions", meta,
    sa.Column("token_hash", sa.String(64), primary_key=True),                 # sha256 of the cookie; the cookie itself is never stored
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("expires_at", sa.Float, nullable=False),
    sa.Column("ip", sa.String(64)),
    sa.Column("agent", sa.String(300)),
)
usage = sa.Table(                                                             # one row per AI call
    "usage", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sa.Column("t", sa.Float, nullable=False),
    sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),   # text sent to the AI
    sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),  # text it wrote back
    sa.Column("purpose", sa.String(60), nullable=False),
    sa.Column("creator", sa.String(80)),
    sa.Column("place", sa.String(200)),
    sa.Index("usage_user_t", "user_id", "t"),
)


email_ok = sa.Table(                                                          # addresses proven to belong to the account
    "email_ok", meta,
    sa.Column("user_id", sa.String(40), primary_key=True),                    # "_existing" marks that older accounts were counted
    sa.Column("verified_at", sa.Float, nullable=False),
)
email_tokens = sa.Table(                                                      # one-time links: verify an email, reset a password
    "email_tokens", meta,
    sa.Column("token_hash", sa.String(64), primary_key=True),                 # sha256 of the link token; the token itself is never stored
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    sa.Column("purpose", sa.String(10), nullable=False),                      # verify | reset
    sa.Column("expires_at", sa.Float, nullable=False),
    sa.Column("used_at", sa.Float),
)


feedback = sa.Table(                                                          # bug reports and ideas, read by admins
    "feedback", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="SET NULL")),
    sa.Column("t", sa.Float, nullable=False, index=True),
    sa.Column("kind", sa.String(10), nullable=False),                         # bug | idea | other
    sa.Column("message", sa.Text, nullable=False),
    sa.Column("page", sa.String(200), nullable=False, server_default=""),     # where in the app they were
    sa.Column("context", sa.String(1000), nullable=False, server_default=""), # e.g. the error they were looking at
    sa.Column("status", sa.String(10), nullable=False, server_default="new", index=True),  # new | seen | done
    sa.Column("updated_at", sa.Float, nullable=False),
)
notices = sa.Table(                                                           # the bell: things worth telling someone about
    "notices", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sa.Column("t", sa.Float, nullable=False),
    sa.Column("kind", sa.String(20), nullable=False),                         # live | clips | post | account | feedback
    sa.Column("title", sa.String(160), nullable=False),
    sa.Column("body", sa.String(400), nullable=False, server_default=""),
    sa.Column("link", sa.String(200), nullable=False, server_default=""),
    sa.Column("ref", sa.String(80)),                                          # set when it must only be sent once
    sa.Column("read_at", sa.Float),
    sa.Index("notices_user_t", "user_id", "t"),
)


admin_log = sa.Table(                                                         # what admins did, never edited
    "admin_log", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("t", sa.Float, nullable=False, index=True),
    sa.Column("admin_id", sa.String(40), nullable=False),
    sa.Column("action", sa.String(30), nullable=False),                       # disable | enable | delete | role:admin | role:user
    sa.Column("target_id", sa.String(40)),
    sa.Column("detail", sa.String(300), nullable=False, server_default=""),
)


# ---------------------------------------------------------------- Earn: paid clipping campaigns
earn_campaigns = sa.Table(                                                    # one campaign a creator or brand pays for
    "earn_campaigns", meta,
    sa.Column("id", sa.String(24), primary_key=True),
    sa.Column("slug", sa.String(60), nullable=False, unique=True),
    sa.Column("title", sa.String(120), nullable=False),
    sa.Column("creator_name", sa.String(120), nullable=False, server_default=""),
    sa.Column("creator_url", sa.String(300), nullable=False, server_default=""),
    sa.Column("tagline", sa.String(200), nullable=False, server_default=""),
    sa.Column("brief", sa.Text, nullable=False, server_default=""),
    sa.Column("rules", sa.Text, nullable=False, server_default=""),           # one rule per line
    sa.Column("sources", sa.Text, nullable=False, server_default=""),         # one link per line: streams, VODs, drive folders
    sa.Column("platforms", sa.String(80), nullable=False, server_default="youtube,instagram,x"),
    sa.Column("required_tag", sa.String(80), nullable=False, server_default=""),   # must appear in the caption, e.g. @creator
    sa.Column("category", sa.String(40), nullable=False, server_default="Gaming"),
    sa.Column("rate_per_1k", sa.Float, nullable=False, server_default="0"),   # rupees per 1,000 verified views
    sa.Column("min_views", sa.Integer, nullable=False, server_default="0"),   # clips under this earn nothing
    sa.Column("max_per_clip", sa.Float, nullable=False, server_default="0"),  # 0 = no cap
    sa.Column("budget", sa.Float, nullable=False, server_default="0"),        # the most that will ever be paid out
    sa.Column("hold_days", sa.Integer, nullable=False, server_default="7"),   # views are counted this many days after posting
    sa.Column("status", sa.String(10), nullable=False, server_default="draft"),    # draft | live | paused | ended
    sa.Column("starts_at", sa.Float),
    sa.Column("ends_at", sa.Float),
    sa.Column("has_cover", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("accent", sa.String(9), nullable=False, server_default="#C6F432"),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("updated_at", sa.Float, nullable=False),
)
earn_profiles = sa.Table(                                                     # a clipper's payout details and handles
    "earn_profiles", meta,
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("display_name", sa.String(60), nullable=False, server_default=""),
    sa.Column("whatsapp", sa.String(24), nullable=False, server_default=""),
    sa.Column("upi", sa.String(80), nullable=False, server_default=""),
    sa.Column("youtube", sa.String(80), nullable=False, server_default=""),
    sa.Column("instagram", sa.String(80), nullable=False, server_default=""),
    sa.Column("x", sa.String(80), nullable=False, server_default=""),
    sa.Column("tiktok", sa.String(80), nullable=False, server_default=""),
    sa.Column("city", sa.String(60), nullable=False, server_default=""),
    sa.Column("updated_at", sa.Float, nullable=False),
)
earn_members = sa.Table(                                                      # who joined which campaign
    "earn_members", meta,
    sa.Column("campaign_id", sa.String(24), sa.ForeignKey("earn_campaigns.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("joined_at", sa.Float, nullable=False),
)
earn_submissions = sa.Table(                                                  # one posted clip, sent in for payment
    "earn_submissions", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("campaign_id", sa.String(24), sa.ForeignKey("earn_campaigns.id", ondelete="CASCADE"), nullable=False, index=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    sa.Column("platform", sa.String(12), nullable=False),                     # youtube | instagram | x | tiktok
    sa.Column("url", sa.String(400), nullable=False),
    sa.Column("video_key", sa.String(80), nullable=False),                    # platform:id, the same clip sent twice is refused
    sa.Column("note", sa.String(300), nullable=False, server_default=""),
    sa.Column("submitted_at", sa.Float, nullable=False),
    sa.Column("posted_at", sa.Float),                                         # from the platform when it can tell us
    sa.Column("views", sa.Integer, nullable=False, server_default="0"),
    sa.Column("views_at", sa.Float),
    sa.Column("views_source", sa.String(10), nullable=False, server_default=""),   # api | manual
    sa.Column("checks", sa.Text, nullable=False, server_default="{}"),        # what the automatic cross-check found (JSON)
    sa.Column("has_proof", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("status", sa.String(10), nullable=False, server_default="pending", index=True),  # pending | approved | rejected | paid
    sa.Column("amount", sa.Float, nullable=False, server_default="0"),        # fixed when approved
    sa.Column("review_note", sa.String(300), nullable=False, server_default=""),
    sa.Column("reviewed_at", sa.Float),
    sa.Column("payout_id", sa.Integer),
    sa.UniqueConstraint("campaign_id", "video_key", name="earn_one_clip_once"),
)
earn_payouts = sa.Table(                                                      # money sent to a clipper
    "earn_payouts", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    sa.Column("amount", sa.Float, nullable=False),
    sa.Column("method", sa.String(20), nullable=False, server_default="UPI"),
    sa.Column("ref", sa.String(80), nullable=False, server_default=""),       # UTR or transaction id
    sa.Column("upi", sa.String(80), nullable=False, server_default=""),
    sa.Column("clips", sa.Integer, nullable=False, server_default="0"),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("admin_id", sa.String(40), nullable=False, server_default=""),
)


def init():
    meta.create_all(engine)


def now() -> float:
    return time.time()
