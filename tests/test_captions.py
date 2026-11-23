from app.captions import STYLES, make_ass, retext

WORDS = [{"w": "hello{x}", "start": 0.0, "end": 0.5}, {"w": "world", "start": 0.5, "end": 1.0}]


def test_ass_header_and_escaping(tmp_path):
    p = make_ass(WORDS, 0, 1, tmp_path / "c.ass", style="hype")
    text = p.read_text(encoding="utf-8")
    assert "PlayResX: 1080" in text and "Dialogue:" in text
    assert "{x}" not in text  # user text ke braces escape hue


def test_every_style_renders(tmp_path):
    for s in STYLES:
        make_ass(WORDS, 0, 1, tmp_path / f"{s}.ass", style=s)
        assert "Dialogue:" in (tmp_path / f"{s}.ass").read_text(encoding="utf-8")


def test_hindi_font_is_used(tmp_path):
    p = make_ass(WORDS, 0, 1, tmp_path / "h.ass", style="hype", font="devanagari")
    assert "Noto Sans Devanagari" in p.read_text(encoding="utf-8")


def test_retext_maps_user_text_across_timings():
    out = retext(WORDS, "one two three", 0.0, 3.0)
    assert [w["w"] for w in out] == ["one", "two", "three"]
    assert out[0]["start"] == 0.0 and out[-1]["end"] == 1.0
