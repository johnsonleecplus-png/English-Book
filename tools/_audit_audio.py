"""Audit TTS audio vs card words."""
import os
import re
from pathlib import Path

REPO = Path(r"F:\26-English Book")
SRC = Path(r"F:\27-上海中考英文词汇表\tts_mp3")
DST = REPO / "public" / "audio" / "words"

# 1) 源 1714 文件去前缀后唯一性
src_files = list(SRC.glob("*.mp3"))
src_words = [re.sub(r'^\d+_', '', f.stem) for f in src_files]
src_unique = set(src_words)
print(f"[源]  tts_mp3 文件数: {len(src_files)}")
print(f"[源]  去重后唯一词: {len(src_unique)}")
print(f"[源]  重名 word 数: {len(src_words) - len(src_unique)}")

# 2) 提取 VOCAB (从 vocabSeed.ts 解析所有 word: 'xxx')
vocab_re = re.compile(r"word:\s*'([^']+)'")
vocab_words = []
with open(REPO / "src" / "data" / "vocabSeed.ts", encoding="utf-8") as f:
    for line in f:
        m = vocab_re.search(line)
        if m:
            vocab_words.append(m.group(1).lower())
vocab_set = set(vocab_words)
print(f"[VOCAB] 单词数: {len(vocab_words)} / 唯一: {len(vocab_set)}")

# 3) MOCK 5 词
mock_words = {"develop", "although", "opportunity", "kindness", "achieve"}
print(f"[MOCK] 词数: {len(mock_words)}")

all_cards = vocab_set | mock_words
print(f"[总卡] 唯一词数: {len(all_cards)}")

# 4) 目标目录音频
dst_files = list(DST.glob("*.mp3"))
dst_words = [f.stem for f in dst_files]
dst_set = set(dst_words)
print(f"[目标] public/audio/words 文件数: {len(dst_files)} / 唯一: {len(dst_set)}")

# 5) 卡片无音频
cards_no_audio = sorted(all_cards - dst_set)
print(f"\n[差集] 卡片在 VOCAB 但 目标目录没音频: {len(cards_no_audio)}")
if cards_no_audio:
    print("  前 20:", cards_no_audio[:20])

# 6) 音频无对应卡片
audio_no_card = sorted(dst_set - all_cards)
print(f"\n[差集] 目标目录有音频 但 没对应卡片: {len(audio_no_card)}")
if audio_no_card:
    print("  前 30:", audio_no_card[:30])
    print("  ...总 271 个，看看分类...")
    months = [w for w in audio_no_card if w in {'january','february','march','april','may','june','july','august','september','october','november','december'}]
    countries = [w for w in audio_no_card if w in {'africa','america','asia','australia','brazil','canada','china','egypt','england','europe','france','germany','india','japan','russia','spain'}]
    adj_country = [w for w in audio_no_card if w in {'american','australian','british','canadian','chinese','english','french','german','japanese','russian'}]
    print(f"    月份: {months}")
    print(f"    国家(部分): {countries}")
    print(f"    形容词(部分): {adj_country}")

# 7) 关键验证: 源中是否所有 audio 都在目标里
src_in_dst = src_unique & dst_set
src_miss = src_unique - dst_set
print(f"\n[源->目标] 源里目标有的: {len(src_in_dst)} / 源 1714 - 目标有 = 源丢失: {len(src_miss)}")
if src_miss:
    print(f"  源丢失前 10: {sorted(src_miss)[:10]}")
