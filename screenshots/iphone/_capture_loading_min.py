"""验证 loading 屏至少显示 1s."""
from playwright.sync_api import sync_playwright
import os, time

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase-loading')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=loadingmin'

with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    t0 = time.time()
    page.goto(DEV_URL, wait_until='domcontentloaded')

    # 等待 200ms: 应还在 loading
    page.wait_for_timeout(200)
    on_loading_200 = page.locator('img[src$="loading.png"]').count() > 0
    print(f't=0.2s  在 loading: {on_loading_200}')

    # 等待 600ms: 应还在 loading (因为保证 1s)
    page.wait_for_timeout(400)  # 累计 600ms
    on_loading_600 = page.locator('img[src$="loading.png"]').count() > 0
    print(f't=0.6s  在 loading: {on_loading_600}')
    assert on_loading_600, '0.6s 时 loading 屏应该还在 (保证 1s)'

    # 等待到 1.4s: 应已切到 home
    page.wait_for_timeout(800)  # 累计 1.4s
    on_loading_1400 = page.locator('img[src$="loading.png"]').count() > 0
    on_home = '开始今日' in (page.locator('body').text_content() or '')
    print(f't=1.4s  在 loading: {on_loading_1400}  已进 home: {on_home}')
    assert not on_loading_1400, '1.4s 时应已退出 loading'
    assert on_home, '应已到 home tab'

    page.screenshot(path=os.path.join(OUT_DIR, '04-loading-min-1s.png'), full_page=True)

    total = time.time() - t0
    print(f'\n总耗时: {total:.2f}s (loading 屏显示 ≥1s)')

    browser.close()
    print('✅ 验证通过')
