"""Phase 3.1 verify: ConfirmTarget 屏
- 01 home 显示「开始今日」按钮
- 02 confirm-first 首次使用, 默认 15
- 03 confirm-day2 利旧 (昨天 30, 默认 30 高亮)
- 04 confirm-custom 自定义输入 25
- 05 active 选了 30 后, queue 跑 30 张
- 06 home-after 显示 30/30 完美达标
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase31')
os.makedirs(OUT, exist_ok=True)

TEST_WORDS = [{'word': f'w{i}', 'cn': str(i), 'pos': 'n.', 'example': ''} for i in range(80)]


def clear_and_seed(page, words, daily_target=15):
    return page.evaluate(f"""async () => {{
        return new Promise((resolve, reject) => {{
            const req = indexedDB.open('english-book');
            req.onsuccess = () => {{
                const db = req.result;
                const stores = Array.from(db.objectStoreNames);
                const tx = db.transaction(stores, 'readwrite');
                let pending = stores.length;
                if (pending === 0) {{ seed(); return; }}
                for (const s of stores) {{
                    const r = tx.objectStore(s).clear();
                    r.onsuccess = () => {{ if (--pending === 0) seed(); }};
                }}
                function seed() {{
                    const words = {words};
                    const now = Date.now();
                    const tx2 = db.transaction(['cards','settings'], 'readwrite');
                    for (const w of words) {{
                        tx2.objectStore('cards').put({{
                            id: w.word.toLowerCase(),
                            word: w.word, pos: w.pos, cn: w.cn, example: w.example,
                            ef: 2.5, interval: 0, reps: 0,
                            due: now, firstSeen: 0, createdAt: now,
                        }});
                    }}
                    tx2.objectStore('settings').put({{
                        key: 'main', dailyNewTarget: {daily_target}, newRatio: 0.5, seededAt: now,
                    }});
                    tx2.oncomplete = () => resolve();
                }}
            }};
        }});
    }}""")


def run_first(p, iphone, label, daily_target=15):
    """首次使用: settings 15, 累计 0 词"""
    browser = p.chromium.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()

    page.goto(f'http://127.0.0.1:5173/?bust=cf1{label}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    clear_and_seed(page, TEST_WORDS, daily_target)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    # Home
    page.screenshot(path=os.path.join(OUT, f'{label}-01-home.png'), full_page=True)
    print(f'  [{label}] 01-home')

    # 开始今日 → confirm
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(OUT, f'{label}-02-confirm.png'), full_page=True)
    print(f'  [{label}] 02-confirm')

    # 选 30 (chip)
    page.locator('button:has-text("30"):not(:has-text("个"))').first.click()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(OUT, f'{label}-03-confirm-pick30.png'), full_page=True)
    print(f'  [{label}] 03-confirm-pick30')

    # 开始
    page.locator('button:has-text("开始学 30 个新词")').first.click()
    page.wait_for_timeout(1500)

    # 跑完 30 张
    for i in range(35):
        try:
            page.locator('button:has-text("揭示答案")').first.click(timeout=1500)
            page.wait_for_timeout(150)
            page.locator('button[title="认识"]').first.click()
            page.wait_for_timeout(600)
        except Exception:
            break

    # queue-done
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(OUT, f'{label}-04-queue-done.png'), full_page=True)
    print(f'  [{label}] 04-queue-done')

    # 点 "再学 10 个新词" → 续 10 张
    try:
        page.locator('button:has-text("再学 10 个新词")').first.click()
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f'  [{label}] add fail: {e}')

    # 回首页
    try:
        page.wait_for_timeout(300)
        page.locator('button:has-text("今日到这")').first.wait_for(timeout=3000)
        page.locator('button:has-text("今日到这")').first.click()
        page.wait_for_timeout(800)
    except Exception as e:
        print(f'  [{label}] back fail: {e}')

    page.screenshot(path=os.path.join(OUT, f'{label}-05-home-after.png'), full_page=True)
    print(f'  [{label}] 05-home-after')

    browser.close()


def run_day2(p, iphone, label, daily_target=30):
    """第二天: settings 30 (昨天学的), 累计 30 词 (因为是测试第二阶段)"""
    browser = p.chromium.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()

    page.goto(f'http://127.0.0.1:5173/?bust=cf2{label}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)

    # seed: 80 卡 + settings.dailyNewTarget=30 + 一个 previous session 模拟 "昨天学了 30"
    page.evaluate(f"""async () => {{
        return new Promise((resolve, reject) => {{
            const req = indexedDB.open('english-book');
            req.onsuccess = () => {{
                const db = req.result;
                const stores = Array.from(db.objectStoreNames);
                const tx = db.transaction(stores, 'readwrite');
                let pending = stores.length;
                if (pending === 0) {{ seed(); return; }}
                for (const s of stores) {{
                    const r = tx.objectStore(s).clear();
                    r.onsuccess = () => {{ if (--pending === 0) seed(); }};
                }}
                function seed() {{
                    const now = Date.now();
                    const yesterday = new Date(now - 86400000);
                    const yKey = yesterday.getFullYear() + '-' + String(yesterday.getMonth()+1).padStart(2,'0') + '-' + String(yesterday.getDate()).padStart(2,'0');
                    const tx2 = db.transaction(['cards','settings','sessions'], 'readwrite');
                    // 80 cards
                    for (let i = 0; i < 80; i++) {{
                        tx2.objectStore('cards').put({{
                            id: 'w'+i, word: 'w'+i, pos: 'n.', cn: String(i), example: '',
                            ef: 2.5, interval: 0, reps: 0,
                            due: now, firstSeen: 0, createdAt: now,
                        }});
                    }}
                    // 30 cards already learned (reps=1)
                    for (let i = 0; i < 30; i++) {{
                        tx2.objectStore('cards').put({{
                            id: 'l'+i, word: 'l'+i, pos: 'n.', cn: 'learned', example: '',
                            ef: 2.5, interval: 1, reps: 1,
                            due: now + 86400000, firstSeen: now - 86400000, createdAt: now - 86400000,
                        }});
                    }}
                    // settings: dailyNewTarget = 30 (昨天设置)
                    tx2.objectStore('settings').put({{
                        key: 'main', dailyNewTarget: {daily_target}, newRatio: 0.5, seededAt: now - 86400000,
                    }});
                    // 昨天 session: newCount=30, completedCount=30
                    tx2.objectStore('sessions').put({{
                        id: yKey, startedAt: now - 86400000, endedAt: now - 80000000,
                        targetCount: 30, completedCount: 30, reviewsCount: 0, newCount: 30,
                        date: yKey,
                    }});
                    tx2.oncomplete = () => resolve();
                }}
            }};
        }});
    }}""")

    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    # Home (应该累计 30 词, 1 天连续, 不是首次)
    page.screenshot(path=os.path.join(OUT, f'{label}-01-home.png'), full_page=True)
    print(f'  [{label}] 01-home')

    # 开始今日 → confirm (应该默认 30 高亮)
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(OUT, f'{label}-02-confirm-reuse.png'), full_page=True)
    print(f'  [{label}] 02-confirm-reuse (default 30)')

    browser.close()


try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        print('=== 首次使用 ===')
        run_first(p, iphone, 'first', daily_target=15)
        print('\n=== 第二天利旧 ===')
        run_day2(p, iphone, 'day2', daily_target=30)

    print(f'\nDone: screenshots in {OUT}')
except Exception:
    traceback.print_exc()
    sys.exit(1)
