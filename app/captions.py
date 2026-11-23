"""ASS captions. Har style ek spec hai; naye trending styles yahin add karo."""

# hl = highlight colour (BGR, ASS format) ya None (koi highlight nahi)
STYLES = {
    "hype":       {"label": "Hype (yellow pop)",       "hl": "&H0000FFFF", "fs": 84, "outline": 6,  "upper": True,  "box": False, "font": "arial"},
    "neon":       {"label": "Neon green",              "hl": "&H0000FF00", "fs": 84, "outline": 5,  "upper": True,  "box": False, "font": "arial"},
    "fire":       {"label": "Fire orange",             "hl": "&H000080FF", "fs": 90, "outline": 6,  "upper": True,  "box": False, "font": "arial"},
    "mrbeast":    {"label": "Big bold (heavy outline)", "hl": "&H0000FFFF", "fs": 96, "outline": 10, "upper": True,  "box": False, "font": "arial"},
    "boxed":      {"label": "Boxed (black bar)",       "hl": "&H000000FF", "fs": 72, "outline": 0,  "upper": False, "box": True,  "font": "arial"},
    "clean":      {"label": "Clean white",             "hl": None,         "fs": 70, "outline": 3,  "upper": False, "box": False, "font": "arial"},
    "minimal":    {"label": "Minimal lowercase",       "hl": None,         "fs": 64, "outline": 2,  "upper": False, "box": False, "font": "arial"},
    "devanagari": {"label": "Hindi (Devanagari)",      "hl": "&H0000FFFF", "fs": 80, "outline": 6,  "upper": False, "box": False, "font": "devanagari"},
}

FONT_NAMES = {"arial": "Arial", "dejavu": "DejaVu Sans", "devanagari": "Noto Sans Devanagari"}

# alignment (ASS numpad), margin vertical
POSITIONS = {"bottom": (2, 520), "center": (5, 0), "top": (8, 260)}


def _t(s):
    s = max(s, 0)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def _esc(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def retext(ws, text, start, end):
    """User-edited (ya Hindi) text ko original timings par map karo."""
    toks = text.split()
    if not toks:
        return []
    if len(toks) == len(ws):
        return [{**w, "w": t} for w, t in zip(ws, toks)]
    a, b = (ws[0]["start"], ws[-1]["end"]) if ws else (start, end)
    d = (b - a) / len(toks)
    return [{"w": t, "start": a + i * d, "end": a + (i + 1) * d} for i, t in enumerate(toks)]


def make_ass(words, start, end, path, style="hype", per_line=3, position="bottom", font=None):
    spec = STYLES.get(style, STYLES["hype"])
    align, mv = POSITIONS.get(position, POSITIONS["bottom"])
    fname = FONT_NAMES.get(font or spec["font"], FONT_NAMES["arial"])
    primary = "&H00FFFFFF"
    back = "&HA0000000" if spec["box"] else "&H80000000"
    outline_col = back if spec["box"] else "&H00000000"
    border = 3 if spec["box"] else 1
    shadow = 0 if spec["box"] else 1
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Cap,{fname},{spec['fs']},{primary},{primary},{outline_col},{back},-1,0,0,0,100,100,0,0,"
        f"{border},{spec['outline']},{shadow},{align},60,60,{mv},1\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    fmt = (lambda x: x.upper()) if spec["upper"] else (lambda x: x)
    ws = [w for w in words if w["start"] >= start - 0.01 and w["end"] <= end + 0.01]
    hl = spec["hl"]
    out = []
    for i in range(0, len(ws), per_line):
        ch = ws[i:i + per_line]
        for j, w in enumerate(ch):
            parts = []
            for k, c in enumerate(ch):
                word = fmt(_esc(c["w"]))
                if k == j and hl:
                    # highlighted word: thoda pop animation (scale up)
                    parts.append("{\\c" + hl + "&\\fscx90\\fscy90\\t(0,140,\\fscx115\\fscy115)}" + word + "{\\r}")
                else:
                    parts.append(word)
            txt = " ".join(parts)
            a = w["start"] - start
            b = (ch[j + 1]["start"] if j + 1 < len(ch) else w["end"]) - start
            out.append(f"Dialogue: 0,{_t(a)},{_t(max(b, a + .05))},Cap,,0,0,0,,{txt}")
    path.write_text(head + "\n".join(out) + "\n", encoding="utf-8")
    return path
