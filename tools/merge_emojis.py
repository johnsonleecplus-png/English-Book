# -*- coding: utf-8 -*-
"""Merge batch1-8 into single wordEmojis.json, strip _meta, dedup, write .ts file too."""
import json, sys
from pathlib import Path
from collections import Counter

DATA = Path(r"D:\10-English-Book\src\data")
OUT_JSON = DATA / "wordEmojis.json"
OUT_TS = DATA / "wordEmojis.ts"

merged = {}
batches = sorted(DATA.glob("wordEmojis-batch*.json"))
print(f"batches: {[b.name for b in batches]}", file=sys.stderr)

for b in batches:
    obj = json.loads(b.read_text(encoding="utf-8"))
    n = 0
    for k, v in obj.items():
        if k.startswith("_"):
            continue
        if k in merged:
            print(f"DUP: {k} in {b.name}", file=sys.stderr)
        merged[k] = v
        n += 1
    print(f"  {b.name}: {n} entries", file=sys.stderr)

print(f"total merged: {len(merged)}", file=sys.stderr)

# emoji usage stats
usage = Counter()
for v in merged.values():
    if v:
        usage[v] += 1

print(f"unique emojis used: {len(usage)}", file=sys.stderr)
print(f"null entries: {sum(1 for v in merged.values() if v is None)}", file=sys.stderr)

# check hot emoji budget: ❤️⭐🎉🏆
hot = ["❤️", "⭐", "🎉", "🏆", "💖", "✨"]
for h in hot:
    c = usage.get(h, 0)
    flag = "⚠️ OVER" if c > 3 else "ok"
    print(f"  hot '{h}': {c} [{flag}]", file=sys.stderr)

# write JSON
OUT_JSON.write_text(
    json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True),
    encoding="utf-8"
)
print(f"wrote: {OUT_JSON}", file=sys.stderr)

# write .ts (typed Record<string, string|null>) for clean import
ts_lines = [
    "// Auto-merged from wordEmojis-batch{1..8}.json",
    "// 1376 entries, null = no good emoji (fallback to CN text in UI)",
    f"// generated: 2026-08-03, count: {len(merged)}",
    "",
    "export const WORD_EMOJIS: Record<string, string | null> = {",
]
for k in sorted(merged.keys()):
    v = merged[k]
    if v is None:
        v_str = "null"
    else:
        # safe escape: just write the literal
        v_str = json.dumps(v, ensure_ascii=False)
    ts_lines.append(f"  {json.dumps(k, ensure_ascii=False)}: {v_str},")
ts_lines.append("};")
ts_lines.append("")

OUT_TS.write_text("\n".join(ts_lines), encoding="utf-8")
print(f"wrote: {OUT_TS}", file=sys.stderr)
