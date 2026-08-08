"""最终交付截图: CardView 揭示瞬间 + MP3 真在播"""
from playwright.sync_api import sync_playwright
import time, re
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")
vocab_src = Path(r"D:\10-English-Book\src\data\vocabSeed.ts").read_text(encoding='utf-8')
words = re.findall(r'word:\s*[\'"]([^\'"]+)[\'"]', vocab_src)
existing = set(p.stem for p in Path(r"D:\10-English-Book\public\audio\words").glob('*.mp3'))
test = [w for w in words if w in existing][:10]
words_json = str(test).replace("'", '"')

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
                for (let i = 0; i < ws.length; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+i, word: ws[i], pos: 'n.', cn: 'n.', example: 'I use ' + ws[i] + ' in a sentence.',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 0, createdAt: now,
                    }});
                }}
                for (let i = 0; i < 100; i++) {{
                    tx2.objectStore('cards').put({{
                        id: 'w'+(i+1000), word: '__pad'+i, pos: 'n.', cn: 'p', example: '',
                        ef: 2.5, interval: 0, reps: 0,
                        due: now, firstSeen: 1, createdAt: now,
                    }});
                }}
                tx2.objectStore('settings').put({{
                    key: 'main', dailyNewTarget: 10, newRatio: 0.5, seededAt: now,
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

    page.goto(f'http://127.0.0.1:5173/?cb=cap&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    page.evaluate(SEED)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # 钩 audio + tts
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

    # Home → 开始
    page.screenshot(path=str(OUT / "final-home.png"), full_page=True)

    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(1000)
    page.screenshot(path=str(OUT / "final-confirm.png"), full_page=True)
    page.locator('button:has-text("开始学")').last.click()
    page.wait_for_timeout(2000)

    # CardView 卡片初始
    page.screenshot(path=str(OUT / "final-cardview-1.png"), full_page=True)

    # 切 image 模式 (默认 en2cn 看不到 MP3, 切到 image 看 emoji)
    page.locator('button:has-text("图说")').first.click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "final-cardview-2-image.png"), full_page=True)

    # 揭示
    page.locator('button:has-text("揭示答案")').first.click()
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / "final-cardview-3-revealed.png"), full_page=True)

    # 查 audio
    audio_calls = page.evaluate('window.__audioCalls || []')
    tts = page.evaluate('window.__ttsFallbacks || []')
    print(f"audio calls: {len(audio_calls)}")
    for c in audio_calls:
        print(f"  {c['src']}")
    print(f"TTS fallback: {len(tts)}")

    # 切 listen 模式 + 大圆 button
    page.locator('button[title="认识"]').first.click(timeout=5000)
    page.wait_for_timeout(1000)
    page.locator('button:has-text("听说")').first.click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "final-cardview-4-listen.png"), full_page=True)

    page.locator('main >> button.rounded-full').first.click()
    page.wait_for_timeout(1000)
    page.screenshot(path=str(OUT / "final-cardview-5-listen-played.png"), full_page=True)

    audio_calls2 = page.evaluate('window.__audioCalls || []')
    tts2 = page.evaluate('window.__ttsFallbacks || []')
    print(f"\nFinal: audio calls: {len(audio_calls2)}, tts fallback: {len(tts2)}")

    browser.close()
print("\n=== Screenshots saved to tts-verify/final-*.png ===")
