"""
验证 CardView 揭示步骤:
- 进入 CardView 时, 卡片显示 ? 提示 + "答案" 按钮 (未揭示)
- 点 "答案" 按钮后, 卡片显示完整 pos/cn/word/example + 3 评分按钮
- 按 Space 键也能揭示
- 4 个模式都验证 (image/en2cn/cn2en/listen)
- 0 溢出 验证 (844px viewport)
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

OUT_DIR = r"D:\10-English-Book\screenshots\reveal-step"
PREVIEW_URL = "http://localhost:4173"

os.makedirs(OUT_DIR, exist_ok=True)


async def check_overflow(page, label: str) -> bool:
    info = await page.evaluate("""() => ({
        scrollH: document.documentElement.scrollHeight,
        clientH: document.documentElement.clientHeight,
    })""")
    overflow = info["scrollH"] - info["clientH"]
    ok = overflow <= 1
    print(f"  [overflow.{label}] scrollH={info['scrollH']} clientH={info['clientH']} overflow={overflow} {'OK' if ok else 'OVERFLOW'}")
    return ok


async def advance_to_masked(page, label: str):
    """如果当前卡片是 revealed 状态, 评分一张前进到新的 masked 卡片"""
    has_答案 = await page.locator("button:has-text('答案')").count()
    if has_答案 == 0:
        # 当前是 revealed, 评分前进
        await page.locator("button[title*='认识']").first.click(timeout=5000)
        await page.wait_for_timeout(900)  # 等动画 + 加载新卡
        print(f"  [{label}] advanced to fresh masked card")
    else:
        print(f"  [{label}] already masked")


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
        await page.wait_for_timeout(500)

        all_ok = True

        # === 测试 4 个模式 ===
        modes = [
            ("01-en2cn",  "英→中"),
            ("02-cn2en",  "中→英"),
            ("03-listen", "听说"),
            ("04-image",  "图说"),
        ]

        for label, mode_label in modes:
            print(f"\n=== {label} (mode: {mode_label}) ===")
            await page.locator(f"button:has-text('{mode_label}')").first.click(timeout=5000)
            await page.wait_for_timeout(200)
            await advance_to_masked(page, label)

            # --- 未揭示截图 ---
            await page.screenshot(path=f"{OUT_DIR}/{label}-masked.png", full_page=False)
            ok = await check_overflow(page, f"{label}-masked")
            all_ok = all_ok and ok

            # 验证 答案 按钮 + ? 提示
            reveal_btn = await page.locator("button:has-text('答案')").count()
            masked_q = await page.locator("text=?").count()
            print(f"  [masked] 答案 button={reveal_btn} (期望 1) ? hint={masked_q} (期望 ≥ 1)")
            all_ok = all_ok and (reveal_btn == 1 and masked_q >= 1)

            # --- 点 答案 按钮揭示 ---
            await page.locator("button:has-text('答案')").first.click(timeout=5000)
            await page.wait_for_timeout(300)

            await page.screenshot(path=f"{OUT_DIR}/{label}-revealed.png", full_page=False)
            ok = await check_overflow(page, f"{label}-revealed")
            all_ok = all_ok and ok

            # 验证评分按钮 (忘了/模糊/认识)
            forgot = await page.locator("button[title*='忘了']").count()
            fuzzy = await page.locator("button[title*='模糊']").count()
            known = await page.locator("button[title*='认识']").count()
            reveal_after = await page.locator("button:has-text('答案')").count()
            print(f"  [revealed] rating btns (忘了/模糊/认识)={forgot}/{fuzzy}/{known} 答案 button after={reveal_after} (期望 0)")
            all_ok = all_ok and (forgot == 1 and fuzzy == 1 and known == 1 and reveal_after == 0)

        # === 测试 Space 键揭示 ===
        print(f"\n=== 05-space-reveal (en2cn) ===")
        await page.locator("button:has-text('英→中')").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await advance_to_masked(page, "05")
        await page.screenshot(path=f"{OUT_DIR}/05-space-01-masked.png", full_page=False)
        # 按 Space
        await page.keyboard.press("Space")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT_DIR}/05-space-02-revealed.png", full_page=False)
        ok = await check_overflow(page, "05-space-revealed")
        all_ok = all_ok and ok
        forgot = await page.locator("button[title*='忘了']").count()
        print(f"  [space-revealed] rating btn (忘了)={forgot} (期望 1)")
        all_ok = all_ok and (forgot == 1)

        print(f"\n=== 总结 ===")
        print(f"  {'PASS' if all_ok else 'FAIL'}: 揭示步骤 + 4 模式 + 0 溢出")
        print(f"  截图: {OUT_DIR}")

        await browser.close()
        return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
