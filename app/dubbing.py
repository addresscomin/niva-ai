"""BETA: English transcript -> Hindi text -> Hindi TTS (edge-tts, free) -> clip audio.
Voice ka quality/choice baad me (DUB_VOICE env). Original audio is replace hota hai."""
import asyncio, json, subprocess
from pathlib import Path
from . import config
from .llm import ask


def translate_hindi(text):
    if not text.strip():
        return ""
    out = ask("Translate this spoken English into natural, conversational Hindi written in Devanagari. "
              "Keep it short and keep the same meaning. Reply ONLY with the Hindi text.\n\n" + text)
    return (out or "").strip()


def speak(text, out_path: Path) -> Path:
    import edge_tts  # lazy import
    async def _go():
        await edge_tts.Communicate(text, config.DUB_VOICE).save(str(out_path))
    asyncio.run(_go())
    return out_path


def _duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def fit_audio(mp3: Path, target: float, out: Path) -> Path:
    """Agar Hindi audio clip se lamba hai to thoda tez karo (max 1.5x), phir clip length par cut/pad."""
    d = _duration(mp3)
    tempo = min(1.5, max(1.0, d / target)) if target > 0 else 1.0
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-af", f"atempo={tempo:.3f},apad",
                    "-t", f"{target:.3f}", "-ac", "2", "-ar", "44100", "-c:a", "aac", str(out)], check=True)
    return out
