"""
UI 修复验证:
1. CardView 评分按钮 - 确认没有 1/2/3 数字提示
2. History 7 周热力图 - 100+ 才是深绿色
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

OUT_DIR = r"D:\10-English-Book\screenshots\ui-fix"
PREVIEW_URL = "http://localhost:4173"

os.makedirs(OUT_DIR, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
        )
        page = await context.new_page()

        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

        # 1. 打开
        print("→ 打开 preview")
        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        # 2. 清 IDB + reload
        await page.evaluate("""async () => {
            const dbs = await indexedDB.databases()
            for (const d of dbs) {
              if (d.name) await new Promise((res) => {
                const r = indexedDB.deleteDatabase(d.name)
                r.onsuccess = r.onerror = r.onblocked = () => res()
              })
            }
        }""")
        await page.reload()
        await page.wait_for_timeout(2000)

        # 3. 直接跳 History (点 TabBar 的"历史")
        # 不需要先开 session
        print("→ 直接进 History 屏")
        await page.wait_for_selector("text=开始今日", timeout=10000)
        # 点 "历史" tab
        history_btn = page.locator("button").filter(has_text="历史").first
        await history_btn.click(timeout=5000)
        await page.wait_for_timeout(1000)

        # 等热力图渲染
        await page.wait_for_selector("text=7 周打卡", timeout=5000)
        await page.screenshot(path=f"{OUT_DIR}/01-history-heatmap.png", full_page=False)
        print("  History 截图: 01-history-heatmap.png")

        # 验证: 热力图图例显示 "100+"
        legend = await page.locator("text=100+").count()
        print(f"  图例 100+: {legend} 处")

        # 4. 验证 CardView: 进 session 看评分按钮
        print("→ 进 session 看 CardView 评分按钮")
        # 回 home
        home_btn = page.locator("button").filter(has_text="今日").first
        await home_btn.click(timeout=5000)
        await page.wait_for_timeout(500)

        # 点 开始今日 → confirm → 选 15 → 开始
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_timeout(1000)

        # 等 CardView
        await page.wait_for_selector("button:has-text('答案')", timeout=10000)

        # 揭示
        await page.click("button:has-text('答案')")
        await page.wait_for_timeout(200)

        # 评分按钮应该出现, 不应该有 kbd 1/2/3
        await page.screenshot(path=f"{OUT_DIR}/02-cardview-no-kbd.png", full_page=False)
        print("  CardView 截图: 02-cardview-no-kbd.png")

        # 检查 kbd 元素数量 (应该 0)
        kbd_count = await page.locator("kbd").count()
        print(f"  kbd 元素数: {kbd_count} (期望 0)")

        # 检查 title 是否还含 "快捷键"
        titles = await page.locator("button[title]").all()
        has_kbd_hint = False
        for t in titles:
            title = await t.get_attribute("title") or ""
            if "快捷键" in title:
                has_kbd_hint = True
                print(f"  ❌ 残留快捷键提示: {title!r}")
        if not has_kbd_hint:
            print(f"  ✓ 评分按钮无 '快捷键' 提示")

        await browser.close()
        print(f"\n完成。截图在 {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
