from . import config

_model = None


def transcribe(path, progress=lambda s: None):
    """Word-level timestamps. Lambi audio ke liye progress report karta hai."""
    global _model
    from faster_whisper import WhisperModel  # lazy import: tests/CLI me heavy dependency na lage
    if _model is None:
        _model = WhisperModel(config.WHISPER_MODEL, compute_type="int8")
    segs, _ = _model.transcribe(str(path), word_timestamps=True, vad_filter=True, beam_size=1)
    words, n = [], 0
    for s in segs:
        n += 1
        if n % 100 == 0:
            progress(f"Transcript ban raha hai: {int(s.end // 60)} min tak ho gaya")
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                words.append({"w": t, "start": float(w.start), "end": float(w.end)})
    return words
