"""Rename phrase audio files: phr_NNNN_xxx_xxx.mp3 -> xxx_xxx.mp3 (no prefix)."""
from pathlib import Path
import csv

DST = Path(r"F:\26-English Book\public\audio\words")
MANIFEST = Path(r"F:\27-上海中考英文词汇表\tts_manifest.csv")

# Build mapping: phr_NNNN_name.mp3 -> new_name.mp3
phr_map = {}  # old_filename -> new_filename
with MANIFEST.open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["kind"] != "phrase":
            continue
        old_mp3 = r["mp3"]   # e.g. phr_0001_a_couple_of.mp3
        # new: strip "phr_NNNN_" prefix; text-with-spaces already replaced by underscores in old name
        new_stem = "_".join(old_mp3.split("_")[2:])  # skip "phr" and "0001"
        new_mp3 = f"{new_stem}.mp3"
        phr_map[old_mp3] = new_mp3

print(f"待重命名: {len(phr_map)}")

renamed = 0
skipped = 0
for old, new in phr_map.items():
    old_path = DST / old
    new_path = DST / new
    if not old_path.exists():
        print(f"  源不存在: {old}")
        skipped += 1
        continue
    if new_path.exists() and new_path != old_path:
        # 如果新名字已存在(冲突), 跳过避免覆盖
        print(f"  冲突跳过: {old} -> {new} (新文件已存在)")
        skipped += 1
        continue
    old_path.rename(new_path)
    renamed += 1

print(f"\n重命名: {renamed} / 跳过: {skipped}")
print(f"\n剩余 phr_ 前缀文件: {sum(1 for f in DST.iterdir() if f.name.startswith('phr_'))}")
print(f"目录总文件: {sum(1 for _ in DST.iterdir())}")
