# -*- coding: utf-8 -*-
"""Merge wordEmojis-batch9.json (271 missing words) into wordEmojis.json."""
import json, sys
from pathlib import Path

DATA = Path(r"D:\10-English-Book\src\data")
MAIN = DATA / "wordEmojis.json"
B9 = DATA / "wordEmojis-batch9.json"

main = json.loads(MAIN.read_text(encoding="utf-8"))
b9 = json.loads(B9.read_text(encoding="utf-8"))

before = len(main)
added = 0
for k, v in b9.items():
    if k in main:
        print(f"OVERWRITE: {k} (was {main[k]!r}, now {v!r})", file=sys.stderr)
    main[k] = v
    added += 1

MAIN.write_text(json.dumps(main, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
print(f"before: {before}  added: {added}  after: {len(main)}", file=sys.stderr)
