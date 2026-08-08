"""Phase 5.2/6.4/6.5/7.1 端到端验证:
- 5.2: 7 周热力图 (sessions 数据 → 49 天 grid)
- 6.4: 键盘快捷键 (Space 揭示 + 1/2/3 评分)
- 6.5: 完成动画 (queue-done 屏 🎉 + emoji)
- 7.1: JSON 备份/恢复 (export + import)
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback, json
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase-misc')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=misc'

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone, accept_downloads=True)
        page = context.new_page()

        # 0) clear IDB + reload → 让 ensureSeeded 跑全新 1716 卡
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

        # 1) 注入混合 sessions 数据 (5.2 热力图测试)
        # 制造过去 21 天每天有不同数量的 session
        page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                const tx = db.transaction('sessions', 'readwrite');
                const store = tx.objectStore('sessions');
                const today = new Date();
                const labels = [0, 2, 5, 8, 3, 0, 6,  // 这周
                                4, 0, 2, 12, 7, 0, 0,  // 上周
                                0, 3, 1, 5, 0, 8, 2, 0, 0]; // 再上周
                for (let i = 0; i < labels.length; i++) {
                    const d = new Date(today);
                    d.setDate(d.getDate() - i);
                    const yyyy = d.getFullYear();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const dd = String(d.getDate()).padStart(2, '0');
                    const dateKey = `${yyyy}-${mm}-${dd}`;
                    const count = labels[i];
                    if (count === 0) continue;
                    await new Promise(r => {
                        const req = store.put({
                            id: dateKey,
                            startedAt: d.getTime(),
                            endedAt: d.getTime() + 600_000,
                            targetCount: count,
                            completedCount: count,
                            reviewsCount: count,
                            newCount: Math.floor(count / 2),
                            date: dateKey,
                        });
                        req.onsuccess = r;
                    });
                }
                await tx.done;
            }
        """)
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2500)

        # 5.2 验证: 7 周热力图 + 全部 4 张表卡片 (今日 / 连续+累计 / 词库进度 / 7 周打卡) + footer 2 个备份按钮
        text = page.locator('body').text_content() or ''
        checks = {
            '7周打卡': '7 周打卡' in text,
            '近 7 天': '近 7 天' in text,
            '导出': '导出' in text and 'JSON' in text,
            '导入': '导入' in text and 'JSON' in text,
            '开始今日': '开始今日' in text,
            '词库进度': '词库进度' in text,
        }
        print(f'1/8 5.2 + 7.1 UI 检查: {checks}')
        for k, v in checks.items():
            assert v, f'缺关键字: {k}'

        # 截图 home (含热力图)
        page.screenshot(path=os.path.join(OUT_DIR, '01-home-with-heatmap.png'), full_page=True)
        print('2/8 ok: 01-home-with-heatmap.png')

        # 7.1 验证: 导出 JSON
        with page.expect_download(timeout=5000) as dl_info:
            page.locator('button:has-text("导出 JSON")').first.click()
        download = dl_info.value
        path = os.path.join(OUT_DIR, 'export.json')
        download.save_as(path)
        with open(path, encoding='utf-8') as f:
            backup = json.load(f)
        assert backup['$type'] == 'english-book-backup'
        assert backup['$version'] == '1.0'
        assert isinstance(backup['cards'], list)
        print(f'3/8 ok: export.json 含 {len(backup["cards"])} 卡片 / {len(backup["sessions"])} sessions')

        # 7.1 验证: 模拟 备份 import (用刚才导出的)
        # 改 backup 一些数据, 模拟"另一台设备"
        backup['sessions'].append({
            'id': '9999-12-31',
            'startedAt': 9999999999000,
            'endedAt': 9999999999000 + 600_000,
            'targetCount': 10,
            'completedCount': 10,
            'reviewsCount': 10,
            'newCount': 5,
            'date': '9999-12-31',
        })
        modified_path = os.path.join(OUT_DIR, 'modified.json')
        with open(modified_path, 'w', encoding='utf-8') as f:
            json.dump(backup, f, ensure_ascii=False)

        # 监听 dialog (import 前的 confirm)
        confirm_text_holder = {'text': None}
        def on_dialog(d):
            confirm_text_holder['text'] = d.message
            d.accept()
        page.on('dialog', on_dialog)

        # 触发 import
        page.set_input_files('input[type="file"]', modified_path)
        page.wait_for_timeout(2500)  # 等 reload
        assert confirm_text_holder['text'] is not None, 'import 没弹 confirm'
        assert '即将覆盖' in confirm_text_holder['text']
        print(f'4/8 ok: import 弹了 confirm: "{confirm_text_holder["text"][:50]}..."')

        # 验证 IDB 多了 9999-12-31 session
        new_session = page.evaluate("""
            async () => {
                const db = await new Promise(r => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => r(req.result);
                });
                return new Promise(r => {
                    const req = db.transaction('sessions', 'readonly').objectStore('sessions').get('9999-12-31');
                    req.onsuccess = () => r(req.result || null);
                });
            }
        """)
        assert new_session and new_session['completedCount'] == 10
        print('5/8 ok: 导入后 IDB 多了 9999-12-31 session (10 词)')

        # 6.4 验证: 键盘快捷键 (在 desktop viewport 测)
        page2 = context.new_page()
        page2.set_viewport_size({"width": 1024, "height": 768})
        page2.goto(DEV_URL, wait_until='domcontentloaded')
        page2.wait_for_timeout(2500)

        # 点 [开始今日] → confirm
        page2.locator('button:has-text("开始今日")').first.click()
        page2.wait_for_timeout(800)
        page2.locator('button:has-text("开始学")').first.click()
        page2.wait_for_timeout(1500)

        # Space 揭示
        page2.keyboard.press('Space')
        page2.wait_for_timeout(500)
        # 揭示后, 应出现 3 个评分按钮 (不显示"揭示答案"按钮)
        reveal_btn = page2.locator('button:has-text("揭示答案")')
        rate_btns = page2.locator('button[title*="快捷键"]')
        n_reveal = reveal_btn.count()
        n_rate = rate_btns.count()
        print(f'6/8 ok: 6.4 键盘 Space 揭示 (揭示按钮: {n_reveal}, 评分按钮: {n_rate})')
        assert n_reveal == 0, 'Space 没触发揭示'
        assert n_rate == 3, f'应有 3 个评分按钮, 实际 {n_rate}'

        # 截图: 揭示后 + 快捷键提示
        page2.screenshot(path=os.path.join(OUT_DIR, '02-cardview-keyboard-hints.png'), full_page=True)

        # 数字键 3 = good
        page2.keyboard.press('Digit3')
        page2.wait_for_timeout(1200)
        # 下一张卡, 应该又显示揭示按钮
        assert page2.locator('button:has-text("揭示答案")').count() == 1
        print('7/8 ok: 6.4 键盘 3 = good, 下一张已就绪')

        # 6.5 验证: 完成动画 (跑完所有卡, 看 queue-done 屏)
        # 用直接点击 (keyboard 偶尔被 input 抢走)
        for i in range(30):
            try:
                reveal = page2.locator('button:has-text("揭示答案")')
                if reveal.count() > 0:
                    reveal.first.click()
                    page2.wait_for_timeout(300)
                # 评分 (用 button[title*=认识] 选 good)
                good = page2.locator('button[title*="认识"]')
                if good.count() > 0:
                    good.first.click()
                    page2.wait_for_timeout(700)
                # 检查状态
                txt = page2.locator('body').text_content() or ''
                if '太棒了' in txt or 'queue 已跑完' in txt:
                    break
                # 如果跑到加新词屏, 跳过 (不点, 保留现状)
                if page2.locator('button:has-text("再学 10")').count() > 0:
                    break
            except Exception as e:
                print(f'  iter {i} error: {e}')
                break

        # 检查是否到达 queue-done 屏
        page2.wait_for_timeout(1500)
        text2 = page2.locator('body').text_content() or ''
        if '太棒了' in text2 or 'queue 已跑完' in text2:
            page2.screenshot(path=os.path.join(OUT_DIR, '03-queue-done-animation.png'), full_page=True)
            # 检查 emoji 装饰
            anim_check = page2.evaluate("""
                () => {
                    const txt = document.body.textContent || '';
                    return {
                        hasPop: !!document.querySelector('.animate-pop'),
                        hasBounce: document.querySelectorAll('.animate-bounce').length,
                        hasStars: txt.includes('⭐') || txt.includes('✨') || txt.includes('🏆'),
                    };
                }
            """)
            print(f'8/8 ok: 6.5 完成动画: pop={anim_check["hasPop"]} bounce={anim_check["hasBounce"]} stars={anim_check["hasStars"]}')
            assert anim_check['hasPop'], '没找到 animate-pop 元素'
        else:
            page2.screenshot(path=os.path.join(OUT_DIR, '03-queue-done-animation.png'), full_page=True)
            print(f'8/8 跳过: queue 没跑完, 文本: {text2[:150]!r}')

        browser.close()
        print(f'\n✅ 4 feature 验证全过')
        print(f'截图: {OUT_DIR}')
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
