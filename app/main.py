import re, shutil, threading, time, uuid, os
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Form, UploadFile, File, Request, Response, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import config, db
from .captions import STYLES, FONT_NAMES, POSITIONS
from .pipeline import run, render_one

app = FastAPI(title="ReelForge", version="2.0.0")
SEM = threading.Semaphore(config.WORKERS)
ALLOWED_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "vimeo.com", "www.vimeo.com"}
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"


class Cred(BaseModel):
    email: str
    password: str


class Edit(BaseModel):
    text: str
    style: str = "hype"
    font: str = ""
    position: str = "bottom"
    start: float
    end: float


def me(req: Request):
    u = db.user(req.cookies.get("t"))
    if not u:
        raise HTTPException(401, "Pehle login karo")
    return u


def _cookie(resp, token):
    resp.set_cookie("t", token, httponly=True, secure=COOKIE_SECURE, samesite="lax",
                    max_age=60 * 60 * 24 * 30, path="/")


def _valid_opts(layout, style, font, position, min_sec, max_sec, count, dub, mute=False):
    if min_sec < config.CLIP_MIN_SEC or max_sec > config.CLIP_MAX_SEC or min_sec > max_sec:
        raise HTTPException(400, f"Clip length {config.CLIP_MIN_SEC}-{config.CLIP_MAX_SEC} second ke beech rakho")
    if dub and not config.DUBBING_ENABLED:
        raise HTTPException(400, "Hindi dubbing abhi server par band hai")
    return {
        "layout": layout if layout in ("blur", "crop") else "blur",
        "style": style if style in STYLES else "hype",
        "font": font if font in FONT_NAMES else "",
        "position": position if position in POSITIONS else "bottom",
        "min_sec": min_sec, "max_sec": max_sec,
        "count": max(1, min(count, config.MAX_CLIPS_PER_JOB)),
        "dub": bool(dub),
        "mute": bool(mute),
    }


@app.post("/api/signup")
def signup(c: Cred, resp: Response):
    e = c.email.strip().lower()
    if len(e) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e) or not 8 <= len(c.password) <= 128:
        raise HTTPException(400, "Valid email aur 8-128 character password do")
    token = db.signup(e, c.password)
    if not token:
        raise HTTPException(400, "Ye email pehle se registered hai")
    _cookie(resp, token)
    return db.user(token)


@app.post("/api/login")
def login(c: Cred, resp: Response):
    token = db.login(c.email.strip().lower(), c.password)
    if not token:
        raise HTTPException(400, "Email ya password galat hai")
    _cookie(resp, token)
    return db.user(token)


@app.post("/api/logout")
def logout(req: Request, resp: Response):
    db.logout(req.cookies.get("t"))
    resp.delete_cookie("t", path="/")
    return {}


@app.get("/api/me")
def whoami(u=Depends(me)):
    return u


@app.get("/api/config")
def public_config():
    return {
        "styles": {k: v["label"] for k, v in STYLES.items()},
        "fonts": list(FONT_NAMES),
        "positions": list(POSITIONS),
        "clip_min": config.CLIP_MIN_SEC,
        "clip_max": config.CLIP_MAX_SEC,
        "max_per_job": config.MAX_CLIPS_PER_JOB,
        "daily_limit": config.DAILY_CLIP_LIMIT,
        "dubbing": config.DUBBING_ENABLED,
    }


def worker(jid, uid, url, file_path, opts):
    try:
        with SEM:
            result = run(config.DATA / jid, url, file_path, opts, progress=lambda s: db.job_set(jid, status=s))
        db.settle_job(jid, len(result))
        db.job_set(jid, status="done", clips=result)
    except Exception as exc:
        db.settle_job(jid, 0)
        db.job_set(jid, status="error", error=str(exc)[:300])


@app.post("/api/jobs")
async def create(url: str = Form(""), layout: str = Form("blur"), style: str = Form("hype"),
                 font: str = Form(""), position: str = Form("bottom"),
                 min_sec: int = Form(config.CLIP_MIN_SEC), max_sec: int = Form(60),
                 count: int = Form(10), dub: bool = Form(False), mute: bool = Form(False),
                 file: UploadFile | None = File(None), u=Depends(me)):
    has_file = bool(file and file.filename)
    if not has_file and not url.strip():
        raise HTTPException(400, "Video link ya file do")
    url = url.strip()
    if url:
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
            raise HTTPException(400, "Abhi sirf YouTube/Vimeo https links ya direct upload allowed hai")
    if has_file and Path(file.filename or "").suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(400, "MP4, MOV, MKV, WEBM ya M4V file upload karo")
    opts = _valid_opts(layout, style, font, position, min_sec, max_sec, count, dub, mute)

    jid = uuid.uuid4().hex[:12]
    reserved = db.reserve_job(jid, u["id"], opts["count"])
    if reserved < 1:
        raise HTTPException(402, f"Aaj ke {config.DAILY_CLIP_LIMIT} clips poore ho gaye. Kal phir try karo.")
    opts["count"] = reserved

    job_dir = config.DATA / jid
    job_dir.mkdir(parents=True, exist_ok=True)
    file_path = None
    if has_file:
        file_path = job_dir / ("upload" + Path(file.filename).suffix.lower())
        size = 0
        try:
            with open(file_path, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > config.MAX_UPLOAD_MB * 1024 * 1024:
                        raise HTTPException(413, f"Upload limit {config.MAX_UPLOAD_MB} MB hai")
                    out.write(chunk)
        except Exception:
            db.settle_job(jid, 0)
            db.job_set(jid, status="error", error="Upload fail")
            shutil.rmtree(job_dir, ignore_errors=True)
            raise
        finally:
            await file.close()

    threading.Thread(target=worker, args=(jid, u["id"], url or None, file_path, opts), daemon=True).start()
    return {"id": jid, "clips_reserved": reserved}


@app.get("/api/jobs")
def jobs(u=Depends(me)):
    return db.jobs_of(u["id"])


def _own(jid, u):
    if not re.fullmatch(r"[a-f0-9]{12}", jid):
        raise HTTPException(404, "Not found")
    j = db.job_get(jid)
    if not j or j["uid"] != u["id"]:
        raise HTTPException(404, "Not found")
    return j


@app.post("/api/jobs/{jid}/clips/{i}")
def edit(jid: str, i: int, e: Edit, u=Depends(me)):
    j = _own(jid, u)
    clip = next((c for c in j["clips"] if c["i"] == i), None)
    if not clip:
        raise HTTPException(404, "Clip nahi mila")
    if not config.CLIP_MIN_SEC <= e.end - e.start <= config.CLIP_MAX_SEC or e.start < 0:
        raise HTTPException(400, f"Clip {config.CLIP_MIN_SEC}-{config.CLIP_MAX_SEC} second ka rakho")
    if e.style not in STYLES:
        raise HTTPException(400, "Invalid caption style")
    with SEM:
        new = render_one(config.DATA / jid, clip, e.text[:3000], e.style, e.font if e.font in FONT_NAMES else "",
                         e.position if e.position in POSITIONS else "bottom", e.start, e.end,
                         dub=clip.get("dub", False))
    new["v"] = int(time.time())
    j["clips"] = [new if c["i"] == i else c for c in j["clips"]]
    db.job_set(jid, clips=j["clips"])
    return new


@app.get("/files/{jid}/{name}")
def files(jid: str, name: str, u=Depends(me)):
    _own(jid, u)
    safe = Path(name).name
    base = (config.DATA / jid).resolve()
    target = (base / safe).resolve()
    if target.parent != base or not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target, filename=safe)


app.mount("/", StaticFiles(directory="web", html=True), name="web")
