"""额外: 点卡片揭示答案, 验证评分按钮 (1/2/3) 也被 TabBar 正确避让."""
from playwright.sync_api import sync_playwright
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase-ux-v3')
DEV_URL = 'http://localhost:5173/?bust=reveal'

with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    # 不清 IDB, 直接续用
    page.goto(DEV_URL, wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # 在 active session 状态下, 直接点卡片揭示
    # 找 [开始今日] (如有) 或直接点卡片
    start_btn = page.locator('button:has-text("开始今日")')
    if start_btn.count() > 0:
        start_btn.first.click()
        page.wait_for_timeout(500)
        page.locator('button:has-text("15")').first.click()
        page.wait_for_timeout(200)
        page.locator('button:has-text("开始学")').first.click()
        page.wait_for_timeout(1500)

    # 点卡片
    page.locator('[class*="rounded-3xl"][class*="border-2"]').first.click()
    page.wait_for_timeout(500)

    # 截图
    page.screenshot(path=os.path.join(OUT_DIR, '06-cardview-revealed.png'), full_page=False)
    print('截图完成: 06-cardview-revealed.png')

    browser.close()
