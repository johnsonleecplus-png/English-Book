"""验证 v3 UX: TabBar 永远在 + 删 Confirm 返回按钮 + 保留 tip.

截图用 viewport (不是 full_page), 真实呈现 TabBar 在屏底 fixed 位置.
"""
from playwright.sync_api import sync_playwright
import os, sys

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase-ux-v3')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=ux3'


def shoot(page, name):
    """viewport 截图: 真实 iPhone 视口, TabBar 永远在屏底"""
    page.screenshot(path=os.path.join(OUT_DIR, name), full_page=False)
    print(f'  -> {name}')


with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    # 1) clear + reload
    page.goto(DEV_URL, wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    page.evaluate("""
        () => new Promise((r) => {
            const req = indexedDB.deleteDatabase('english-book');
            req.onsuccess = () => r();
            req.onerror = () => r();
            req.onblocked = () => r();
        })
    """)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(3000)

    # 2) Home 应有 TabBar + 切到确认屏
    home_text = page.locator('body').text_content() or ''
    assert page.locator('nav').count() == 1, 'Home 应有 TabBar'
    print('1/5 ok: Home 有 TabBar')
    shoot(page, '01-home.png')

    # 3) 点 [开始今日] → Confirm 屏
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(800)

    confirm_text = page.locator('body').text_content() or ''
    has_tab = page.locator('nav').count() == 1
    no_tip = '复习卡' not in confirm_text
    no_back = page.locator('button:has-text("返回")').count() == 0
    print(f'2/5 confirm 屏: tab={has_tab} no_tip={no_tip} no_back={no_back}')
    assert has_tab, 'Confirm 屏应显示 TabBar'
    assert no_tip, 'Confirm 屏不应有 tip (2026-08-04 用户拍板删除)'
    assert no_back, 'Confirm 屏不应有返回按钮'
    shoot(page, '02-confirm.png')

    # 4) 选 5 → 开始
    page.locator('button:has-text("5")').first.click()
    page.wait_for_timeout(300)
    page.locator('button:has-text("开始学")').first.click()
    page.wait_for_timeout(1500)

    # 5) CardView 应有 TabBar
    has_tab_active = page.locator('nav').count() == 1
    nav_box = page.locator('nav').first.bounding_box()
    print(f'3/5 CardView: tab_bar={has_tab_active}, nav_y={nav_box}')
    assert has_tab_active, 'CardView 应显示 TabBar'
    shoot(page, '03-cardview.png')

    # 6) 切到历史 tab
    page.locator('nav button:has-text("历史")').first.click()
    page.wait_for_timeout(800)
    hist_text = page.locator('body').text_content() or ''
    on_history = '7 周打卡' in hist_text
    print(f'4/5 切到历史: on_history={on_history}')
    assert on_history, '应能切到历史 tab'
    shoot(page, '04-history-from-active.png')

    # 7) 切回今日 → CardView 应恢复 (3 个评分按钮 + 词卡片)
    page.locator('nav button:has-text("今日")').first.click()
    page.wait_for_timeout(1000)
    # 评分按钮快捷键 kbd 1/2/3 + 评分按钮 aria 提示
    has_rate_btns = page.locator('kbd:text-is("1")').count() == 1 and page.locator('kbd:text-is("2")').count() == 1 and page.locator('kbd:text-is("3")').count() == 1
    print(f'5/5 切回今日 CardView: {has_rate_btns}')
    assert has_rate_btns, '切回今日应显示 CardView 评分按钮 (1/2/3 kbd)'
    shoot(page, '05-back-to-cardview.png')

    browser.close()
    print(f'\n✅ v3 UX 验证全过, 截图: {OUT_DIR}')
