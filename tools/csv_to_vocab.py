# -*- coding: utf-8 -*-
"""Build-time: 解析 CSV → src/data/vocabSeed.ts (1444 词).
- word.toLowerCase() 当 id (保证 type Card.id 兼容)
- 重复 word 跳过 (MOCK_WORDS 5 词的 cn 跟 CSV 不一致, 保留 MOCK 状态, 避免覆盖学习进度)
- 输出 ts module: const VOCAB: VocabRow[] = [...]
"""
import csv, sys, re
from pathlib import Path

CSV = Path(r"D:\10-English-Book\public\词源\上海中考英文词汇表_完整版.csv")
OUT = Path(r"D:\10-English-Book\src\data\vocabSeed.ts")

WORD_RE = re.compile(r"^[a-z][a-z\-']*$")

# 5 MOCK 词: IDB 已有, CSV 也有但 cn/pos 不一样
# 策略: 保留 MOCK 当前状态, CSV 中重复的也跳过
MOCK_WORDS = {"develop", "although", "opportunity", "kindness", "achieve"}

rows = []
seen = set()
with CSV.open("r", encoding="utf-8-sig") as f:
    # skip comments
    lines = [l for l in f if not l.lstrip().startswith("#")]

# 表头行是 "序号,单词,词性(英文),词性(中文),释义"
# 找表头
header_idx = 0
for i, line in enumerate(lines):
    if line.startswith("序号"):
        header_idx = i
        break

# 用 csv module 解析
reader = csv.reader(lines[header_idx:])
next(reader)  # skip header
for parts in reader:
    if len(parts) < 5:
        continue
    seq, word, pos_en, pos_zh, cn = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()
    if not word or word == "单词":
        continue
    if not WORD_RE.match(word):
        continue
    if word in MOCK_WORDS:
        continue  # 保留 MOCK 当前 cn/pos + 学习状态
    if word in seen:
        continue
    seen.add(word)
    rows.append({"word": word, "pos": pos_zh or pos_en, "cn": cn})

print(f"unique vocab words: {len(rows)} (MOCK 5 跳过)", file=sys.stderr)

# 生成 ts
ts_lines = [
    "// Build-time generated from CSV 上海中考英文词汇表_完整版.csv",
    f"// {len(rows)} 词 (MOCK_WORDS 5 词已排除, 保留 IDB 学习状态)",
    "// 注意: 这是源数据, IDB 是 truth; 用户在 IDB 学过的 pos/cn 以 IDB 为准",
    "",
    "export interface VocabRow {",
    "  word: string",
    "  pos: string  // 词性 (中文: 动词/名词/...)",
    "  cn: string   // 中文释义",
    "}",
    "",
    f"export const VOCAB: readonly VocabRow[] = [",
]
for r in rows:
    ts_lines.append(f"  {{ word: {r['word']!r}, pos: {r['pos']!r}, cn: {r['cn']!r} }},")
ts_lines.append("];")
ts_lines.append("")

OUT.write_text("\n".join(ts_lines), encoding="utf-8")
print(f"wrote: {OUT}", file=sys.stderr)
