"""
Sync new TTS mp3 from GitHub (Johnson 新 commit 8bd0ac92 dot 化版本)
- 拉新 mp3 覆盖 public/audio/words/
- 删旧 _test_*.mp3 (我之前的 debug 残留)
- 保留 _v2_*.mp3 (验证文件, 不覆盖)
"""
import json
import os
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

COMMIT_SHA = '8bd0ac92f5c0297245d209e6662427636dd20755'
WORDS_DIR = r'D:\10-English-Book\public\audio\words'

# 1. 拿 tree (解析所有 mp3 路径 + size)
print(f"→ 拿 commit {COMMIT_SHA[:8]} tree")
url = f'https://api.github.com/repos/johnsonleecplus-png/English-Book/git/trees/{COMMIT_SHA}?recursive=1'
req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json'})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read().decode('utf-8-sig'))
assert not data.get('truncated'), 'tree truncated (too many files)'

mp3s = [e for e in data['tree'] if e['path'].startswith('public/audio/words/') and e['path'].endswith('.mp3')]
print(f"  mp3 总数: {len(mp3s)}")

# 2. 删旧 _test_*.mp3 (我的 debug 残留, Johnson 没有)
deleted = 0
for f in os.listdir(WORDS_DIR):
    if f.startswith('_test_') and f.endswith('.mp3'):
        os.remove(os.path.join(WORDS_DIR, f))
        deleted += 1
print(f"  删 debug 残留: {deleted}")

# 3. 拉每个新 mp3 (覆盖)
print(f"→ 拉 {len(mp3s)} 个 mp3 覆盖 (并行 16)")
import concurrent.futures as cf

raw_base = f'https://raw.githubusercontent.com/johnsonleecplus-png/English-Book/{COMMIT_SHA}'

def fetch(mp3):
    name = mp3['path'].split('/')[-1]
    url = f"{raw_base}/{mp3['path']}"
    out = os.path.join(WORDS_DIR, name)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(out, 'wb') as f:
            f.write(data)
        return (name, len(data), mp3['size'])
    except Exception as e:
        return (name, None, str(e))

ok = 0
fail = 0
size_diff = []
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for name, got, expected in ex.map(fetch, mp3s):
        if got is None:
            print(f"  FAIL {name}: {expected}")
            fail += 1
        else:
            if isinstance(expected, int) and got != expected:
                size_diff.append((name, got, expected))
            ok += 1

print(f"\n  OK: {ok} / FAIL: {fail}")
if size_diff:
    print(f"  大小不一致: {len(size_diff)}")
    for n, g, e in size_diff[:5]:
        print(f"    {n}: got {g} != expected {e}")

# 4. 验证 abandon / 1st 不在 (Johnson commit 一致)
test_words = ['abandon', '1st', '2nd', '21st', 'a_bit', 'lose_one_s_life', 'a_couple_of']
print(f"\n→ 关键词验证:")
for w in test_words:
    p = os.path.join(WORDS_DIR, f'{w}.mp3')
    if os.path.exists(p):
        size = os.path.getsize(p)
        print(f"  ✓ {w}.mp3: {size} bytes")
    else:
        print(f"  ✗ {w}.mp3: 不存在 (vocab 里没 / Johnson 没生成)")
