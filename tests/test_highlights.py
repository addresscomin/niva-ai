from app.highlights import normalise, parse_json_list, pick_non_overlapping


def test_parse_handles_code_fences():
    txt = '```json\n[{"start":1,"end":30,"title":"x","score":8}]\n```'
    assert len(parse_json_list(txt)) == 1


def test_parse_garbage_returns_empty():
    assert parse_json_list("nope") == []
    assert parse_json_list(None) == []


def test_normalise_clamps_to_clip_length():
    c = [{"start": 0, "end": 5, "title": "a", "score": 5}, {"start": 10, "end": 500, "title": "b", "score": 7}]
    out = normalise(c, duration=300, lmin=10, lmax=60)
    assert out[0]["end"] - out[0]["start"] == 10
    assert out[1]["end"] - out[1]["start"] == 60


def test_non_overlapping_keeps_best_scores():
    cands = [
        {"start": 0, "end": 30, "score": 9, "title": "a"},
        {"start": 10, "end": 40, "score": 8, "title": "b"},
        {"start": 50, "end": 80, "score": 7, "title": "c"},
    ]
    assert [c["title"] for c in pick_non_overlapping(cands, 5)] == ["a", "c"]
