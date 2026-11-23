import hashlib, json, secrets, sqlite3, threading, time, datetime
from contextlib import contextmanager
from . import config

DB_PATH = config.DATA / "app.db"
_lock = threading.RLock()
SESSION_TTL = 60 * 60 * 24 * 30


def _conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


@contextmanager
def _db():
    with _lock:
        c = _conn()
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()


with _db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT NOT NULL,
      salt TEXT NOT NULL, created REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY, uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      expires REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS daily_usage(
      uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, day TEXT NOT NULL,
      used INTEGER NOT NULL DEFAULT 0 CHECK(used >= 0), PRIMARY KEY(uid, day));
    CREATE TABLE IF NOT EXISTS jobs(
      id TEXT PRIMARY KEY, uid INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', clips TEXT NOT NULL DEFAULT '[]',
      created REAL NOT NULL, day TEXT NOT NULL, reserved INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX IF NOT EXISTS jobs_uid_created ON jobs(uid, created DESC);
    CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires);
    """)


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _h(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 300000).hex()


def signup(email, pw):
    salt = secrets.token_hex(16)
    try:
        with _db() as c:
            c.execute("INSERT INTO users(email,pw,salt,created) VALUES(?,?,?,?)",
                      (email, _h(pw, salt), salt, time.time()))
    except sqlite3.IntegrityError:
        return None
    return login(email, pw)


def login(email, pw):
    with _db() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row or not secrets.compare_digest(row["pw"], _h(pw, row["salt"])):
            return None
        token = secrets.token_urlsafe(32)
        c.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
        c.execute("INSERT INTO sessions(token,uid,expires) VALUES(?,?,?)",
                  (token, row["id"], time.time() + SESSION_TTL))
        return token


def logout(token):
    if token:
        with _db() as c:
            c.execute("DELETE FROM sessions WHERE token=?", (token,))


def _used_today(c, uid):
    row = c.execute("SELECT used FROM daily_usage WHERE uid=? AND day=?", (uid, today())).fetchone()
    return row["used"] if row else 0


def user(token):
    if not token:
        return None
    with _db() as c:
        row = c.execute("SELECT u.id, u.email FROM sessions s JOIN users u ON u.id=s.uid "
                        "WHERE s.token=? AND s.expires>?", (token, time.time())).fetchone()
        if not row:
            return None
        used = _used_today(c, row["id"])
    return {"id": row["id"], "email": row["email"], "clips_used_today": used,
            "daily_limit": config.DAILY_CLIP_LIMIT,
            "remaining_today": max(0, config.DAILY_CLIP_LIMIT - used)}


def reserve_job(jid, uid, want):
    """Aaj ke limit me se 'want' clips reserve karo. Jo mile wahi return hota hai (0 = limit khatam)."""
    day = today()
    with _db() as c:
        used = _used_today(c, uid)
        n = max(0, min(want, config.DAILY_CLIP_LIMIT - used))
        if n == 0:
            return 0
        c.execute("INSERT INTO daily_usage(uid,day,used) VALUES(?,?,?) "
                  "ON CONFLICT(uid,day) DO UPDATE SET used=used+excluded.used", (uid, day, n))
        c.execute("INSERT INTO jobs(id,uid,status,created,day,reserved) VALUES(?,?,?,?,?,?)",
                  (jid, uid, "queued", time.time(), day, n))
        return n


def settle_job(jid, produced):
    """Job khatam hone par jitne clips nahi bane, unka reservation wapas do."""
    with _db() as c:
        row = c.execute("SELECT uid, day, reserved FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row or row["reserved"] == 0:
            return
        refund = max(0, row["reserved"] - produced)
        if refund:
            c.execute("UPDATE daily_usage SET used=used-? WHERE uid=? AND day=?",
                      (refund, row["uid"], row["day"]))
        c.execute("UPDATE jobs SET reserved=0 WHERE id=?", (jid,))


def job_set(jid, status=None, error=None, clips=None):
    sets, vals = [], []
    if status is not None: sets.append("status=?"); vals.append(status)
    if error is not None: sets.append("error=?"); vals.append(error)
    if clips is not None: sets.append("clips=?"); vals.append(json.dumps(clips))
    if not sets: return
    with _db() as c:
        c.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id=?", (*vals, jid))


def _j(row):
    d = dict(row)
    d.pop("reserved", None); d.pop("day", None)
    d["clips"] = json.loads(d["clips"] or "[]")
    return d


def job_get(jid):
    with _db() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    return _j(row) if row else None


def jobs_of(uid):
    with _db() as c:
        rows = c.execute("SELECT * FROM jobs WHERE uid=? ORDER BY created DESC LIMIT 30", (uid,)).fetchall()
    return [_j(r) for r in rows]


def oauth_login(email):
    """Create or sign in a user whose email was verified by the OAuth provider."""
    email = email.strip().lower()
    with _db() as c:
        row = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            salt = secrets.token_hex(16)
            random_pw = secrets.token_urlsafe(48)
            cur = c.execute("INSERT INTO users(email,pw,salt,created) VALUES(?,?,?,?)",
                            (email, _h(random_pw, salt), salt, time.time()))
            uid = cur.lastrowid
        else:
            uid = row["id"]
        token = secrets.token_urlsafe(32)
        c.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
        c.execute("INSERT INTO sessions(token,uid,expires) VALUES(?,?,?)",
                  (token, uid, time.time() + SESSION_TTL))
        return token


def create_password_reset(email):
    with _db() as c:
        row = c.execute("SELECT id FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if not row:
            return None
        raw = secrets.token_urlsafe(32)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        c.execute("DELETE FROM password_resets WHERE expires < ?", (time.time(),))
        c.execute("INSERT INTO password_resets(token_hash,uid,expires) VALUES(?,?,?)",
                  (digest, row["id"], time.time() + 1800))
        return raw


def reset_password(raw_token, new_password):
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    salt = secrets.token_hex(16)
    with _db() as c:
        row = c.execute("SELECT uid FROM password_resets WHERE token_hash=? AND expires>?",
                        (digest, time.time())).fetchone()
        if not row:
            return False
        c.execute("UPDATE users SET pw=?,salt=? WHERE id=?",
                  (_h(new_password, salt), salt, row["uid"]))
        c.execute("DELETE FROM password_resets WHERE uid=?", (row["uid"],))
        c.execute("DELETE FROM sessions WHERE uid=?", (row["uid"],))
        return True
