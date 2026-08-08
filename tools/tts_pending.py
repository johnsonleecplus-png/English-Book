# -*- coding: utf-8 -*-
"""列出待生成的 TTS 词, 用于批量调 MiniMax TTS"""
import json, sys
from pathlib import Path

VOCAB = Path(r"D:\10-English-Book\src\data\vocabSeed.ts")
SOURCE = Path(r"D:\10-网页集合站\tts\words")  # 中转
DEST = Path(r"D:\10-English-Book\public\audio\words")

# 解析 vocabSeed.ts 提词 (简单 regex 抓 word 字段)
import re
text = VOCAB.read_text(encoding="utf-8")
words = re.findall(r"word:\s*['\"]([a-z][a-z\-']*)['\"]", text)
print(f"VOCAB total: {len(words)}", file=sys.stderr)

# 去重保序
seen, unique = set(), []
for w in words:
    if w not in seen:
        seen.add(w); unique.append(w)

# 已生成
existing = set()
for p in DEST.glob("*.mp3"):
    if p.stem.startswith("_"):
        continue
    existing.add(p.stem)

# 待生成
pending = [w for w in unique if w not in existing]
print(f"already generated: {len(existing)}", file=sys.stderr)
print(f"pending: {len(pending)}", file=sys.stderr)

# 输出: 每行一个 word (Python 端)
out = Path(r"D:\10-网页集合站\tts\pending_words.json")
out.write_text(json.dumps(pending, ensure_ascii=False), encoding="utf-8")
print(f"wrote: {out}", file=sys.stderr)

# 输出: 10-per-batch JSON (人类读 + LLM 读)
chunks = [pending[i:i+10] for i in range(0, len(pending), 10)]
print(f"chunks: {len(chunks)}", file=sys.stderr)
