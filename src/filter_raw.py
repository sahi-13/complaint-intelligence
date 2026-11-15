"""
Shrink the huge CFPB file: keep recent complaints and blank out narratives.

Run from VS Code (Run button) or:  python src/filter_raw.py
Optional: python src/filter_raw.py --since 2026-01-01
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # the project folder, wherever you run from

p = argparse.ArgumentParser()
p.add_argument("--input", default=str(ROOT / "data" / "raw" / "complaints.csv"))
p.add_argument("--output", default=str(ROOT / "data" / "raw" / "complaints_recent.csv"))
p.add_argument("--since", default="2025-01-01")
p.add_argument("--exclude", default="credit report", help="Drop products containing this text")
args = p.parse_args()

print(f"Reading: {args.input}")
first, kept, seen = True, 0, 0
for chunk in pd.read_csv(args.input, dtype=str, chunksize=200_000, low_memory=False):
    seen += len(chunk)
    dates = pd.to_datetime(chunk["Date received"], errors="coerce")
    chunk = chunk[dates >= args.since].copy()
    chunk = chunk[~chunk["Product"].str.contains(args.exclude, case=False, na=False)]
    chunk["Consumer complaint narrative"] = pd.NA  # narratives are most of the file size
    chunk.to_csv(args.output, mode="w" if first else "a", header=first, index=False)
    first = False
    kept += len(chunk)
    print(f"read {seen:,} rows, kept {kept:,}", flush=True)

print(f"Done. Saved {kept:,} rows to {args.output}")