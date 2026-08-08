"""4 模式独立截图, 跑 4 次 (每个模式单独测, 不连续评)"""
from playwright.sync_api import sync_playwright
import time, re
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")
mp3_dir = Path(r"D:\10-English-Book\public\audio\words")
vocab_src = Path(r"D:\10-English-Book\src\data\vocabSeed.ts").read_text(encoding='utf-8')
words = re.findall(r'word:\s*[\'"]([^\'"]+)[\'"]', vocab_src)
existing = set(p.stem for p in mp3_dir.glob('*.mp3'))
covered = [w for w in words if w in existing][:15]
words_json = str(covered).replace("'", '"')

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
                        id: 'w'+i, word: ws[i], pos: 'n.', cn: 'cn '+ws[i], example: 'I use ' + ws[i] + ' in a sentence.',
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

def setup(ctx, idx, target=10):
    page = ctx.new_page()
    page.goto(f'http://127.0.0.1:5173/?cb=mode{idx}&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    page.evaluate(SEED)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(800)
    page.locator('button:has-text("开始学")').last.click()
    page.wait_for_timeout(2000)
    return page

ANDROID_UA = 'Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36'

with sync_playwright() as p:
    browser = p.chromium.launch()

    for idx, (mode, label) in enumerate([
        ('en2cn', '英→中'),
        ('cn2en', '中→英'),
        ('图说', '图说'),
        ('听说', '听说'),
    ]):
        ctx = browser.new_context(
            user_agent=ANDROID_UA,
            viewport={'width': 393, 'height': 851},
            device_scale_factor=2.75,
            is_mobile=True,
            has_touch=True,
        )
        page = setup(ctx, idx)

        # 切到目标模式
        page.locator(f'button:has-text("{label}")').first.click()
        page.wait_for_timeout(400)

        # 揭示前
        page.screenshot(path=str(OUT / f"mode-{idx+1}-{mode}-pre.png"), full_page=True)

        # 揭示
        page.locator('button:has-text("答案")').first.click()
        page.wait_for_timeout(800)

        # 揭示后
        page.screenshot(path=str(OUT / f"mode-{idx+1}-{mode}-revealed.png"), full_page=True)

        print(f"mode-{idx+1}-{mode}: pre + revealed saved")
        ctx.close()

    browser.close()
print("Done.")
