"""把 firstSeen=0 设给 30+ 个多义词, 让 CardView 必出多义词"""
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
        page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:100]}"))

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

        # 把 ALL cn 含 / 的词 (限 30 个) 标新
        target_words = await page.evaluate(r"""
async () => {
  return new Promise((resolve) => {
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {
      const db = req.result
      const tx = db.transaction('cards', 'readwrite')
      const store = tx.objectStore('cards')
      const all = store.getAll()
      all.onsuccess = () => {
        const withSlash = all.result.filter(c => c.cn && c.cn.includes('/')).slice(0, 30)
        const ws = withSlash.map(c => c.word)
        for (const c of withSlash) {
          c.firstSeen = 0
          c.reps = 0
          c.due = Date.now() - 1000
          store.put(c)
        }
        tx.oncomplete = () => resolve(ws)
      }
    }
  })
}
""")
        print(f"  注入 {len(target_words)} 个多义词: {target_words[:5]}...")

        # Home → Confirm → CardView
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_selector("button[title*='忘了']", timeout=10000)

        # 直接截图 (默认 en2cn 模式, 单词显示 + cn 答案)
        # 第一张应该就是 a couple of (前面 first)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}/07-multi-en2cn.png", full_page=False)
        print("  saved 07-multi-en2cn.png")

        # 切 cn2en
        await page.locator("button:has-text('中→英')").first.click(timeout=5000)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}/08-multi-cn2en.png", full_page=False)
        print("  saved 08-multi-cn2en.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
