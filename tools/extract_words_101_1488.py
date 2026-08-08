# -*- coding: utf-8 -*-
"""Extract single English words 101-1488 from vocab CSV (skip header, multi-word phrases, Chinese markers)."""
import json, sys, re
from pathlib import Path

CSV = Path(r"D:\10-English-Book\public\词源\上海中考英文词汇表_完整版.csv")
OUT = Path(r"D:\10-English-Book\tools\words_101_1488.json")

# single English word: only a-z letters, possibly hyphen
WORD_RE = re.compile(r"^[a-z][a-z\-']*$")

words = []
with CSV.open("r", encoding="utf-8-sig") as f:  # strip BOM
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) < 2:
            continue
        w = parts[1].strip()
        if not w or w == "单词":  # header
            continue
        if not WORD_RE.match(w):
            # skip multi-word phrases and proper-noun markers
            continue
        words.append(w)

# dedup
seen, uniq = set(), []
for w in words:
    if w not in seen:
        seen.add(w); uniq.append(w)

print(f"unique single English words: {len(uniq)}", file=sys.stderr)
print(f"first 5: {uniq[:5]}", file=sys.stderr)
print(f"last 5: {uniq[-5:]}", file=sys.stderr)

# skip batch1 (100 words we already have)
batch1 = set()
batch1_path = Path(r"D:\10-English-Book\src\data\wordEmojis-batch1.json")
b1 = json.loads(batch1_path.read_text(encoding="utf-8"))
for k in b1:
    if k != "_meta":
        batch1.add(k)

remaining = [w for w in uniq if w not in batch1]
print(f"after batch1 ({len(batch1)}): {len(remaining)}", file=sys.stderr)

OUT.write_text(json.dumps(remaining, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote: {OUT}", file=sys.stderr)
