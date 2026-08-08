"""Phase 5.1 verify: 词库进度 4 档分类 + 剩余天数.

两种场景:
- A. 全新用户 (5 MOCK + 1711 vocab 全未学)
- B. 模拟混合状态 (一些 mastered/fuzzy/struggling)
"""
from playwright.sync_api import sync_playwright
import os, json, traceback, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase51')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=phase51'

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone)
        page = context.new_page()

        # 场景 A: 全新用户
        page.goto(DEV_URL, wait_until='domcontentloaded')
        page.wait_for_timeout(1500)
        page.evaluate("""
            () => new Promise((resolve) => {
                const req = indexedDB.deleteDatabase('english-book');
                req.onsuccess = () => resolve();
                req.onerror = () => resolve();
                req.onblocked = () => resolve();
            })
        """)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(3000)  # 等 seed 跑完

        page.screenshot(path=os.path.join(OUT_DIR, '01-home-fresh.png'), full_page=True)
        print('A/3 ok: 01-home-fresh.png (全新用户, 1716 全未学)')

        # 验证 IDB 状态
        result = page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                const all = await new Promise(r => {
                    const req = db.transaction('cards', 'readonly').objectStore('cards').getAll();
                    req.onsuccess = () => r(req.result);
                });
                const unlearned = all.filter(c => c.firstSeen === 0).length;
                const mastered = all.filter(c => c.firstSeen > 0 && c.reps >= 3 && c.ef >= 2.5).length;
                const fuzzy = all.filter(c => c.firstSeen > 0 && c.reps >= 3 && c.ef >= 2.0 && c.ef < 2.5).length;
                const struggling = all.filter(c => c.firstSeen > 0 && (c.reps < 3 || c.ef < 2.0)).length;
                return { total: all.length, unlearned, mastered, fuzzy, struggling };
            }
        """)
        print(f'  IDB 状态: total={result["total"]}, unlearned={result["unlearned"]}, mastered={result["mastered"]}, fuzzy={result["fuzzy"]}, struggling={result["struggling"]}')

        # 场景 B: 模拟混合状态 — 改一些卡片的 reps/ef
        page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                const tx = db.transaction('cards', 'readwrite');
                const store = tx.objectStore('cards');
                let n_master = 0, n_fuzzy = 0, n_strugg = 0;
                await new Promise(r => {
                    const req = store.openCursor();
                    req.onsuccess = (e) => {
                        const c = e.target.result;
                        if (c) {
                            const card = c.value;
                            if (card.firstSeen === 0) {
                                // 前 30 张 → 掌握 (ef=2.6, reps=4, interval=30)
                                if (n_master < 30) {
                                    card.firstSeen = Date.now() - 30*86400_000;
                                    card.ef = 2.6;
                                    card.reps = 4;
                                    card.interval = 30;
                                    c.update(card);
                                    n_master++;
                                } else if (n_fuzzy < 50) {
                                    // 接 50 张 → 模糊
                                    card.firstSeen = Date.now() - 14*86400_000;
                                    card.ef = 2.2;
                                    card.reps = 3;
                                    card.interval = 14;
                                    c.update(card);
                                    n_fuzzy++;
                                } else if (n_strugg < 20) {
                                    // 接 20 张 → 不会
                                    card.firstSeen = Date.now() - 3*86400_000;
                                    card.ef = 1.8;
                                    card.reps = 1;
                                    card.interval = 1;
                                    c.update(card);
                                    n_strugg++;
                                }
                            }
                            c.continue();
                        } else {
                            r();
                        }
                    };
                });
                await tx.done;
                return { n_master, n_fuzzy, n_strugg };
            }
        """)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUT_DIR, '02-home-mixed.png'), full_page=True)
        print('B/3 ok: 02-home-mixed.png (混合: 30 掌握 + 50 模糊 + 20 不会 + 余下未学)')

        # 验证页面文字
        text = page.locator('body').text_content() or ''
        checks = {
            '掌握': '掌握' in text,
            '模糊': '模糊' in text,
            '不会': '不会' in text,
            '未学': '未学' in text,
            '剩余天数': '天' in text and ('剩余' in text or '还剩' in text),
        }
        print(f'  页面文字检查: {checks}')
        for k, v in checks.items():
            assert v, f'页面缺关键字: {k}'

        # 场景 C: 全部学完
        page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                const tx = db.transaction('cards', 'readwrite');
                const store = tx.objectStore('cards');
                await new Promise(r => {
                    const req = store.openCursor();
                    req.onsuccess = (e) => {
                        const c = e.target.result;
                        if (c) {
                            const card = c.value;
                            card.firstSeen = Date.now() - 30*86400_000;
                            card.ef = 2.6;
                            card.reps = 4;
                            card.interval = 30;
                            c.update(card);
                            c.continue();
                        } else {
                            r();
                        }
                    };
                });
                await tx.done;
            }
        """)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUT_DIR, '03-home-all-mastered.png'), full_page=True)
        print('C/3 ok: 03-home-all-mastered.png (全部掌握)')

        browser.close()
        print(f'\nDone: 3 截图保存到 {OUT_DIR}')

except Exception as e:
    traceback.print_exc()
    sys.exit(1)
