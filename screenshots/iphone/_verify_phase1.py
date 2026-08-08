"""Phase 1 验收脚本 (P1 + P1.5)

覆盖:
  - 1.7 持久化: 评分 1 张 → 刷新 → due 日期 / firstSeen / reps 在 IDB
  - 1.5.4 24h 续 session: 开始 → 刷新 → 自动续上 active session
  - 1.5.4 24h 边界: 25h 前的 session 不续

前置: dev server 已在 http://127.0.0.1:5173 跑
注意: Vite HMR WebSocket 长连接 → 不用 networkidle, 用 domcontentloaded
用法: python _verify_phase1.py
"""
import sys, io
# 强制 UTF-8 输出 (Windows 默认 GBK 编码会炸 emoji)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import json, os, traceback

URL = 'http://127.0.0.1:5173/?bust=verify'

def get_idb_dump(page):
    """dump IndexedDB 中所有 cards / reviews / settings / sessions 行"""
    return page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open('english-book');
            req.onsuccess = () => {
                const db = req.result;
                const out = {};
                const stores = ['cards', 'reviews', 'settings', 'sessions'];
                let pending = stores.length;
                if (pending === 0) resolve(out);
                for (const s of stores) {
                    const tx = db.transaction(s, 'readonly');
                    const r = tx.objectStore(s).getAll();
                    r.onsuccess = () => {
                        out[s] = r.result;
                        if (--pending === 0) resolve(out);
                    };
                    r.onerror = () => reject(r.error);
                }
            };
            req.onerror = () => reject(req.error);
        });
    }""")

def clear_idb(page):
    """清空 IDB 所有 store (不动 schema). 比 deleteDatabase 安全 (不卡 onblocked)."""
    return page.evaluate("""async () => {
        return new Promise((resolve, reject) => {
            const req = indexedDB.open('english-book');
            req.onsuccess = () => {
                const db = req.result;
                const stores = Array.from(db.objectStoreNames);
                const tx = db.transaction(stores, 'readwrite');
                let pending = stores.length;
                if (pending === 0) resolve();
                for (const s of stores) {
                    const r = tx.objectStore(s).clear();
                    r.onsuccess = () => { if (--pending === 0) resolve(); };
                    r.onerror = () => reject(r.error);
                }
            };
            req.onerror = () => reject(req.error);
        });
    }""")

def fail(msg):
    print(f'❌ FAIL: {msg}')
    sys.exit(1)

def ok(msg):
    print(f'✅ {msg}')

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone)
        page = context.new_page()

        # ============= 1.7 持久化验收 =============
        print('\n========== 1.7 持久化验收 ==========')
        # 清空 IDB store, 重新开始 (用 clear() 而非 deleteDatabase, 避免 onblocked 死锁)
        page.goto(URL, wait_until='domcontentloaded')
        page.wait_for_timeout(1500)
        clear_idb(page)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        # 进入 CardView
        page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
        page.locator('button:has-text("开始今日")').first.click()
        page.wait_for_timeout(1500)
        # 揭示 + 评分
        page.locator('button:has-text("揭示答案")').first.wait_for(timeout=3000)
        page.locator('button:has-text("揭示答案")').first.click()
        page.wait_for_timeout(400)
        page.locator('button[title="认识"]').first.click()
        page.wait_for_timeout(1000)

        # 记录评分后状态
        before = get_idb_dump(page)
        rated_card = next((c for c in before['cards'] if c['reps'] >= 1), None)
        if not rated_card:
            fail(f'评分后没找到 reps >= 1 的 card. cards: {before["cards"]}')
        ok(f'评分后找到 card: {rated_card["word"]} ef={rated_card["ef"]} interval={rated_card["interval"]} reps={rated_card["reps"]}')
        if rated_card['firstSeen'] <= 0:
            fail(f'firstSeen 应该是正数, 实际 {rated_card["firstSeen"]}')
        ok(f'firstSeen 已写入: {rated_card["firstSeen"]}')
        if rated_card['interval'] != 1:
            fail(f'good 评分后 interval 应该是 1, 实际 {rated_card["interval"]}')
        ok(f'interval = 1 (good 第一次)')

        # 刷新页面
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(1500)

        # 验证 IDB 还在
        after = get_idb_dump(page)
        after_card = next((c for c in after['cards'] if c['id'] == rated_card['id']), None)
        if not after_card:
            fail('刷新后 card 丢了')
        if (after_card['ef'] != rated_card['ef']
            or after_card['interval'] != rated_card['interval']
            or after_card['reps'] != rated_card['reps']
            or after_card['due'] != rated_card['due']):
            fail(f'刷新后 card 状态变了:\n  刷新前: {rated_card}\n  刷新后: {after_card}')
        ok(f'刷新后 card 状态保留: ef={after_card["ef"]} interval={after_card["interval"]} reps={after_card["reps"]} due={after_card["due"]}')

        if len(after['reviews']) != 1:
            fail(f'reviews 表行数错: 期望 1, 实际 {len(after["reviews"])}')
        ok(f'reviews 表有 {len(after["reviews"])} 条 (一次评分 = 一行)')

        # ============= 1.5.4 24h 续 session 验收 =============
        print('\n========== 1.5.4 24h 续 session 验收 ==========')
        # 此时应该还有 active session (24h 内, 刷新没关 tab)
        active = [s for s in after['sessions'] if s['endedAt'] is None]
        if len(active) != 1:
            fail(f'24h 内应该续上 1 个 active session, 实际 {len(active)}. sessions: {after["sessions"]}')
        ok(f'24h 内 active session 自动续上: id={active[0]["id"]} completed={active[0]["completedCount"]}')

        # 验证刷新后进入的是 CardView (不是 Home)
        try:
            page.locator('button:has-text("揭示答案")').first.wait_for(timeout=3000)
            ok('刷新后直接进入 CardView (没回 Home) — session 续上成功')
        except Exception:
            fail('刷新后应该直接进 CardView, 实际进 Home')

        # 进度条应该显示 1 / 30
        prog_text = page.locator('text=/\\d+ \\/ 30/').first.text_content()
        if '1 / 30' not in prog_text:
            fail(f'进度条应显示 "1 / 30", 实际 "{prog_text}"')
        ok(f'进度条显示 "{prog_text}" — session 进度保留')

        # ============= 1.5.4 24h 边界验收 =============
        print('\n========== 1.5.4 24h 边界验收 ==========')
        # 把 startedAt 改到 25h 前, 看是否不续
        page.evaluate("""async () => {
            return new Promise((resolve, reject) => {
                const r = indexedDB.open('english-book');
                r.onsuccess = () => {
                    const db = r.result;
                    const tx = db.transaction('sessions', 'readwrite');
                    const g = tx.objectStore('sessions').getAll();
                    g.onsuccess = () => {
                        const sessions = g.result;
                        for (const s of sessions) {
                            s.startedAt = Date.now() - 25 * 60 * 60 * 1000;
                            tx.objectStore('sessions').put(s);
                        }
                    };
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                };
                r.onerror = () => reject(r.error);
            });
        }""")
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(1500)
        # 25h 前的不应续, 应回 Home
        try:
            page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
            ok('25h 前的 session 不续 — 回到 Home (新一天) ')
        except Exception:
            fail('25h 前的 session 应该不续, 实际仍进 CardView')

        # 最终 dump
        print('\n========== 最终 IDB 状态 ==========')
        final = get_idb_dump(page)
        print(f'  cards: {len(final["cards"])} 张')
        print(f'  reviews: {len(final["reviews"])} 条')
        print(f'  settings: {len(final["settings"])} 条 (key={final["settings"][0]["key"] if final["settings"] else "n/a"})')
        print(f'  sessions: {len(final["sessions"])} 条 (含历史)')

        browser.close()
        print('\n🎉 全部验收通过!')
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    sys.exit(1)
