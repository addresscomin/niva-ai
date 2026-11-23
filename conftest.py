import os
import tempfile

# Tests ko alag temp data folder do, taaki real app.db ko touch na ho.
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="reelforge-test-"))
os.environ.setdefault("DAILY_CLIP_LIMIT", "20")
