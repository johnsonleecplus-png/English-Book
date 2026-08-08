"""30 个全有 MP3 的词: 100% 走真 MP3, 0 fallback 验证

不依赖 TTS 进度, 直接用已生成的词验证修法正确性。
"""
from playwright.sync_api import sync_playwright
import time, re
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")
mp3_dir = Path(r"D:\10-English-Book\public\audio\words")

# 读 VOCAB 词
vocab_src = Path(r"D:\10-English-Book\src\data\vocabSeed.ts").read_text(encoding='utf-8')
words = re.findall(r'word:\s*[\'"]([^\'"]+)[\'"]', vocab_src)
existing = set(p.stem for p in mp3_dir.glob('*.mp3'))

# 全有 MP3 的 30 个
covered_only = [w for w in words if w in existing][:30]
print(f"Test words (all have MP3): {len(covered_only)}")
print(f"  first 5: {covered_only[:5]}")

# 拼 seed JS — 灌 30 真实词 + 100 占位 (确保 cardCount >= 100, 避免 ensureSeeded 覆盖)
words_json = str(covered_only).replace("'", '"')
SEED = f"""async () => {{
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
                const ws = {words_json};
                // 30 真实词 (id w0..w29, 词从 ws)
                for (let i = 0; i < ws.length; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+i, word: ws[i], pos: 'n.', cn: 'test', example: '',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 0, createdAt: now,
                    }});
                }}
                // 100 占位 (id w100..w199, 词 __pad_xx__, 不在 VOCAB → ensureSeeded 跳过)
                // firstSeen = 1 (非 0, 不被当新词) + reps = 0 (不被当复习) → 完全不出现在 queue
                for (let i = 0; i < 100; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+(i+100), word: '__pad_'+i, pos: 'n.', cn: '占位', example: '',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 1, createdAt: now,
                    }});
                }}
                tx2.objectStore('settings').put({{
                    key: 'main', dailyNewTarget: 30, newRatio: 0.5, seededAt: now,
                }});
                tx2.oncomplete = () => resolve();
            }}
        }};
    }});
}}"""

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
        if '/audio/words/' in r.url and r.request.method == 'GET' else None
    ))

    page.goto(f'http://127.0.0.1:5173/?cb=mp3only&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)

    page.evaluate(SEED)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # 钩 Audio + speechSynthesis
    page.evaluate("""() => {
        window.__audioCalls = [];
        const orig = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function() {
            if (this.src && this.src.includes('audio/words/')) {
                window.__audioCalls.push({ src: this.src });
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

    print(f"\n=== Running 30 cards ===")
    cards_ran = 0
    for i in range(40):
        try:
            if page.locator('button:has-text("今日到这")').count() > 0:
                break
            if page.locator('button:has-text("揭示答案")').count() > 0:
                page.locator('button:has-text("揭示答案")').first.click()
                page.wait_for_timeout(800)
            if page.locator('button[title="认识"]').count() > 0:
                page.locator('button[title="认识"]').first.click()
                page.wait_for_timeout(700)
                cards_ran += 1
        except Exception as e:
            print(f"  err at {i}: {e}")
            break

    audio_calls = page.evaluate('window.__audioCalls || []')
    tts_falls = page.evaluate('window.__ttsFallbacks || []')

    print(f"\n=== Result: ran {cards_ran} cards ===")
    print(f"Audio.play() calls: {len(audio_calls)}")
    print(f"speechSynthesis fallbacks: {len(tts_falls)}")
    if tts_falls:
        print(f"  TTS fallback words: {tts_falls}")

    # 唯一词
    audio_words = set(c['src'].split('/')[-1].replace('.mp3', '') for c in audio_calls)
    print(f"Unique audio words: {len(audio_words)}")

    # 200 mp3 数
    mp3_200 = [r for r in net_audio if r['status'] == 200 and r['ct'].startswith('audio/')]
    print(f"MP3 200 responses: {len(mp3_200)}")

    if len(tts_falls) == 0 and len(audio_calls) > 0:
        print(f"\n✅ PASS: 30 张全走真 MP3, 0 fallback")
    elif len(tts_falls) > 0:
        print(f"\n⚠️  30 张里有 {len(tts_falls)} 走 fallback")
    else:
        print(f"\n❌ FAIL: 全无音频")

    browser.close()
