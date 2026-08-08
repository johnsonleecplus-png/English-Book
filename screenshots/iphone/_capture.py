"""iPhone 14 Pro 视口截图脚本 (Phase 1 适配)

适配项:
- 路径改用项目根 (不再硬编码 F:\\22-...)
- 新增 Home 屏截图 (01-home)
- 起点改成 Home → 点 [开始今日] → 进入 CardView
- 后续截图保持原顺序: en2cn-before / en2cn-after / cn2en / listen

用法:
  cd screenshots/iphone
  python _capture.py
  (需要先在另一个 shell 跑 npm run dev)
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

# 项目根 = _capture.py 的上两级 (screenshots/iphone -> screenshots -> project)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone')
os.makedirs(OUT_DIR, exist_ok=True)

DEV_URL = 'http://localhost:5173/?bust=phase1'

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone)
        page = context.new_page()

        # 0) Home 屏 (新)
        page.goto(DEV_URL, wait_until='networkidle')
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUT_DIR, '00-home.png'), full_page=True)
        print('0/5 ok: 00-home.png')

        # 点 [开始今日] → 跳 confirm 屏 (P3.1+)
        page.locator('button:has-text("开始今日")').first.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUT_DIR, '00b-confirm.png'), full_page=True)
        print('0b/5 ok: 00b-confirm.png (P3.1 confirm 目标屏)')

        # 点 [开始学 N 个新词] 确认 → 进入 CardView
        page.locator('button:has-text("开始学")').first.click()
        page.wait_for_timeout(800)

        # 1) Card 1 英→中 揭示前
        page.screenshot(path=os.path.join(OUT_DIR, '01-en2cn-before.png'), full_page=True)
        print('1/5 ok: 01-en2cn-before.png')

        # 2) 英→中 揭示后
        page.locator('button:has-text("揭示答案")').first.click()
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(OUT_DIR, '02-en2cn-after.png'), full_page=True)
        print('2/5 ok: 02-en2cn-after.png')

        # 3) 中→英 (保留 revealed 状态)
        page.locator('button:has-text("中→英")').first.click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(OUT_DIR, '03-cn2en-after.png'), full_page=True)
        print('3/5 ok: 03-cn2en-after.png')

        # 4) 听说模式 (评分前进后切到 listen, 看未揭示的大喇叭)
        page.locator('button[title="认识"]').first.click()
        page.wait_for_timeout(700)
        page.locator('button:has-text("听说")').first.click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(OUT_DIR, '04-listen.png'), full_page=True)
        print('4/5 ok: 04-listen.png')

        # 5) 主动结束 → 回 Home (验证 P1.5 状态机)
        # 直接关 tab (无显式退出) — 模拟用户离开
        # 用 evaluate 清掉 active session 然后刷新, 模拟"明天开始"
        # 实际上更准确: 评分完成所有 5 张 → 触发 onFinish → 回 Home
        # 这里简化: 把所有卡点一次, 然后看是否回 Home
        for _ in range(6):
            # 揭示 + 评分, 循环直到 queue 完成
            try:
                reveal_btn = page.locator('button:has-text("揭示答案")')
                if reveal_btn.count() == 0:
                    break
                reveal_btn.first.click()
                page.wait_for_timeout(400)
                page.locator('button[title="认识"]').first.click()
                page.wait_for_timeout(700)
            except Exception:
                break

        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUT_DIR, '05-home-after.png'), full_page=True)
        print('5/5 ok: 05-home-after.png (queue 完成回 Home)')

        browser.close()
        print('Done: 6 screenshots saved to', OUT_DIR)
except Exception:
    traceback.print_exc()
    sys.exit(1)
