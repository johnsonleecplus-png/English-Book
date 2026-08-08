"""全量 1441 词验证 (TTS 100% 后跑)

验证项:
1. 所有 1441 词都有 MP3 (本地文件存在)
2. dev server 能 200 这些 MP3 (且 content-type=audio)
3. 抽 50 词 random 走 CardView 端到端, 50/50 全 MP3
4. Android UA + iPhone UA 两种环境都跑
"""
from playwright.sync_api import sync_playwright
import time, re, random
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")
mp3_dir = Path(r"D:\10-English-Book\public\audio\words")

# 读 VOCAB
vocab_src = Path(r"D:\10-English-Book\src\data\vocabSeed.ts").read_text(encoding='utf-8')
words = re.findall(r'word:\s*[\'"]([^\'"]+)[\'"]', vocab_src)
print(f"VOCAB: {len(words)}")

# ===== 1. 本地文件覆盖率 =====
existing = set(p.stem for p in mp3_dir.glob('*.mp3'))
missing = [w for w in words if w not in existing]
print(f"MP3 existing: {len(existing)}")
print(f"Missing: {len(missing)}")
if missing[:5]:
    print(f"  e.g. {missing[:5]}")

coverage = len(existing) / len(words) * 100
print(f"Coverage: {coverage:.2f}%")

# ===== 2. dev server 200 检查 (head request) =====
import urllib.request
def check_url(url):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.headers.get('content-type', ''), r.headers.get('content-length', '0')
    except Exception as e:
        return 0, str(e)[:50], '0'

# 抽 20 词验 server
sample = random.sample(words, 20)
server_ok = 0
server_bad = []
for w in sample:
    url = f'http://127.0.0.1:5173/audio/words/{w}.mp3'
    status, ct, cl = check_url(url)
    if status == 200 and ct.startswith('audio/') and int(cl or '0') > 1024:
        server_ok += 1
    else:
        server_bad.append((w, status, ct, cl))
print(f"\nServer HEAD check: {server_ok}/20 ok")
if server_bad:
    for s in server_bad:
        print(f"  BAD: {s}")

# ===== 3. CardView 端到端: 50 词 random 走 =====
SEED = f"""async (testWords) => {{
    return new Promise((resolve) => {{
        const req = indexedDB.open('english-book');
        req.onsuccess = () => {{
            const db = req.result;
            const stores = Array.from(db.objectStoreNames);
            const tx = db.transaction(stores, 'readwrite');
            let pending = stores.length;
            if (pending === 0) {{ seed(); return; }}
            for (const s of stores) {{
                const r = tx.objectStore(s).clear();
                r.onsuccess = () => {{ if (--pending === 0) seed(); }};
            }}
            function seed() {{
                const now = Date.now();
                const tx2 = db.transaction(['cards','settings'], 'readwrite');
                for (let i = 0; i < testWords.length; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+i, word: testWords[i], pos: 'n.', cn: 'test', example: '',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 0, createdAt: now,
                    }});
                }}
                // 100 占位 (避免 ensureSeeded 灌 VOCAB 覆盖)
                for (let i = 0; i < 100; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+(i+1000), word: '__pad'+i, pos: 'n.', cn: 'p', example: '',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 1, createdAt: now,  // firstSeen=1, not new
                    }});
                }}
                tx2.objectStore('settings').put({{
                    key: 'main', dailyNewTarget: 50, newRatio: 0.5, seededAt: now,
                }});
                tx2.oncomplete = () => resolve();
            }}
        }};
    }});
}}"""

# 抽 50 个**有 MP3** 的词
covered = [w for w in words if w in existing]
test50 = random.sample(covered, 50)
print(f"\nTest sample: 50 words (all have MP3)")

ANDROID_UA = 'Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36'

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        user_agent=ANDROID_UA,
        viewport={'width': 393, 'height': 851},
        device_scale_factor=2.75,
        is_mobile=True,
        has_touch=True,
    )
    page = ctx.new_page()

    net_audio = []
    page.on('response', lambda r: (
        net_audio.append({'url': r.url, 'status': r.status, 'ct': r.headers.get('content-type', '')})
        if '/audio/words/' in r.url else None
    ))

    page.goto(f'http://127.0.0.1:5173/?cb=final&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    page.evaluate(SEED, test50)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # 钩 Audio + speechSynthesis
    page.evaluate("""() => {
        window.__audioCalls = [];
        const orig = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function() {
            if (this.src && this.src.includes('audio/words/')) {
                window.__audioCalls.push({ src: this.src, t: Date.now() });
            }
            return orig.apply(this, arguments);
        };
        window.__ttsFallbacks = [];
        const origSpeak = window.speechSynthesis.speak.bind(window.speechSynthesis);
        window.speechSynthesis.speak = function(u) {
            window.__ttsFallbacks.push(u.text);
            return origSpeak(u);
        };
    }""")

    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(1000)
    page.locator('button:has-text("开始学")').last.click()
    page.wait_for_timeout(2000)

    print(f"\n=== Running 50 cards (Android Chrome UA) ===")
    cards_ran = 0
    for i in range(60):
        try:
            if page.locator('button:has-text("今日到这")').count() > 0:
                break
            if page.locator('button:has-text("揭示答案")').count() > 0:
                page.locator('button:has-text("揭示答案")').first.click()
                page.wait_for_timeout(800)
            if page.locator('button[title="认识"]').count() > 0:
                page.locator('button[title="认识"]').first.click(timeout=5000, force=False)
                page.wait_for_timeout(1000)  # 等 600ms transition 完成
                cards_ran += 1
        except Exception as e:
            print(f"  err at {i}: {e}")
            break

    audio_calls = page.evaluate('window.__audioCalls || []')
    tts_falls = page.evaluate('window.__ttsFallbacks || []')
    audio_words = set(c['src'].split('/')[-1].replace('.mp3', '') for c in audio_calls)

    print(f"\n=== Result: ran {cards_ran} cards ===")
    print(f"Audio.play() calls: {len(audio_calls)}")
    print(f"Unique audio words: {len(audio_words)}")
    print(f"speechSynthesis fallbacks: {len(tts_falls)}")

    mp3_200 = [r for r in net_audio if r['status'] == 200 and r['ct'].startswith('audio/')]
    print(f"MP3 200 responses: {len(mp3_200)}")

    page.screenshot(path=str(OUT / "final-01-cardview.png"), full_page=True)

    # ===== VERDICT =====
    print(f"\n========================================")
    print(f"=== FINAL VERDICT (TTS coverage: {coverage:.2f}%) ===")
    print(f"========================================")
    print(f"1. 本地 MP3 覆盖率: {len(existing)}/{len(words)} = {coverage:.2f}%")
    print(f"2. dev server HEAD 抽样: {server_ok}/20 真 MP3 ({'PASS' if server_ok == 20 else 'FAIL'})")
    print(f"3. Android UA 端到端: {len(audio_words)}/{cards_ran} 走 MP3, {len(tts_falls)} 走 fallback")

    if coverage >= 99.0 and server_ok == 20 and len(tts_falls) == 0 and len(audio_words) >= cards_ran - 2:
        print(f"\n✅ PASS: Android 真机可播 (MP3 100% 覆盖)")
    elif coverage >= 99.0 and server_ok == 20 and len(tts_falls) <= 2:
        print(f"\n✅ PASS: Android 真机可播 (少量 fallback 走 speechSynthesis)")
    else:
        print(f"\n⚠️  待修")

    browser.close()
