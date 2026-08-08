"""验证 bug: 用户在 Settings 改 dailyNewTarget 后, 切回 Home 应看到新值."""
from playwright.sync_api import sync_playwright
import os, re

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase-ux-v3')
DEV_URL = 'http://localhost:5173/?bust=settings-bug'


def shoot(page, name):
    page.screenshot(path=os.path.join(OUT_DIR, name), full_page=False)
    print(f'  -> {name}')


with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    # 清 IDB, 干净启动
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

    # 1) Home 应显示 15 (默认)
    home_text = page.locator('body').text_content() or ''
    m = re.search(r'(\d+)\s*/\s*(\d+)', home_text)
    assert m, f'找不到数字 进度格式, body={home_text[:200]}'
    init_done, init_target = m.group(1), m.group(2)
    print(f'1/4 初始 Home: {init_done}/{init_target}')
    assert init_target == '15', f'初始 dailyNewTarget 应是 15, 实际 {init_target}'

    # 2) 切到设置 tab
    page.locator('nav button:has-text("设置")').first.click()
    page.wait_for_timeout(800)
    shoot(page, '07-settings-before.png')

    # 3) 点 50 芯片
    page.locator('button:has-text("50")').first.click()
    page.wait_for_timeout(800)
    # 验证 Settings 内显示"已保存: 每天 50"
    body = page.locator('body').text_content() or ''
    saved_text = '已保存: 每天 50' in body
    print(f'2/4 Settings 改 50: 已保存提示={saved_text}')
    assert saved_text, 'Settings 应显示"已保存: 每天 50"'
    shoot(page, '08-settings-after-50.png')

    # 4) 切回 Home (今日 tab)
    page.locator('nav button:has-text("今日")').first.click()
    page.wait_for_timeout(1500)  # 留时间给 useEffect + refreshHome
    shoot(page, '09-home-after-50.png')

    # 5) Home 应显示 / 50 (不是 / 15)
    home_text = page.locator('body').text_content() or ''
    m = re.search(r'(\d+)\s*/\s*(\d+)', home_text)
    assert m, 'Home 找不到数字'
    new_done, new_target = m.group(1), m.group(2)
    print(f'3/4 Home 切回后: {new_done}/{new_target}')
    assert new_target == '50', f'BUG: Home dailyNewTarget 应是 50, 实际 {new_target}'

    # 6) 改 100 再验证
    page.locator('nav button:has-text("设置")').first.click()
    page.wait_for_timeout(600)
    page.locator('button:has-text("100")').first.click()
    page.wait_for_timeout(500)
    page.locator('nav button:has-text("今日")').first.click()
    page.wait_for_timeout(1200)
    home_text = page.locator('body').text_content() or ''
    m = re.search(r'(\d+)\s*/\s*(\d+)', home_text)
    new_done, new_target = m.group(1), m.group(2)
    print(f'4/4 Home 改 100 后: {new_done}/{new_target}')
    assert new_target == '100', f'BUG: 100 应生效, 实际 {new_target}'

    browser.close()
    print(f'\n✅ Settings→Home dailyNewTarget 联动正常, 截图: {OUT_DIR}')
