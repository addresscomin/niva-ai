"""CLI: python cli.py <youtube-url> [--layout blur|crop] [--style hype] [--min 20] [--max 50] [--count 10]"""
import argparse
from pathlib import Path
from app.pipeline import run

p = argparse.ArgumentParser()
p.add_argument("url")
p.add_argument("--layout", default="blur")
p.add_argument("--style", default="hype")
p.add_argument("--font", default="")
p.add_argument("--position", default="bottom")
p.add_argument("--min", type=int, default=20, dest="min_sec")
p.add_argument("--max", type=int, default=50, dest="max_sec")
p.add_argument("--count", type=int, default=10)
a = p.parse_args()
opts = vars(a).copy()
opts.pop("url")
res = run(Path("data/cli"), url=a.url, opts={**opts, "dub": False}, progress=print)
print(*[f"{r['file']}  {r['start']:.1f}-{r['end']:.1f}s  {r['title']}" for r in res], sep="\n")
