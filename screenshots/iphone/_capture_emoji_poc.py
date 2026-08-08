"""POC: emoji 模式截 2 套 (彩色 + 灰阶), 覆盖 MOCK_WORDS 5 词
用法: python -X utf8 _capture_emoji_poc.py
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emoji-poc')
os.makedirs(OUT, exist_ok=True)

def clear_idb(page):
    return page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open('english-book');
            req.onsuccess = () => {
                const db = req.result;
                const stores = Array.from(db.objectStoreNames);
                const tx = db.transaction(stores, 'readwrite');
                let pending = stores.length;
                if (pending === 0) resolve();
                for (const s of stores) {
                    const r = tx.objectStore(s).clear();
                    r.onsuccess = () => { if (--pending === 0) resolve(); };
                }
            };
            req.onerror = () => reject(req.error);
        });
    }""")


def run_one(p, iphone, label, url_suffix):
    """跑一轮 (彩色或灰阶), 截 5 张"""
    browser = p.chromium.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()

    page.goto(f'http://127.0.0.1:5173/?{url_suffix}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    clear_idb(page)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(1500)

    page.locator('button:has-text("图说")').first.click()
    page.wait_for_timeout(500)

    for i in range(5):
        # 取当前显示词 (但 emoji 占主导, 用 progress bar 上的 数字 反推)
        n = i + 1
        fname = f'{label}-{n:02d}.png'
        page.screenshot(path=os.path.join(OUT, fname), full_page=True)
        print(f'  [{label} {n}/5] {fname}')

        # 揭示 + 评分
        try:
            page.locator('button:has-text("揭示答案")').first.click(timeout=2000)
            page.wait_for_timeout(400)
            page.locator('button[title="认识"]').first.click()
            page.wait_for_timeout(800)
        except Exception as e:
            print(f'  rate fail (queue done?): {e}')
            break

    browser.close()


try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        # 1) 彩色版 (默认, 不带 grayscale 参数)
        print('=== 彩色版 ===')
        run_one(p, iphone, 'color', 'bust=emojicolor')
        # 2) 灰阶版 (?grayscale=1)
        print('\n=== 灰阶版 ===')
        run_one(p, iphone, 'gray', 'bust=emojigray&grayscale=1')

    print(f'\nDone: 10 screenshots in {OUT}')
except Exception:
    traceback.print_exc()
    sys.exit(1)
