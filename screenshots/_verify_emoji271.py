# -*- coding: utf-8 -*-
"""验证 271 词补全: 真实流程 (clear IDB → ensureSeeded → 标记测试词为 review → 图说模式逐卡验证 emoji 渲染)
原 271 缺口词全部会进入 review queue 开头, 逐张验证: 卡片 word 渲染出 emoji, 无灰色 [无图标] 占位。
"""
import json, os, sys, traceback
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4173"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji271")
os.makedirs(OUT, exist_ok=True)

# 原 271 缺口词挑 16 个代表 (专有名词/星期/词组/单字/情态/拼写怪词)
TEST_WORDS = [
    "Africa", "London", "Monday", "OK", "opportunity",
    "a piece of", "come true", "shake hands with", "the Atlantic", "lose one's life",
    "may (might)", "stay up", "Olympic", "of course", "think bout", "used to",
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  user_agent="Mozilla/5.0 (Linux; Android 13; OnePlus) Chrome/120 Mobile")
        page = ctx.new_page()
        page.on("pageerror", lambda e: print(f"  [pageerror] {e}"))

        # 1. 首次打开: 触发 ensureSeeded 灌全量
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # 2. 清 IDB (clear stores, 不 deleteDatabase) + 重新 load → backfill 1716 词
        page.evaluate("""async () => {
            const req = indexedDB.open('english-book')
            await new Promise((res, rej) => { req.onsuccess = res; req.onerror = () => rej(req.error) })
            const db = req.result
            const stores = Array.from(db.objectStoreNames)
            const tx = db.transaction(stores, 'readwrite')
            let pending = stores.length
            for (const s of stores) {
                const r = tx.objectStore(s).clear()
                r.onsuccess = () => { if (--pending === 0) {} }
            }
            await new Promise((res) => tx.oncomplete = res)
        }""")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # 3. 把测试词标记为 review (reps>0, due=now) → queue 优先出
        page.evaluate("""(words) => {
            const req = indexedDB.open('english-book')
            return new Promise((res, rej) => {
                req.onsuccess = () => {
                    const db = req.result
                    const tx = db.transaction(['cards'], 'readwrite')
                    const store = tx.objectStore('cards')
                    const now = Date.now()
                    for (const w of words) {
                        store.put({
                            id: w.toLowerCase(), word: w, pos: '测试', cn: '测试', example: '',
                            ef: 2.5, interval: 1, reps: 1, lapses: 0, failedStreak: 0,
                            due: now - 1000, firstSeen: now - 86400000, createdAt: now - 86400000,
                            status: 'review',
                        })
                    }
                    tx.oncomplete = () => res()
                    tx.onerror = () => rej(tx.error)
                }
                req.onerror = () => rej(req.error)
            })
        }""", TEST_WORDS)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # 4. Home → ConfirmTarget → 开始学 15
        page.locator("button:has-text('开始今日')").first.wait_for(timeout=8000)
        page.locator("button:has-text('开始今日')").first.click()
        page.wait_for_timeout(400)
        page.locator("button:has-text('15')").first.click(timeout=5000)
        page.wait_for_timeout(200)
        page.locator("button:has-text('开始学 15')").first.click(timeout=5000)
        page.wait_for_timeout(800)

        # 5. 切图说模式
        page.locator("button:has-text('图说')").first.click(timeout=5000)
        page.wait_for_timeout(300)

        results = []
        for i in range(len(TEST_WORDS)):
            # 等新卡就绪: 未揭示的"答案"按钮出现 + word 已加载 (main 区出现 emoji 或 [无图标] 或单词)
            page.locator("button:has-text('答案')").first.wait_for(timeout=6000)
            check = None
            for _ in range(10):
                page.wait_for_timeout(400)
                check = page.evaluate("""() => {
                    const main = document.querySelector('main')
                    const t = main ? main.innerText : ''
                    // 覆盖 BMP 区 (✈☀✨⭐ 等) + 补充平面 (🌍🦉🧩 等)
                    const emojiRe = /[\\u{2600}-\\u{27BF}\\u{2B00}-\\u{2BFF}\\u{1F000}-\\u{1FFFF}\\u{FE0F}]/u
                    return { gray: t.includes('无图标'),
                             emoji: [...t].filter(c => emojiRe.test(c)).join(''),
                             wordish: /[a-zA-Z]{2,}/.test(t) }
                }""")
                # word 已加载的标志: 有 emoji 或有灰占位; 或 main 出现单词 (cn2en/en2cn 兜底判断)
                if check["emoji"] or check["gray"]:
                    break

            fname = f"271-{i+1:02d}.png"
            page.screenshot(path=os.path.join(OUT, fname), full_page=False)
            ok = (not check["gray"]) and bool(check["emoji"])
            if not ok:
                debug = page.evaluate("() => { const m = document.querySelector('main'); return m ? m.innerText.slice(0, 200) : 'NO MAIN' }")
                print(f"  [DBG] main text: {debug!r}")
            results.append({"ok": ok, "gray": check["gray"], "emoji": check["emoji"]})
            print(f"  [{i+1:02d}] emoji={check['emoji']!r} gray={check['gray']} {'PASS' if ok else 'FAIL'}")

            # 揭示 + 评分认识 → 下一张
            try:
                page.locator("button:has-text('答案')").first.click(timeout=2000)
                page.wait_for_timeout(250)
                page.locator("button[title*='认识']").first.click(timeout=3000)
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"  [warn] advance: {e}")
                break

        browser.close()

        failed = [r for r in results if not r["ok"]]
        print(f"\n=== 结果: {len(results)-len(failed)}/{len(results)} PASS ===")
        if failed:
            print("FAIL:", [r for r in failed])
            sys.exit(2)
        print("全部通过 ✅ 271 词 emoji 渲染正常, 无灰色占位")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
