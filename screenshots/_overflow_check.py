"""
单页下拉检测 — 390x844 viewport (iPhone 14) 逐页截图, 看是否溢出.
判断标准: 页面内容总高度 > 844 - 底部 tab bar 高度 (约 70px) = 774px
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

OUT_DIR = r"D:\10-English-Book\screenshots\overflow-check"
PREVIEW_URL = "http://localhost:4173"
VIEWPORT_W = 390
VIEWPORT_H = 844  # iPhone 14

os.makedirs(OUT_DIR, exist_ok=True)


async def check_page_overflow(page, name: str, scrollable_selector: str = "body"):
    """
    检查一个页面是否在 viewport 内塞下. 返回 (height, content_height, is_overflow).
    """
    info = await page.evaluate(f"""
() => {{
  const body = document.body
  const docEl = document.documentElement
  const fullHeight = Math.max(body.scrollHeight, body.offsetHeight, docEl.clientHeight, docEl.scrollHeight, docEl.offsetHeight)
  const innerHeight = window.innerHeight
  const innerWidth = window.innerWidth
  return {{ fullHeight, innerHeight, innerWidth }}
}}
""")
    height = info['fullHeight']
    inner = info['innerHeight']
    overflow = height > inner + 2  # 容忍 2px
    print(f"  {name}: 内容总高={height}px viewport={inner}px {'⚠️ OVERFLOW' if overflow else '✓ FITS'}")
    return height, inner, overflow


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page = await context.new_page()
        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

        print(f"=== 390x844 viewport 单页下拉检测 ===\n")
        print("→ 打开 preview")
        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 清 IDB (确保新用户状态,无历史)
        print("→ 清 IDB 重新加载")
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

        results = []

        # === 屏 1: Home ===
        print("\n[1/5] Home 屏 (新用户, 0 学过)")
        try:
            await page.wait_for_selector("text=开始今日", timeout=8000)
            await page.screenshot(path=f"{OUT_DIR}/01-home.png", full_page=False)
            results.append(("Home", *await check_page_overflow(page, "Home")))
        except Exception as e:
            print(f"  Home 没出现: {e}")

        # === 屏 2: Confirm ===
        print("\n[2/5] Confirm 屏")
        try:
            await page.click("button:has-text('开始今日')", timeout=5000)
            await page.wait_for_timeout(500)
            await page.wait_for_selector("text=今天学几个", timeout=5000)
            await page.screenshot(path=f"{OUT_DIR}/02-confirm.png", full_page=False)
            results.append(("Confirm", *await check_page_overflow(page, "Confirm")))
        except Exception as e:
            print(f"  Confirm 失败: {e}")
            return

        # === 屏 3: CardView (默认 en2cn) ===
        print("\n[3/5] CardView (en2cn)")
        try:
            await page.locator("button").filter(has_text="15").first.click(timeout=5000)
            await page.wait_for_timeout(200)
            await page.click("button:has-text('开始学 15')", timeout=5000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"{OUT_DIR}/03-cardview-en2cn.png", full_page=False)
            results.append(("CardView-en2cn", *await check_page_overflow(page, "CardView-en2cn")))
        except Exception as e:
            print(f"  CardView en2cn 失败: {e}")

        # === 屏 4: History (无数据) ===
        print("\n[4/5] History 屏 (无 session)")
        try:
            # TabBar 切到历史
            await page.locator("nav button:has-text('历史')").first.click(timeout=5000)
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUT_DIR}/04-history-empty.png", full_page=False)
            results.append(("History-empty", *await check_page_overflow(page, "History-empty")))
        except Exception as e:
            print(f"  History 失败: {e}")

        # === 屏 4b: History (有 session 数据 - 通过 CardView 评分产生) ===
        print("\n[4b/5] History 屏 (有 session 数据, 评 5 张后回历史)")
        try:
            # 切到 CardView, 评 5 张
            await page.locator("nav button:has-text('今日')").first.click(timeout=5000)
            await page.wait_for_timeout(500)
            # CardView 应该还在 (active session)
            for i in range(5):
                try:
                    # 评分按钮 (title='认识')
                    good_btn = page.locator("button[title*='认识']").first
                    await good_btn.click(timeout=3000)
                    await page.wait_for_timeout(700)
                except Exception:
                    break
            # 切到历史
            await page.locator("nav button:has-text('历史')").first.click(timeout=5000)
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUT_DIR}/04b-history-with-data.png", full_page=False)
            results.append(("History-with-data", *await check_page_overflow(page, "History-with-data")))
        except Exception as e:
            print(f"  History with data 失败: {e}")

        # === 屏 5: Settings ===
        print("\n[5/5] Settings 屏")
        try:
            await page.locator("nav button:has-text('设置')").first.click(timeout=5000)
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUT_DIR}/05-settings.png", full_page=False)
            results.append(("Settings", *await check_page_overflow(page, "Settings")))
        except Exception as e:
            print(f"  Settings 失败: {e}")

        # 总结
        print("\n=== 总结 ===")
        for name, h, inner, overflow in results:
            mark = "❌" if overflow else "✓"
            print(f"  {mark} {name}: {h}px / {inner}px")

        # 标记最严重的
        worst = [r for r in results if r[3]]
        if worst:
            print(f"\n⚠️  溢出页面: {[r[0] for r in worst]}")
            print("需要压扁")
        else:
            print(f"\n✓ 全部塞下")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
