"""POC: 截 image 模式 5 张 (覆盖 MOCK_WORDS 全部 5 词)
用法: python -X utf8 _capture_image_poc.py
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

URL = 'http://127.0.0.1:5173/?bust=imagepoc'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image-poc')
os.makedirs(OUT, exist_ok=True)

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        ctx = browser.new_context(**iphone)
        page = ctx.new_page()

        # 清 IDB
        page.goto(URL, wait_until='domcontentloaded')
        page.wait_for_timeout(1500)
        page.evaluate("""async () => {
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
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        # 开始今日
        page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
        page.locator('button:has-text("开始今日")').first.click()
        page.wait_for_timeout(1500)

        # 切到 image 模式
        page.locator('button:has-text("图说")').first.click()
        page.wait_for_timeout(500)

        # 截图 5 张, 评分后切下一张
        for i in range(5):
            # 当前卡截图 (未揭示, 显示图标)
            # 拿当前显示的词
            try:
                big_text = page.locator('div.text-6xl, div.text-5xl').first.text_content(timeout=2000)
            except Exception:
                big_text = f'card-{i+1}'
            fname = f'0{i+1}-image-{big_text or "unknown"}.png'.replace('/', '_')
            page.screenshot(path=os.path.join(OUT, fname), full_page=True)
            print(f'{i+1}/5 ok: {fname}')

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
        print(f'\nDone: screenshots in {OUT}')
except Exception:
    traceback.print_exc()
    sys.exit(1)
