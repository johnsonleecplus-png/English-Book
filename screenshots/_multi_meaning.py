"""截图一个有多释义的词, 看 / 分隔符效果"""
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
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        )
        page = await context.new_page()
        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}"))

        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
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

        # 走 N 张直到遇到有多义词的词
        # 直接 IDB 查 vocab, 找 cn 含 / 的词
        multi_words = await page.evaluate(r"""
async () => {
  return new Promise((resolve) => {
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {
      const db = req.result
      const tx = db.transaction('cards', 'readonly')
      const all = tx.objectStore('cards').getAll()
      all.onsuccess = () => {
        const cards = all.result
        const withSlash = cards.filter(c => c.cn && c.cn.includes('/'))
        resolve(withSlash.slice(0, 5).map(c => ({ word: c.word, cn: c.cn, pos: c.pos })))
      }
    }
  })
}
""")
        print(f"  cn 含 / 的词: {len(multi_words)}")
        for w in multi_words:
            print(f"    {w['word']}: {w['cn']}")

        # 把 cards 顺序调一下, 让 multi_word 在前
        if multi_words:
            # 通过 IDB 修改 firstSeen=now 强制重新进 queue
            # 简单: 改 buildTodayQueue 时用这些词填前 5 张
            # 直接 page.evaluate 改 IDB
            target = multi_words[:3]
            target_words = [w['word'] for w in target]
            await page.evaluate(f"""
async () => {{
  return new Promise((resolve) => {{
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {{
      const db = req.result
      const tx = db.transaction('cards', 'readwrite')
      const store = tx.objectStore('cards')
      const targetWords = {target_words}
      let done = 0
      for (const w of targetWords) {{
        const g = store.get(w)
        g.onsuccess = () => {{
          if (g.result) {{
            g.result.firstSeen = 0  // 强制 firstSeen=0 让进 new queue
            g.result.due = Date.now() + 86400000  // 跳过今日
            store.put(g.result)
          }}
          done++
          if (done === targetWords.length) tx.oncomplete = () => resolve('done')
        }}
      }}
    }}
  }})
}}
""")
            print(f"  把 {target_words} 标 firstSeen=0")

        # 截图多义词的卡 (循环评到)
        # 简化: 等几秒, 让 useQueue 拉, 然后看当前词
        for i in range(15):
            cur_text = await page.locator("main .text-5xl, main .text-6xl, main .text-4xl").first.inner_text()
            cur = cur_text.strip()
            if any(t == cur for t in target_words):
                print(f"  step {i}: 找到目标词 {cur}")
                break
            # 揭示 + good
            await page.click("button:has-text('答案')")  # 实际已没有 '答案' 按钮, master 重构
            await page.wait_for_timeout(100)
            try:
                # 直接 good
                good_btn = page.locator("button[title*='认识']").first
                await good_btn.click(timeout=3000)
            except:
                # 没揭示步骤, 直接 good
                good_btn = page.locator("button[title*='认识']").first
                await good_btn.click(timeout=3000)
            await page.wait_for_timeout(700)

        # 截图
        await page.screenshot(path=f"{OUT_DIR}/05-multi-meaning.png", full_page=False)
        print("  saved 05-multi-meaning.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
