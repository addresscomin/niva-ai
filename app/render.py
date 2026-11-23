import subprocess
from pathlib import Path
from .captions import make_ass
from .download import has_video


def render_clip(src: Path, words, clip, out_dir: Path, idx: int, layout="blur", style="hype",
                font=None, position="bottom", seek=None, audio=None, prefix="reel", mute=False, aspect_ratio="9:16"):
    """Clip render: 9:16, styled captions, optional dub audio. Koi watermark nahi."""
    start, end = float(clip["start"]), float(clip["end"])
    dur = end - start
    seek = start if seek is None else seek
    width, height = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
    ass = out_dir / f"c{idx}.ass"
    make_ass(words, start, end, ass, style=style, position=position, font=font, resolution=(width, height))
    out = out_dir / f"{prefix}_{idx}.mp4"

    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{seek:.3f}", "-i", str(src.resolve())]
    if audio and not mute:
        cmd += ["-i", str(Path(audio).resolve())]
    if layout == "crop":
        vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},ass={ass.name}"
        cmd += ["-vf", vf, "-map", "0:v:0"]
    else:
        fc = (f"[0:v]split[a][b];"
              f"[a]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},boxblur=30:5[bg];"
              f"[b]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,ass={ass.name}[v]")
        cmd += ["-filter_complex", fc, "-map", "[v]"]
    if mute:
        cmd += ["-an"]
    elif audio:
        cmd += ["-map", "1:a:0", "-af", "apad"]
    else:
        cmd += ["-map", "0:a:0?"]
    cmd += ["-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "2",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out.name]
    subprocess.run(cmd, cwd=out_dir, check=True)
    if not has_video(out):
        raise RuntimeError("Clip me video stream nahi bana")
    return out
