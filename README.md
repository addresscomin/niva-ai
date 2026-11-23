# ReelForge v2 - AI reel clipper (personal system)

Link paste karo (YouTube/Vimeo, lambi stream bhi). Flow:

1. Sirf **audio** download hota hai (poori video nahi), usse transcript banta hai (Faster-Whisper).
2. Transcript ko 15-min chunks me AI (Gemini/Groq/OpenRouter/OpenAI/Claude, free keys bhi chalengi) ko bheja jata hai, wo best moments chunte hain.
3. Sirf chune hue scenes ka video range download hota hai, 9:16 me render hota hai, styled captions lagte hain.
4. Caption edit karke clip dobara render kar sakte ho. Koi logo/watermark nahi.

## Features
- Clip length 10 se 120 second, har clip alag length chal sakti hai (min/max).
- Clips per job 1 se 20.
- Caption styles: hype, neon, fire, mrbeast, boxed, clean, minimal, devanagari (Hindi).
- Fonts: Arial, DejaVu Sans, Noto Sans Devanagari. Position: bottom / center / top.
- Layout: blur background (gaming/landscape) ya center crop.
- Limit: har user ke liye roz `DAILY_CLIP_LIMIT` (default 20) clips. Monthly/quarter limit nahi.
- Hindi dubbing: BETA (`DUBBING_ENABLED=1`), translation + edge-tts Hindi voice. Voice quality baad me tune karenge.

## Run locally
```bash
sudo apt install ffmpeg fonts-liberation fonts-dejavu-core fonts-noto-core
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # keys daalo
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
CLI: `python cli.py "https://youtu.be/XXXX" --min 20 --max 45 --count 8 --style hype`

## Docker
```bash
docker build -t reelforge .
docker run --rm -p 8000:8000 --env-file .env -v "$PWD/data:/srv/data" reelforge
```

## Tests
`pytest -q` (ffmpeg chahiye, CI me automatic chalta hai via `.github/workflows/ci.yml`).

## Important notes
- Lambi stream ka transcript CPU par time leta hai. `WHISPER_MODEL=base` ya `tiny` karo speed ke liye.
- Live stream abhi supported nahi, stream khatam hone ke baad link do.
- YouTube kabhi-kabhi server IPs block karta hai. Fail ho to `YT_COOKIES_FILE` set karo aur `yt-dlp` update rakho.
- Sirf wahi content process karo jiska tumhare paas right ya permission ho. Doosron ke content ko republish karna copyright/YouTube terms ka issue ban sakta hai.
- Hosting: VPS par deploy karo (backend chahiye, GitHub Pages sirf static hota hai). HTTPS ke liye `COOKIE_SECURE=1` aur Caddy/Nginx reverse proxy.
- SQLite single-instance ke liye hai. Scale karna ho to PostgreSQL + proper queue.
