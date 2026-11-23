import json, subprocess
from pathlib import Path
from . import config, download, dubbing
from .transcribe import transcribe
from .highlights import pick_highlights
from .render import render_clip
from .captions import retext, FONT_NAMES


def duration_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _in(words, a, b):
    return [w for w in words if w["start"] >= a - .01 and w["end"] <= b + .01]


def _upload(job_dir: Path):
    ups = sorted(job_dir.glob("upload.*"))
    return ups[0] if ups else None


def _render_one(job_dir, idx, clip, words, url, src_file, opts, text=None):
    """Ek clip render. URL job me sirf is clip ka section download hota hai, phir delete."""
    s, e = float(clip["start"]), float(clip["end"])
    dur = e - s
    if src_file:
        src, seek, tmp = src_file, s, False
    else:
        src = download.fetch_section(url, s, e, job_dir, f"sec_{idx}")
        seek, tmp = 0, True

    ws = _in(words, s, e)
    audio, hindi = None, None
    dub = opts["dub"]
    if dub:
        hindi = text if text is not None else dubbing.translate_hindi(" ".join(w["w"] for w in ws))
        mp3 = dubbing.speak(hindi, job_dir / f"dub_{idx}.mp3")
        audio = dubbing.fit_audio(mp3, dur, job_dir / f"dub_{idx}.m4a")
        ws = retext(ws, hindi, s, e)
    elif text is not None and text.strip() != " ".join(w["w"] for w in ws).strip():
        ws = retext(ws, text, s, e)

    font = "devanagari" if dub else (opts.get("font") or None)
    try:
        render_clip(src, ws, {"start": s, "end": e}, job_dir, idx, opts["layout"], opts["style"],
                    font=font, position=opts["position"], seek=seek, audio=audio,
                    mute=opts.get("mute", False), aspect_ratio=opts.get("aspect_ratio", "9:16"))
    finally:
        if tmp:
            Path(src).unlink(missing_ok=True)

    return {"i": idx, "file": f"reel_{idx}.mp4", "title": clip.get("title", f"Clip {idx + 1}"),
            "score": clip.get("score", 0), "start": s, "end": e, "v": 0,
            "layout": opts["layout"], "aspect_ratio": opts.get("aspect_ratio", "9:16"), "style": opts["style"], "font": font or "",
            "position": opts["position"], "dub": dub, "mute": opts.get("mute", False),
            "text": hindi if dub else " ".join(w["w"] for w in ws)}


def run(job_dir: Path, url=None, file=None, opts=None, progress=lambda s: None):
    """Full pipeline. opts: layout, style, font, position, min_sec, max_sec, count, dub."""
    opts = opts or {}
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "meta.json").write_text(json.dumps({"url": url}))

    if file:
        analysis, dur = Path(file), duration_of(file)
    else:
        progress("Video info le raha hai")
        info = download.fetch_info(url)
        if info["is_live"]:
            raise ValueError("Live stream abhi supported nahi. Stream khatam hone ke baad link do.")
        dur = info["duration"]
        if dur <= 0:
            raise ValueError("Video ki length nahi mili")
        progress("Stream ka sirf audio le raha hai (poori video nahi)")
        analysis = download.fetch_audio(url, job_dir)

    progress("Transcript ban raha hai (lambi stream me time lagega)")
    words = transcribe(analysis, progress=progress)
    (job_dir / "words.json").write_text(json.dumps(words))

    picks = pick_highlights(analysis, words, dur, opts["min_sec"], opts["max_sec"], opts["count"], progress)
    if not picks:
        raise ValueError("Koi moment nahi mila")

    src_file = _upload(job_dir) if file else None
    res = []
    for i, c in enumerate(picks):
        progress(f"Clip {i + 1}/{len(picks)} render ho raha hai")
        res.append(_render_one(job_dir, i, c, words, url, src_file, opts))
    return res


def render_one(job_dir: Path, clip, text, style, font, position, start, end, dub=False):
    """Caption edit / timing change ke baad ek clip dobara render."""
    meta = json.loads((job_dir / "meta.json").read_text())
    words = json.loads((job_dir / "words.json").read_text())
    src_file = _upload(job_dir)
    opts = {"layout": clip.get("layout", "blur"), "aspect_ratio": clip.get("aspect_ratio", "9:16"), "style": style, "font": font, "position": position,
            "dub": dub or clip.get("dub", False), "mute": clip.get("mute", False)}
    c = {**clip, "start": start, "end": end}
    changed_text = text.strip() != clip.get("text", "").strip()
    return _render_one(job_dir, clip["i"], c, words, meta.get("url"), src_file, opts,
                       text=text if (changed_text or opts["dub"]) else None)
