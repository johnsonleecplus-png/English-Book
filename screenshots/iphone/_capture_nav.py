"""导航改造: 3 tab (今日/历史/设置) 截图 + 切换验证."""
from playwright.sync_api import sync_playwright
import os, sys, traceback, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase-nav')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=nav'

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone)
        page = context.new_page()

        # 0) clear IDB + reload
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
        page.wait_for_timeout(3000)

        # 1) 注入一些 sessions 历史数据
        page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                const tx = db.transaction(['sessions', 'reviews'], 'readwrite');
                const sessionsStore = tx.objectStore('sessions');
                const reviewsStore = tx.objectStore('reviews');
                const today = new Date();
                const samples = [
                    { days: 0, total: 18, good: 14, hard: 3, again: 1 },
                    { days: 1, total: 22, good: 19, hard: 2, again: 1 },
                    { days: 2, total: 15, good: 12, hard: 2, again: 1 },
                    { days: 3, total: 20, good: 16, hard: 3, again: 1 },
                    { days: 5, total: 25, good: 20, hard: 3, again: 2 },
                    { days: 8, total: 12, good: 10, hard: 1, again: 1 },
                ];
                for (let i = 0; i < samples.length; i++) {
                    const s = samples[i];
                    const d = new Date(today);
                    d.setDate(d.getDate() - s.days);
                    const yyyy = d.getFullYear();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const dd = String(d.getDate()).padStart(2, '0');
                    const dateKey = `${yyyy}-${mm}-${dd}`;
                    const sessionId = dateKey;
                    const startedAt = d.getTime();
                    const newCount = Math.floor(s.total / 3);
                    await new Promise(r => {
                        const req = sessionsStore.put({
                            id: sessionId,
                            startedAt,
                            endedAt: startedAt + 900_000,
                            targetCount: 30,
                            completedCount: s.total,
                            reviewsCount: s.total,
                            newCount,
                            date: dateKey,
                        });
                        req.onsuccess = r;
                    });
                    // reviews
                    for (let g = 0; g < s.good; g++) {
                        await new Promise(r => {
                            const req = reviewsStore.add({ cardId: 'word' + g, sessionId, grade: 'good', prevEf: 2.5, prevInterval: 0, prevReps: 0, reviewedAt: startedAt + g * 1000 });
                            req.onsuccess = r;
                        });
                    }
                    for (let g = 0; g < s.hard; g++) {
                        await new Promise(r => {
                            const req = reviewsStore.add({ cardId: 'word' + (s.good + g), sessionId, grade: 'hard', prevEf: 2.5, prevInterval: 0, prevReps: 0, reviewedAt: startedAt + (s.good + g) * 1000 });
                            req.onsuccess = r;
                        });
                    }
                    for (let g = 0; g < s.again; g++) {
                        await new Promise(r => {
                            const req = reviewsStore.add({ cardId: 'word' + (s.good + s.hard + g), sessionId, grade: 'again', prevEf: 2.5, prevInterval: 0, prevReps: 0, reviewedAt: startedAt + (s.good + s.hard + g) * 1000 });
                            req.onsuccess = r;
                        });
                    }
                }
                await tx.done;
            }
        """)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2500)

        # 2) 验证 tab bar 存在 + 3 个 icon
        tab_check = page.evaluate("""
            () => {
                const nav = document.querySelector('nav');
                if (!nav) return { hasTabBar: false };
                const buttons = Array.from(nav.querySelectorAll('button'));
                return {
                    hasTabBar: true,
                    tabs: buttons.map(b => ({
                        label: b.textContent?.trim().split(/\\s+/).pop() || '',
                        hasIcon: !!b.querySelector('svg'),
                    })),
                };
            }
        """)
        print(f'1/6 tab bar 检查: {tab_check}')
        assert tab_check['hasTabBar']
        assert len(tab_check['tabs']) == 3
        for t in tab_check['tabs']:
            assert t['hasIcon'], f"tab 缺 icon: {t['label']}"

        # 截图 Home
        page.screenshot(path=os.path.join(OUT_DIR, '01-tab-home.png'), full_page=True)
        print('2/6 ok: 01-tab-home.png')

        # 3) 切到历史 tab
        page.locator('nav button:has-text("历史")').first.click()
        page.wait_for_timeout(800)
        # 验证页面有"本周"和 session 列表
        hist_text = page.locator('body').text_content() or ''
        hist_check = {
            '历史标题': '历史' in hist_text,
            '本周': '本周' in hist_text,
            '今天': '今天' in hist_text,
        }
        print(f'3/6 历史 tab 检查: {hist_check}')
        for k, v in hist_check.items():
            assert v, f'历史页缺: {k}'
        page.screenshot(path=os.path.join(OUT_DIR, '02-tab-history.png'), full_page=True)
        print('3/6 ok: 02-tab-history.png')

        # 4) 切到设置 tab
        page.locator('nav button:has-text("设置")').first.click()
        page.wait_for_timeout(800)
        set_text = page.locator('body').text_content() or ''
        set_check = {
            '设置标题': '设置' in set_text,
            '每日新词目标': '每日新词目标' in set_text,
            '导出': '导出' in set_text and 'JSON' in set_text,
            '导入': '导入' in set_text and 'JSON' in set_text,
        }
        print(f'4/6 设置 tab 检查: {set_check}')
        for k, v in set_check.items():
            assert v, f'设置页缺: {k}'
        page.screenshot(path=os.path.join(OUT_DIR, '03-tab-settings.png'), full_page=True)
        print('4/6 ok: 03-tab-settings.png')

        # 5) 切回今日 tab
        page.locator('nav button:has-text("今日")').first.click()
        page.wait_for_timeout(500)
        # 验证 tab bar 还在, 没被覆盖
        assert page.locator('nav').count() == 1
        # 验证今天内容
        home_text = page.locator('body').text_content() or ''
        assert '开始今日' in home_text or '继续上次的 session' in home_text
        print('5/6 ok: 切回今日成功')

        # 6) 进 confirm 屏 → tab bar 应消失 + 应有 [← 返回] 按钮
        page.locator('button:has-text("开始今日")').first.click()
        page.wait_for_timeout(800)
        confirm_check = page.evaluate("""
            () => {
                return {
                    hasNav: !!document.querySelector('nav'),
                    hasBackBtn: !!document.querySelector('button:has(svg)'),
                    bodyHas返回: document.body.textContent.includes('返回'),
                };
            }
        """)
        print(f'6/6 confirm 屏检查: {confirm_check}')
        # tab bar 应消失 (我们没在 confirm 屏渲染)
        assert not confirm_check['hasNav'], 'confirm 屏不应有 tab bar'
        assert confirm_check['bodyHas返回'], 'confirm 屏应有"返回"按钮'
        page.screenshot(path=os.path.join(OUT_DIR, '04-confirm-with-back.png'), full_page=True)
        print('6/6 ok: 04-confirm-with-back.png (confirm 屏隐藏 tab bar + 有返回按钮)')

        # 额外: 验证返回按钮能正常工作
        page.locator('button:has-text("返回")').first.click()
        page.wait_for_timeout(500)
        # 应回到 home, tab bar 又出现
        assert page.locator('nav').count() == 1, '返回后 tab bar 应恢复'
        print('  ✓ 返回按钮: tab bar 恢复')

        browser.close()
        print(f'\n✅ 导航改造全过')
        print(f'截图: {OUT_DIR}')
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
