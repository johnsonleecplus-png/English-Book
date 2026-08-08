"""Android UA 模拟看新 CardView 渲染"""
from playwright.sync_api import sync_playwright
import time, re
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")
OUT.mkdir(parents=True, exist_ok=True)
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
                    key: 'main', dailyNewTarget: 5, newRatio: 0.5, seededAt: now,
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

    page.goto(f'http://127.0.0.1:5173/?cb=cardfix&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    page.evaluate(SEED)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # Home → 开始 → confirm
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(800)
    page.locator('button:has-text("开始学")').last.click()
    page.wait_for_timeout(2000)

    # ===== 测试 1: en2cn 模式, 揭示前 (只显示英文) =====
    page.screenshot(path=str(OUT / "fix-01-en2cn-pre.png"), full_page=True)
    print("fix-01-en2cn-pre.png saved")

    # ===== 测试 2: en2cn 模式, 揭示后 (英文 + 中文 + 例句) =====
    page.locator('button:has-text("揭示答案")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "fix-02-en2cn-revealed.png"), full_page=True)
    print("fix-02-en2cn-revealed.png saved")

    # ===== 测试 3: cn2en 模式, 揭示后 =====
    page.locator('button[title="认识"]').first.click()
    page.wait_for_timeout(1000)
    page.locator('button:has-text("中→英")').first.click()
    page.wait_for_timeout(400)
    page.locator('button:has-text("揭示答案")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "fix-03-cn2en-revealed.png"), full_page=True)
    print("fix-03-cn2en-revealed.png saved")

    # ===== 测试 4: image 模式, 揭示后 =====
    page.locator('button[title="认识"]').first.click()
    page.wait_for_timeout(1000)
    page.locator('button:has-text("图说")').first.click()
    page.wait_for_timeout(400)
    page.locator('button:has-text("揭示答案")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "fix-04-image-revealed.png"), full_page=True)
    print("fix-04-image-revealed.png saved")

    # ===== 测试 5: listen 模式, 揭示后 =====
    page.locator('button[title="认识"]').first.click()
    page.wait_for_timeout(1000)
    page.locator('button:has-text("听说")').first.click()
    page.wait_for_timeout(400)
    page.locator('button:has-text("揭示答案")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "fix-05-listen-revealed.png"), full_page=True)
    print("fix-05-listen-revealed.png saved")

    browser.close()
print("\nAll screenshots saved.")
