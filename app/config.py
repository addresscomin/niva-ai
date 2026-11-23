import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA = Path(os.getenv("DATA_DIR", "data"))
DATA.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
CLIP_MIN_SEC = int(os.getenv("CLIP_MIN_SEC", 10))
CLIP_MAX_SEC = int(os.getenv("CLIP_MAX_SEC", 120))
MAX_CLIPS_PER_JOB = int(os.getenv("MAX_CLIPS_PER_JOB", 20))
DAILY_CLIP_LIMIT = int(os.getenv("DAILY_CLIP_LIMIT", 20))
WORKERS = int(os.getenv("WORKERS", 1))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 2048))
YT_COOKIES_FILE = os.getenv("YT_COOKIES_FILE", "")
DUBBING_ENABLED = os.getenv("DUBBING_ENABLED", "0") == "1"
DUB_VOICE = os.getenv("DUB_VOICE", "hi-IN-SwaraNeural")
