"""Best moments dhoondhna.
1) Transcript ko 15-min chunks me LLM ko bhejo (lambi stream ka poora transcript cover hota hai)
2) Sab candidates ko clip length ke hisaab se clamp karo, overlap hatao, top N lo
3) Agar LLM na chale to audio-energy fallback
"""
import json, math, subprocess
import numpy as np
from . import config
from .llm import ask

SR = 8000
WINDOW_SEC = 900  # 15 min


def audio_energy(path):
    """Per-second RMS loudness. Streaming me padhta hai, poora audio RAM me nahi aata."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, carry = [], b""
    step = SR * 2 * 60  # 1 minute ke bytes
    try:
        while True:
            buf = proc.stdout.read(step)
            if not buf:
                break
            buf = carry + buf
            usable = len(buf) // (2 * SR) * (2 * SR)
            carry = buf[usable:]
            a = np.frombuffer(buf[:usable], dtype=np.int16).astype(np.float32)
            n = a.size // SR
            if n:
                out.append(np.sqrt((a[:n * SR].reshape(n, SR) ** 2).mean(axis=1)))
    finally:
        proc.stdout.close()
        proc.wait()
    if proc.returncode:
        raise RuntimeError("Audio energy read fail")
    return np.concatenate(out) if out else np.zeros(1)


def energy_candidates(path, duration, target, limit):
    e = audio_energy(path)
    win = max(3, min(int(target), len(e)))
    scores = np.convolve(e, np.ones(win) / win, mode="valid") if len(e) > win else e
    picks, taken = [], np.zeros(len(scores) + 2 * win, bool)
    for i in np.argsort(scores)[::-1]:
        i = int(i)
        if taken[max(0, i - win): i + win].any():
            continue
        taken[i:i + win] = True
        s = float(i)
        picks.append({"start": s, "end": float(min(s + target, duration)),
                      "title": f"Moment {len(picks) + 1}", "score": 5.0})
        if len(picks) >= limit:
            break
    return sorted(picks, key=lambda x: x["start"])


def _lines(words, lo, hi, gap=6):
    lines, cur, t0 = [], [], 0.0
    for w in words:
        if w["start"] < lo or w["start"] >= hi:
            continue
        if not cur:
            t0 = w["start"]
        cur.append(w["w"])
        if w["end"] - t0 > gap:
            lines.append(f"[{t0:.0f}] {' '.join(cur)}")
            cur = []
    if cur:
        lines.append(f"[{t0:.0f}] {' '.join(cur)}")
    return "\n".join(lines)[:60000]


def parse_json_list(txt):
    if not txt:
        return []
    try:
        a, b = txt.index("["), txt.rindex("]") + 1
        data = json.loads(txt[a:b])
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def normalise(cands, duration, lmin, lmax):
    out = []
    for c in cands:
        try:
            s, e = float(c["start"]), float(c["end"])
        except (KeyError, TypeError, ValueError):
            continue
        s, e = max(0.0, s), min(e, duration)
        if e - s < lmin:
            e = min(duration, s + lmin)
        if e - s > lmax:
            e = s + lmax
        if e - s < lmin:
            continue
        try:
            score = float(c.get("score", 5) or 5)
        except (TypeError, ValueError):
            score = 5.0
        out.append({"start": s, "end": e, "title": str(c.get("title") or "Clip")[:80], "score": score})
    return out


def pick_non_overlapping(cands, limit):
    kept = []
    for c in sorted(cands, key=lambda x: (-x["score"], x["start"])):
        if any(c["start"] < k["end"] and k["start"] < c["end"] for k in kept):
            continue
        kept.append(c)
        if len(kept) >= limit:
            break
    return sorted(kept, key=lambda x: x["start"])


def llm_chunk(words, lo, hi, n, lmin, lmax):
    body = _lines(words, lo, hi)
    if not body:
        return []
    prompt = (f"Below is a transcript chunk of a long video or stream, timestamps in seconds. "
              f"Pick up to {n} self-contained, highly engaging moments that work as short vertical clips "
              f"(hype, funny, shocking, insightful, emotional, quotable). Each clip must be {lmin} to {lmax} "
              f"seconds long, start on a strong hook, end on a payoff, and stay inside this chunk. "
              f"Use the exact second values from the timestamps. Reply ONLY with a JSON array: "
              f'[{{"start": number, "end": number, "title": "catchy hook under 8 words", "score": 1-10}}]\n\n'
              + body)
    return parse_json_list(ask(prompt))


def pick_highlights(path, words, duration, lmin, lmax, limit, progress=lambda s: None):
    picked = []
    if words and duration > 0:
        n_chunks = max(1, math.ceil(duration / WINDOW_SEC))
        per_chunk = max(2, math.ceil(limit / n_chunks) + 1)
        cands = []
        for k in range(n_chunks):
            progress(f"Finding highlights with AI ({k + 1}/{n_chunks})")
            try:
                raw = llm_chunk(words, k * WINDOW_SEC, (k + 1) * WINDOW_SEC, per_chunk, lmin, lmax)
            except Exception as ex:
                print("LLM chunk failed:", ex)
                raw = []
            cands += normalise(raw, duration, lmin, lmax)
        picked = pick_non_overlapping(cands, limit)
    if not picked:
        progress("Finding highlights from audio activity")
        picked = energy_candidates(path, duration, target=(lmin + lmax) // 2, limit=limit)
    return picked
