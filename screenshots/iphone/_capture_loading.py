"""Loading 屏截图."""
from playwright.sync_api import sync_playwright
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase-loading')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=loading'

with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    # 打开页面, 在 useEffect 跑完前截屏
    page.goto(DEV_URL, wait_until='domcontentloaded')
    # 立即截, 应该还在 loading 状态 (image 还没渲染)
    page.wait_for_timeout(100)
    page.screenshot(path=os.path.join(OUT_DIR, '01-loading-initial.png'), full_page=True)
    print('1/3 ok: 01-loading-initial.png')

    # 等图片加载完成
    page.wait_for_function("""
        () => {
            const img = document.querySelector('img');
            return img && img.complete && img.naturalWidth > 0;
        }
    """, timeout=8000)
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(OUT_DIR, '02-loading-loaded.png'), full_page=True)
    print('2/3 ok: 02-loading-loaded.png')

    # 等到 loading 状态结束 (进入 home)
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(OUT_DIR, '03-after-loading-home.png'), full_page=True)
    print('3/3 ok: 03-after-loading-home.png')

    # 验证图片可访问 + 尺寸
    info = page.evaluate("""
        () => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => ({ src: img.src, w: img.naturalWidth, h: img.naturalHeight, complete: img.complete }));
        }
    """)
    print(f'\nimg info: {info}')

    browser.close()
    print('Done')
