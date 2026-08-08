"""找一个多义词 (cn 含 /) 在 CardView 截图"""
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

        # 直接 IDB 注入 3 个多义词 + 标 firstSeen=0 + reps=0 (新词)
        await page.evaluate(r"""
async () => {
  return new Promise((resolve) => {
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {
      const db = req.result
      const tx = db.transaction('cards', 'readwrite')
      const store = tx.objectStore('cards')
      // 强制 "a couple of" / "able" / "wake up" 标新
      const targets = ['a couple of', 'able', 'wake up']
      let done = 0
      for (const w of targets) {
        const g = store.get(w)
        g.onsuccess = () => {
          if (g.result) {
            g.result.firstSeen = 0
            g.result.reps = 0
            g.result.due = Date.now() - 1000
            store.put(g.result)
            console.log('[inject] reset', w, 'cn:', g.result.cn)
          }
          done++
          if (done === targets.length) tx.oncomplete = () => resolve('done')
        }
      }
    }
  })
}
""")
        # Home → Confirm → CardView
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_selector("button[title*='忘了']", timeout=10000)

        # 等几秒, 跑几张直到看到目标
        for i in range(20):
            try:
                cur_text = await page.locator("main .text-5xl, main .text-6xl, main .text-4xl").first.inner_text()
                cur = cur_text.strip()
                if cur in ('a couple of', 'able', 'wake up'):
                    # 直接 good (会显示 cn 答案)
                    good_btn = page.locator("button[title*='认识']").first
                    await good_btn.click(timeout=3000)
                    await page.wait_for_timeout(700)
                    # 读 cn 答案
                    cn_text = await page.evaluate(r"""
() => {
  // CardView 答案在 main 内 text-2xl/3xl/4xl
  const divs = document.querySelectorAll('main div')
  for (const d of divs) {
    const t = d.textContent.trim()
    if (t && t.includes('/') && t.length < 50) return t
  }
  return ''
}
""")
                    print(f"  step {i}: 目标词 {cur}, cn 答案: {cn_text}")
                    await page.screenshot(path=f"{OUT_DIR}/06-multi-{cur.replace(' ', '_')}.png", full_page=False)
                    print(f"  saved 06-multi-{cur.replace(' ', '_')}.png")
                    break
                # 没目标, 揭示 + good 跳过
                try:
                    # 先揭示 (但 master CardView 总是显示答案, 没有 reveal 步骤)
                    # 直接 good
                    good_btn = page.locator("button[title*='认识']").first
                    await good_btn.click(timeout=3000)
                except:
                    pass
                await page.wait_for_timeout(700)
            except Exception as e:
                print(f"  step {i}: err {e}")
                break

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
