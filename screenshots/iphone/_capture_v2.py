"""v2 布局验证: Home 不含热力图, History 含热力图."""
from playwright.sync_api import sync_playwright
import os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase-v2')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=v2'

with sync_playwright() as p:
    iphone = p.devices['iPhone 14 Pro']
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()

    # 注入历史数据
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

    # 注入 6 天历史
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
                { days: 0, total: 18, good: 14 },
                { days: 1, total: 22, good: 19 },
                { days: 2, total: 15, good: 12 },
                { days: 4, total: 25, good: 20 },
                { days: 6, total: 12, good: 10 },
            ];
            for (const s of samples) {
                const d = new Date(today);
                d.setDate(d.getDate() - s.days);
                const yyyy = d.getFullYear();
                const mm = String(d.getMonth() + 1).padStart(2, '0');
                const dd = String(d.getDate()).padStart(2, '0');
                const dateKey = `${yyyy}-${mm}-${dd}`;
                const startedAt = d.getTime();
                await new Promise(r => {
                    const req = sessionsStore.put({
                        id: dateKey, startedAt,
                        endedAt: startedAt + 900_000,
                        targetCount: 30, completedCount: s.total, reviewsCount: s.total,
                        newCount: Math.floor(s.total / 3), date: dateKey,
                    });
                    req.onsuccess = r;
                });
                for (let g = 0; g < s.good; g++) {
                    await new Promise(r => {
                        const req = reviewsStore.add({ cardId: 'w' + g, sessionId: dateKey, grade: 'good', prevEf: 2.5, prevInterval: 0, prevReps: 0, reviewedAt: startedAt + g * 1000 });
                        req.onsuccess = r;
                    });
                }
            }
            await tx.done;
        }
    """)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2500)

    # 1) Home 不应有 "7 周打卡" 字样
    home_text = page.locator('body').text_content() or ''
    assert '7 周打卡' not in home_text, 'Home 不应含 7 周打卡'
    assert '开始今日' in home_text, 'Home 应有开始今日按钮'
    assert '词库进度' in home_text, 'Home 应有词库进度'
    assert '今日新词' in home_text, 'Home 应有今日新词'
    page.screenshot(path=os.path.join(OUT_DIR, '01-home-no-heatmap.png'), full_page=True)
    print('1/3 ok: Home 不含热力图, 截图保存')

    # 2) 切到历史
    page.locator('nav button:has-text("历史")').first.click()
    page.wait_for_timeout(800)
    hist_text = page.locator('body').text_content() or ''
    assert '7 周打卡' in hist_text, 'History 应含 7 周打卡'
    assert '本周' in hist_text, 'History 应含本周汇总'
    page.screenshot(path=os.path.join(OUT_DIR, '02-history-with-heatmap.png'), full_page=True)
    print('2/3 ok: History 含热力图, 截图保存')

    # 3) 设置页也应不再有导出/导入
    page.locator('nav button:has-text("设置")').first.click()
    page.wait_for_timeout(800)
    set_text = page.locator('body').text_content() or ''
    assert '导出' not in set_text, '设置页不应有导出'
    assert '导入' not in set_text, '设置页不应有导入'
    assert '每日新词目标' in set_text, '设置页应有每日新词目标'
    page.screenshot(path=os.path.join(OUT_DIR, '03-settings-clean.png'), full_page=True)
    print('3/3 ok: Settings 不含备份, 截图保存')

    browser.close()
    print(f'\n✅ v2 布局验证全过')
    print(f'截图: {OUT_DIR}')
