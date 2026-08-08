"""
UI 修复验证:
1. CardView 评分按钮没有 1/2/3 kbd
2. History 7 周热力图 100 词才深绿
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

OUT_DIR = r"D:\10-English-Book\screenshots\ux-fix"
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

        print("→ 打开 preview URL")
        await page.goto(PREVIEW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 清 IDB + 重新加载
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

        # Home → Confirm → CardView
        print("→ Home → Confirm → CardView")
        await page.wait_for_selector("text=开始今日", timeout=10000)
        await page.click("button:has-text('开始今日')", timeout=5000)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("text=今天学几个", timeout=5000)
        await page.locator("button").filter(has_text="15").first.click(timeout=5000)
        await page.wait_for_timeout(200)
        await page.click("button:has-text('开始学 15')", timeout=5000)
        await page.wait_for_selector("button[title*='忘了']", timeout=10000)

        # === 测试 1: 评分按钮没有 1/2/3 kbd ===
        print("\n→ 测试 1: 评分按钮 kbd 是否存在")
        kbd_count = await page.locator("kbd").count()
        print(f"  CardView 里 kbd 元素数: {kbd_count}")
        test1_pass = kbd_count == 0

        # 截图 CardView (3 个评分按钮)
        await page.screenshot(path=f"{OUT_DIR}/01-cardview-no-kbd.png", full_page=False)

        if test1_pass:
            print("  PASS: 1/2/3 提示已去掉")
        else:
            print(f"  FAIL: 仍有 {kbd_count} 个 kbd 元素")

        # 回到 Home
        print("\n→ 回到 Home → 切到历史")
        # 点 "今日到这" 完成
        # 或者直接用 TabBar 切到历史 (但要等 session 跑完或手动结束)
        # 简化:直接 evaluate 进 history
        # 实际: 切 TabBar 走
        # CardView 有 TabBar, 点 "今日" tab → home
        # 然后点 "历史" tab → history
        await page.locator("nav button:has-text('今日')").first.click(timeout=5000)
        await page.wait_for_timeout(500)
        await page.locator("nav button:has-text('历史')").first.click(timeout=5000)
        await page.wait_for_timeout(800)

        # === 测试 2: 热力图 100 词才深绿 ===
        print("\n→ 测试 2: 注入 IDB heatmap 数据, 验证 100 词深绿")
        # 注入 100 reviews (今天) 测深绿
        injected = await page.evaluate(r"""
async () => {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {
      const db = req.result
      if (!Array.from(db.objectStoreNames).includes('reviews')) {
        resolve('no reviews store')
        return
      }
      const tx = db.transaction(['reviews', 'sessions', 'cards'], 'readwrite')
      const now = Date.now()
      const today = new Date().toISOString().split('T')[0]
      tx.objectStore('sessions').put({
        id: today,
        startedAt: now - 3600000,
        endedAt: now,
        targetCount: 100,
        completedCount: 100,
        reviewsCount: 100,
        newCount: 50,
        date: today,
      })
      const allCards = tx.objectStore('cards').getAll()
      allCards.onsuccess = () => {
        const reviews = tx.objectStore('reviews')
        for (const c of allCards.result.slice(0, 100)) {
          reviews.add({
            cardId: c.id,
            sessionId: today,
            grade: 'good',
            prevEf: 2.5,
            prevInterval: 0,
            prevReps: 0,
            reviewedAt: now - Math.random() * 3600000,
          })
        }
      }
      tx.oncomplete = () => resolve('injected 100 reviews for ' + today)
      tx.onerror = () => reject('tx error')
    }
    req.onerror = () => reject('req error')
  })
}
""")
        print(f"  注入: {injected}")

        # 重新加载 History 屏
        await page.reload()
        await page.wait_for_timeout(2000)
        await page.locator("nav button:has-text('历史')").first.click(timeout=5000)
        await page.wait_for_timeout(1000)

        # 截图 History (热力图)
        await page.screenshot(path=f"{OUT_DIR}/02-history-heatmap-100.png", full_page=False)

        # 验证: 找到今天 cell, 看 background 是否深绿
        heatmap_info = await page.evaluate(r"""
() => {
  const cells = document.querySelectorAll('[title*="词"]')
  if (cells.length === 0) return { found: false }
  const out = []
  for (const c of cells) {
    const title = c.getAttribute('title') || ''
    const match = title.match(/(\d{4}-\d{2}-\d{2}).*?(\d+) 词/)
    if (match) {
      out.push({ date: match[1], count: parseInt(match[2]), bg: c.style.background, opacity: c.style.opacity })
    }
  }
  return { found: true, cells: out }
}
""")
        print(f"  heatmap cells: {heatmap_info}")

        # 找今天 (>99 词) 的 cell, 验证 opacity = 1
        test2_pass = False
        if heatmap_info.get('found'):
            for cell in heatmap_info['cells']:
                if cell['count'] >= 100:
                    if cell['opacity'] == '1' and 'success' in cell['bg']:
                        print(f"  PASS: {cell['date']} count={cell['count']} → 深绿 (opacity=1)")
                        test2_pass = True
                    else:
                        print(f"  FAIL: {cell['date']} count={cell['count']} 但 opacity={cell['opacity']} bg={cell['bg']}")

        if not test2_pass:
            print(f"  注意: 没找到 >= 100 词的 cell, 截图看实际效果")

        # 测试 3: 验证 50-99 是中绿
        await page.evaluate(r"""
async () => {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('english-book')
    req.onsuccess = () => {
      const db = req.result
      const tx = db.transaction(['reviews', 'sessions', 'cards'], 'readwrite')
      const now = Date.now()
      const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
      tx.objectStore('sessions').put({
        id: yesterday,
        startedAt: now - 86400000 - 3600000,
        endedAt: now - 86400000,
        targetCount: 50,
        completedCount: 50,
        reviewsCount: 50,
        newCount: 25,
        date: yesterday,
      })
      const allCards = tx.objectStore('cards').getAll()
      allCards.onsuccess = () => {
        const reviews = tx.objectStore('reviews')
        for (const c of allCards.result.slice(0, 50)) {
          reviews.add({
            cardId: c.id, sessionId: yesterday, grade: 'good',
            prevEf: 2.5, prevInterval: 0, prevReps: 0,
            reviewedAt: now - 86400000,
          })
        }
      }
      tx.oncomplete = () => resolve('50 reviews yesterday injected')
      tx.onerror = () => reject('tx error')
    }
    req.onerror = () => reject('req error')
  })
}
""")

        await page.reload()
        await page.wait_for_timeout(2000)
        await page.locator("nav button:has-text('历史')").first.click(timeout=5000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUT_DIR}/03-history-heatmap-50.png", full_page=False)

        await browser.close()

        if test1_pass and test2_pass:
            print("\n✅ ALL PASS")
            return True
        elif test1_pass:
            print(f"\n⚠️  test1 PASS, test2 FAIL")
            return False
        else:
            print(f"\n❌ FAIL")
            return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
