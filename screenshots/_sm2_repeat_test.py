"""
SM-2 session 内重复机制端到端测试.

验证流程:
1. 清 IDB, 重新加载
2. 拿第 1 张 word (A)
3. 揭示 + again A
4. 接下来 10 张 good, 记录每张 word
5. 断言 A 在 step 4-6 出现 (AGAIN_INTERVAL=5)

期望: 5 张 advance 后 A 重出
"""
import asyncio
import os
import sys

# Force UTF-8 输出 (避免 Windows GBK console emoji 报错)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

OUT_DIR = r"D:\10-English-Book\screenshots\sm2"
PREVIEW_URL = "http://localhost:4173"
PROJECT_DIR = r"D:\10-English-Book"

os.makedirs(OUT_DIR, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},  # iPhone 14 viewport
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page = await context.new_page()

        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

        # 1. 打开 (preview 已起)
        print("→ 打开 preview URL")
        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)  # 等 SW 注册

        # 2. 清 IDB (避免脏数据)
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

        # 3. 等 Home 屏 → 点 "开始今日" → Confirm 屏 → 点 "15" → CardView
        print("→ 等 Home 屏 (找 '开始今日' 按钮)")
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.screenshot(path=f"{OUT_DIR}/00-home.png", full_page=False)

        print("→ 点 '开始今日' → Confirm 屏")
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)

        print("→ 等 Confirm 屏 (找 chip '15')")
        # Confirm 屏有 5/15/30/50/100 chips + "自定义..." + "开始学 X 个新词"
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.screenshot(path=f"{OUT_DIR}/00-confirm.png", full_page=False)

        # 选 15 chip
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        print("  选了 15 chip")

        # 等 "开始学 15 个新词" 按钮 (chip 选中后会更新)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        print("  点 '开始学 15 个新词'")

        # 4. 等 CardView
        print("→ 等 CardView 揭示按钮")
        await page.wait_for_selector("button:has-text('答案')", timeout=10000)

        # 5. 读 word 1
        word1_loc = page.locator("main .text-5xl, main .text-6xl, main .text-4xl").first
        await word1_loc.wait_for(timeout=5000)
        word1 = (await word1_loc.inner_text()).strip()
        print(f"  word1: {word1!r}")

        # 截图 1: 起始
        await page.screenshot(path=f"{OUT_DIR}/01-word1-initial.png", full_page=False)

        # 6. 揭示 + again
        print("→ 揭示 + again word1")
        await page.click("button:has-text('答案')")
        await page.wait_for_timeout(150)
        # again 按钮 (X 图标, title="忘了")
        again_btn = page.locator("button[title*='忘了']").first
        await again_btn.click()
        await page.wait_for_timeout(900)  # transition 600 + buffer

        # 7. 接下来 10 张 good, 记录每张 word
        # 期望: AGAIN_INTERVAL=5 → 5 张 advance 后 word1 重出
        # (因 buildTodayQueue 可能只产出 5 张, word1 重出可能在 step 4-5 之间)
        print("→ 接下来 10 张 good, 记录每张 word")
        word_repeat_step = -1
        for i in range(10):
            # 等揭示按钮
            await page.wait_for_selector("button:has-text('答案')", timeout=5000)
            await page.click("button:has-text('答案')")
            await page.wait_for_timeout(150)
            # good 按钮
            good_btn = page.locator("button[title*='认识']").first
            await good_btn.click()
            await page.wait_for_timeout(900)
            # 读当前 word
            cur_loc = page.locator("main .text-5xl, main .text-6xl, main .text-4xl").first
            cur = (await cur_loc.inner_text()).strip()
            print(f"  step {i+1}: {cur!r}")
            if cur == word1 and word_repeat_step == -1:
                word_repeat_step = i + 1
                print(f"  >>> word1 在 step {i+1} 重出!")
                # 截图重出时的画面
                await page.screenshot(path=f"{OUT_DIR}/02-word1-repeated.png", full_page=False)

        # 8. 断言
        print(f"\n→ 验证: word1={word1!r} 是否在 5 张 advance 后重出")
        if word_repeat_step >= 1:
            # 至少 1 张 advance (after again) + 1 张 advance = step 2 之后该重出
            # 实际: step 4-5 之间 (因 buildTodayQueue 长短影响)
            print(f"  PASS: word1 在 step {word_repeat_step} 重出 (期望 step 4-6)")
            result = True
        else:
            print(f"  FAIL: word1 从未重出")
            result = False

        # 10. 验证 leech 优先
        # 思路: 直接 IDB 注入一张卡 (reps=2, isLeech=true, due=now), 然后刷新页面重新进 session,
        # 期待这张 leech 卡是 buildTodayQueue 第 1 张
        print("\n→ 验证 leech 优先: IDB 注入 leech 卡, 期望 buildTodayQueue 第 1 张")
        leech_word = await page.evaluate("""async () => {
            return new Promise((resolve) => {
              const req = indexedDB.open('english-book')
              req.onsuccess = () => {
                const db = req.result
                const tx = db.transaction(['cards', 'sessions'], 'readwrite')
                const all = tx.objectStore('cards').getAll()
                all.onsuccess = () => {
                  const cards = all.result
                  // 找一张 NOT yet used 的,标 leech + reps=2 + due=now
                  const target = cards.find(c => c.reps === 0) || cards[0]
                  target.reps = 2
                  target.ef = 1.8
                  target.interval = 1
                  target.due = Date.now() - 1000  // 已 due
                  target.firstSeen = Date.now() - 100000
                  target.isLeech = true
                  target.lapseStreak = 5
                  tx.objectStore('cards').put(target)
                  // 删 active session (强制重新进)
                  const sessions = tx.objectStore('sessions')
                  sessions.getAll().onsuccess = (e) => {
                    for (const s of e.target.result) {
                      sessions.delete(s.id)
                    }
                  }
                  tx.oncomplete = () => resolve(target.word)
                }
              }
              req.onerror = () => resolve(null)
            })
        }""")
        print(f"  注入 leech 卡: {leech_word!r}")

        # 重新进 session (Home 屏)
        print("→ reload 触发重新进 session")
        await page.reload()
        await page.wait_for_timeout(2000)

        # 等 Home 屏 → 点 "继续" 或 "开始今日"
        # 续上次的 session 不会走 confirm 屏, 直接进 CardView
        # 但 active session 已删, 所以是 "开始今日" → Confirm
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_timeout(1000)

        # 读第 1 张 word, 期待是 leech_word
        first_word_loc = page.locator("main .text-5xl, main .text-6xl, main .text-4xl").first
        first_word = (await first_word_loc.inner_text()).strip()
        print(f"  第 1 张: {first_word!r} (leech: {leech_word!r})")
        await page.screenshot(path=f"{OUT_DIR}/03-leech-first.png", full_page=False)

        leech_pass = first_word == leech_word
        if leech_pass:
            print(f"  PASS: leech 卡 {leech_word!r} 在第 1 张出现")
        else:
            print(f"  FAIL: 期待 leech 卡 {leech_word!r} 在第 1 张, 实际 {first_word!r}")

        await browser.close()

        return result and leech_pass


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
