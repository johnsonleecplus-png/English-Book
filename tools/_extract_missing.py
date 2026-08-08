# -*- coding: utf-8 -*-
"""提取 271 个无 emoji 词的 word + pos + cn (从 vocabSeed.ts + mockWords.ts)"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\10-English-Book"

# 1. 词表所有词
words = []
path = ROOT + r"\src\lib\mockWords.ts"
words += re.findall(r"word:\s*'([^']+)'", open(path, encoding="utf-8").read())
path = ROOT + r"\src\data\vocabSeed.ts"
content = open(path, encoding="utf-8").read().replace("\\'", "'")
words += re.findall(r"word['\"]?\s*:\s*['\"]([^'\"]+)['\"]", content)
seen = set()
unique = []
for w in words:
    if w not in seen:
        seen.add(w)
        unique.append(w)
words = unique

# 2. 现有 emoji
emojis = json.load(open(ROOT + r"\src\data\wordEmojis.json", encoding="utf-8"))

# 3. 缺口词
missing = [w for w in words if w not in emojis]
print(f"缺口词: {len(missing)}")

# 4. 从 vocabSeed 提取 pos+cn (用更稳的逐条解析)
seed_meta = {}
for m in re.finditer(
    r"\{\s*(?:word['\"]?\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*)?pos['\"]?\s*:\s*['\"]([^'\"]*)['\"]\s*,\s*cn['\"]?\s*:\s*['\"]([^'\"]*)['\"]\s*\}",
    content,
):
    w, pos, cn = m.groups()
    if w:
        seed_meta[w] = (pos, cn)

rows = []
for w in sorted(missing):
    pos, cn = seed_meta.get(w, ("", ""))
    rows.append({"word": w, "pos": pos, "cn": cn})

out = ROOT + r"\tools\_missing_words.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print(f"写入 {out} : {len(rows)} 条")

# 打印分类统计 + 词组全表
phrases = [r for r in rows if " " in r["word"]]
proper = [r for r in rows if " " not in r["word"] and r["word"][0].isupper() and r["word"] not in ("OK", "Mr", "Mrs", "God")]
singles = [r for r in rows if r not in phrases and r not in proper]
print(f"词组: {len(phrases)}  专有: {len(proper)}  单字: {len(singles)}")
print("\n=== 词组 (word | pos | cn) ===")
for r in phrases:
    print(f"{r['word']} | {r['pos']} | {r['cn']}")
print("\n=== 单字 ===")
for r in singles:
    print(f"{r['word']} | {r['pos']} | {r['cn']}")
