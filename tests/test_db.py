import uuid
from app import config, db


def _new_user():
    token = db.signup(f"t{uuid.uuid4().hex[:10]}@example.invalid", "strong-pass-123")
    assert token
    return token, db.user(token)["id"]


def test_reserve_settle_and_daily_cap():
    token, uid = _new_user()
    cap = config.DAILY_CLIP_LIMIT
    first = db.reserve_job("a1b2c3d4e5f6", uid, 15)
    assert first == min(15, cap)
    db.settle_job("a1b2c3d4e5f6", 3)
    assert db.user(token)["clips_used_today"] == 3
    second = db.reserve_job("b1b2c3d4e5f6", uid, 50)
    assert second == cap - 3
    assert db.reserve_job("c1b2c3d4e5f6", uid, 5) == 0
    assert db.user(token)["remaining_today"] == 0


def test_failed_job_refunds_everything():
    token, uid = _new_user()
    assert db.reserve_job("d1e2d3c4b5a6", uid, 7) == min(7, config.DAILY_CLIP_LIMIT)
    db.settle_job("d1e2d3c4b5a6", 0)
    assert db.user(token)["clips_used_today"] == 0


def test_settle_is_idempotent():
    token, uid = _new_user()
    db.reserve_job("e1e2d3c4b5a6", uid, 4)
    db.settle_job("e1e2d3c4b5a6", 2)
    db.settle_job("e1e2d3c4b5a6", 0)  # dobara call par kuch refund nahi hona chahiye
    assert db.user(token)["clips_used_today"] == 2
