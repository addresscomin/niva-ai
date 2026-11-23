"""yt-dlp wrappers. Poori stream download nahi hoti:
- fetch_info: sirf metadata (duration, live?)
- fetch_audio: sirf audio (transcript ke liye, chhota file)
- fetch_section: sirf chune hue scene ka video range
"""
import json, subprocess
from pathlib import Path
from . import config


def _yt(*extra):
    base = ["yt-dlp", "--no-playlist", "--no-warnings"]
    if config.YT_COOKIES_FILE:
        base += ["--cookies", config.YT_COOKIES_FILE]
    return base + list(extra)


def fetch_info(url):
    r = subprocess.run(_yt("--skip-download", "--dump-single-json", url),
                       capture_output=True, text=True, check=True, timeout=300)
    j = json.loads(r.stdout)
    return {
        "title": j.get("title", ""),
        "duration": float(j.get("duration") or 0),
        "is_live": j.get("live_status") in ("is_live", "is_upcoming"),
    }


def fetch_audio(url, job_dir: Path) -> Path:
    subprocess.run(_yt("-f", "bestaudio/best", "-x", "--audio-format", "mp3", "--audio-quality", "96K",
                       "-o", str(job_dir / "audio.%(ext)s"), url), check=True)
    out = job_dir / "audio.mp3"
    if not out.exists():
        raise RuntimeError("Audio download nahi hua")
    return out


def has_video(p) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_type", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return "video" in r.stdout


def fetch_section(url, start, end, job_dir: Path, name: str) -> Path:
    """Sirf start..end ka video range download karo (keyframe-accurate cut)."""
    subprocess.run(_yt("-f", "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
                       "--download-sections", f"*{start:.2f}-{end:.2f}", "--force-keyframes-at-cuts",
                       "--merge-output-format", "mp4", "-o", str(job_dir / f"{name}.%(ext)s"), url),
                   check=True)
    found = sorted(job_dir.glob(f"{name}.*"))
    if not found:
        raise RuntimeError("Clip section download nahi hua")
    out = next((f for f in found if f.suffix == ".mp4"), found[0])
    if not has_video(out):
        out.unlink(missing_ok=True)
        raise RuntimeError("Video stream nahi mila (sirf audio aaya). Dusra link ya cookies try karo.")
    return out
