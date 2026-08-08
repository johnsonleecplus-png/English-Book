# -*- coding: utf-8 -*-
"""Regenerate wordEmojis.ts from wordEmojis.json (the canonical source)."""
import json, sys
from pathlib import Path
from collections import Counter

DATA = Path(r"D:\10-English-Book\src\data")
JSON = DATA / "wordEmojis.json"
TS = DATA / "wordEmojis.ts"

obj = json.loads(JSON.read_text(encoding="utf-8"))
print(f"entries: {len(obj)}", file=sys.stderr)

usage = Counter()
null_count = 0
for v in obj.values():
    if v is None:
        null_count += 1
    else:
        usage[v] += 1

print(f"unique emojis: {len(usage)}", file=sys.stderr)
print(f"null entries: {null_count}", file=sys.stderr)

hot = ["❤️", "⭐", "🎉", "🏆", "💖", "✨", "💗", "🥇"]
for h in hot:
    c = usage.get(h, 0)
    flag = "⚠️ OVER" if c > 3 else "ok"
    print(f"  hot '{h}': {c} [{flag}]", file=sys.stderr)

ts_lines = [
    "// Auto-generated from wordEmojis.json",
    f"// {len(obj)} entries, {len(usage)} unique emojis, {null_count} null",
    "// null = no good emoji (UI fallback to CN text)",
    "// hot emoji budget: ❤️⭐🎉🏆 ≤ 3 uses each",
    "",
    "export const WORD_EMOJIS: Record<string, string | null> = {",
]
for k in sorted(obj.keys()):
    v = obj[k]
    if v is None:
        v_str = "null"
    else:
        v_str = json.dumps(v, ensure_ascii=False)
    ts_lines.append(f"  {json.dumps(k, ensure_ascii=False)}: {v_str},")
ts_lines.append("};")
ts_lines.append("")

TS.write_text("\n".join(ts_lines), encoding="utf-8")
print(f"wrote: {TS}", file=sys.stderr)
