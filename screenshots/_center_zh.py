"""
截图 CardView 各种 mode, 验证中文/pos/example 居中
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

OUT_DIR = r"D:\10-English-Book\screenshots\center-zh"
PREVIEW_URL = "http://localhost:4173"

os.makedirs(OUT_DIR, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page = await context.new_page()
        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 清 IDB
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

        # Home → Confirm → CardView
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_selector("button[title*='忘了']", timeout=10000)

        # 截图 CardView en2cn 模式
        await page.screenshot(path=f"{OUT_DIR}/01-en2cn.png", full_page=False)

        # 切到 cn2en 模式
        await page.locator("button:has-text('中→英')").first.click(timeout=5000)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}/02-cn2en.png", full_page=False)

        # 切到 listen 模式
        await page.locator("button:has-text('听说')").first.click(timeout=5000)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}/03-listen.png", full_page=False)

        # 切到 图说 模式
        await page.locator("button:has-text('图说')").first.click(timeout=5000)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}/04-image.png", full_page=False)

        print("All 4 mode screenshots saved")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
