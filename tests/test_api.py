from fastapi.testclient import TestClient
from app import config
from app.main import app

client = TestClient(app)


def test_public_config():
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body["clip_max"] == config.CLIP_MAX_SEC and body["daily_limit"] == config.DAILY_CLIP_LIMIT


def test_jobs_require_login():
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/jobs", data={"url": "https://youtu.be/x"}).status_code == 401
