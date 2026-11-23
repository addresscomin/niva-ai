"""yt-dlp wrappers. Poori stream download nahi hoti:
- fetch_info: sirf metadata (duration, live?)
- fetch_audio: sirf audio (transcript ke liye, chhota file)
- fetch_section: sirf chune hue scene ka video range
"""
import json, subprocess, shutil
from pathlib import Path
from . import config


def _yt(*extra):
    base = ["yt-dlp", "--no-playlist", "--no-warnings"]
    base += ["--extractor-retries", "5", "--retries", "5", "--fragment-retries", "5", "--socket-timeout", "25"]
    if shutil.which("node"):
        base += ["--js-runtimes", "node", "--remote-components", "ejs:github"]
    if config.YT_COOKIES_FILE:
        base += ["--cookies", config.YT_COOKIES_FILE]
    return base + list(extra)


def _run(args, timeout=None):
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()

        # YouTube occasionally fails to return a player response for its default
        # client set. Retry once with a different supported client combination.
        if "Failed to extract any player response" in detail and any(
            "youtube.com" in str(arg) or "youtu.be" in str(arg) for arg in args
        ) and "--extractor-args" not in args:
            retry_args = list(args)
            retry_args[1:1] = ["--extractor-args", "youtube:player_client=web,web_safari,tv"]
            try:
                return subprocess.run(
                    retry_args, capture_output=True, text=True, check=True, timeout=timeout
                )
            except subprocess.CalledProcessError as retry_exc:
                retry_detail = (retry_exc.stderr or retry_exc.stdout or "").strip()
                detail = (detail + "\\nFallback client attempt: " + retry_detail).strip()

        detail = detail[-1800:] if detail else "No diagnostic details were returned."
        raise RuntimeError(
            "The video source could not be accessed. YouTube may be temporarily rejecting "
            "the server request, or the video may require access. Try again later or upload "
            "a video file you have permission to use. Extractor details: " + detail
        ) from exc


def fetch_info(url):
    r = _run(_yt("--skip-download", "--dump-single-json", url), timeout=300)
    j = json.loads(r.stdout)
    return {
        "title": j.get("title", ""),
        "duration": float(j.get("duration") or 0),
        "is_live": j.get("live_status") in ("is_live", "is_upcoming"),
    }


def fetch_audio(url, job_dir: Path) -> Path:
    _run(_yt("-f", "bestaudio/best", "-x", "--audio-format", "mp3", "--audio-quality", "96K",
             "-o", str(job_dir / "audio.%(ext)s"), url), timeout=900)
    out = job_dir / "audio.mp3"
    if not out.exists():
        raise RuntimeError("The audio could not be downloaded from the video source.")
    return out


def has_video(p) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_type", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return "video" in r.stdout


def fetch_section(url, start, end, job_dir: Path, name: str) -> Path:
    """Sirf start..end ka video range download karo (keyframe-accurate cut)."""
    _run(_yt("-f", "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b",
             "--download-sections", f"*{start:.2f}-{end:.2f}", "--force-keyframes-at-cuts",
             "--merge-output-format", "mp4", "-o", str(job_dir / f"{name}.%(ext)s"), url), timeout=900)
    found = sorted(job_dir.glob(f"{name}.*"))
    if not found:
        raise RuntimeError("The selected video section could not be downloaded.")
    out = next((f for f in found if f.suffix == ".mp4"), found[0])
    if not has_video(out):
        out.unlink(missing_ok=True)
        raise RuntimeError("No video stream was found. Try another public link or upload the video file.")
    return out
