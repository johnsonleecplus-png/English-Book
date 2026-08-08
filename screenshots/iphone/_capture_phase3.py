"""Phase 3 verify: 1) 1441 词已 seed, 2) Home 显示 "今日新词 0/15", 3) 跑到 queue 完显示 "再来 N 个新词" 按钮
用法: python -X utf8 _capture_phase3.py
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase3')
os.makedirs(OUT, exist_ok=True)

# 30 测试词 (跟之前一样, 5 MOCK + 10 nouns + 5 verbs + 3 abstract + 2 edge + 5 extra)
TEST_WORDS = [
    # MOCK (5)
    {'word': 'develop',     'cn': '发展',     'pos': 'v.',   'example': 'developing fast'},
    {'word': 'although',    'cn': '虽然',     'pos': 'conj.','example': 'although tired'},
    {'word': 'opportunity', 'cn': '机会',     'pos': 'n.',   'example': 'great opportunity'},
    {'word': 'kindness',    'cn': '善良',     'pos': 'n.',   'example': 'show kindness'},
    {'word': 'achieve',     'cn': '达到',     'pos': 'v.',   'example': 'achieve dream'},
    {'word': 'water',       'cn': '水',       'pos': 'n.',   'example': 'drink water'},
    {'word': 'school',      'cn': '学校',     'pos': 'n.',   'example': 'go to school'},
    {'word': 'friend',      'cn': '朋友',     'pos': 'n.',   'example': 'good friend'},
    {'word': 'book',        'cn': '书',       'pos': 'n.',   'example': 'read a book'},
    {'word': 'family',      'cn': '家庭',     'pos': 'n.',   'example': 'love family'},
    {'word': 'apple',       'cn': '苹果',     'pos': 'n.',   'example': 'eat apple'},
    {'word': 'dog',         'cn': '狗',       'pos': 'n.',   'example': 'pet dog'},
    {'word': 'cat',         'cn': '猫',       'pos': 'n.',   'example': 'feed cat'},
    {'word': 'house',       'cn': '房子',     'pos': 'n.',   'example': 'big house'},
    {'word': 'sun',         'cn': '太阳',     'pos': 'n.',   'example': 'bright sun'},
    {'word': 'eat',         'cn': '吃',       'pos': 'v.',   'example': 'eat food'},
    {'word': 'run',         'cn': '跑',       'pos': 'v.',   'example': 'run fast'},
    {'word': 'read',        'cn': '读',       'pos': 'v.',   'example': 'read book'},
    {'word': 'think',       'cn': '想',       'pos': 'v.',   'example': 'think hard'},
    {'word': 'sing',        'cn': '唱',       'pos': 'v.',   'example': 'sing song'},
    {'word': 'since',       'cn': '自从',     'pos': 'prep.','example': 'since 2020'},
    {'word': 'however',     'cn': '然而',     'pos': 'adv.', 'example': 'however'},
    {'word': 'piano',       'cn': '钢琴',     'pos': 'n.',   'example': 'play piano'},
    {'word': 'butterfly',   'cn': '蝴蝶',     'pos': 'n.',   'example': 'see butterfly'},
    {'word': 'hospital',    'cn': '医院',     'pos': 'n.',   'example': 'at hospital'},
    {'word': 'computer',    'cn': '电脑',     'pos': 'n.',   'example': 'use computer'},
    {'word': 'telephone',   'cn': '电话',     'pos': 'n.',   'example': 'answer phone'},
    {'word': 'umbrella',    'cn': '伞',       'pos': 'n.',   'example': 'open umbrella'},
    {'word': 'mountain',    'cn': '山',       'pos': 'n.',   'example': 'climb mountain'},
    {'word': 'island',      'cn': '岛',       'pos': 'n.',   'example': 'tropical island'},
]

def clear_and_seed(page, words):
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
                        key: 'main', dailyNewTarget: 15, newRatio: 0.5, seededAt: now,
                    }});
                    tx2.oncomplete = () => resolve();
                    tx2.onerror = () => reject(tx2.error);
                }}
            }};
            req.onerror = () => reject(req.error);
        }});
    }}""", TEST_WORDS)


def run(p, iphone, label, max_cards=20):
    browser = p.chromium.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()

    page.goto(f'http://127.0.0.1:5173/?bust=phase3{label}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    clear_and_seed(page, TEST_WORDS)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    # 1) Home 截图
    page.screenshot(path=os.path.join(OUT, f'{label}-01-home.png'), full_page=True)
    print(f'  [{label}] 01-home: {label}-01-home.png')

    page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(1500)

    # 2) 第一张卡 (默认 en2cn mode)
    page.screenshot(path=os.path.join(OUT, f'{label}-02-first-card.png'), full_page=True)
    print(f'  [{label}] 02-first-card')

    # 3) 切 image 模式, 截 1 张
    page.locator('button:has-text("图说")').first.click()
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(OUT, f'{label}-03-image.png'), full_page=True)
    print(f'  [{label}] 03-image')

    # 4) 一直评 good 直到 queue 完 (揭示 → good), 截最后一张
    for i in range(max_cards):
        try:
            # 揭示
            try:
                page.locator('button:has-text("揭示答案")').first.click(timeout=2000)
            except Exception:
                # queue 已完, 跳到 finish 截图
                break
            page.wait_for_timeout(200)
            page.locator('button[title="认识"]').first.click()
            page.wait_for_timeout(800)
        except Exception as e:
            print(f'  [{label}] rate fail at {i+1}: {e}')
            break

    # 5) Queue 完成截图 (显示 "再来 N 个新词" 按钮)
    page.wait_for_timeout(800)
    try:
        page.screenshot(path=os.path.join(OUT, f'{label}-04-queue-done.png'), full_page=True)
        print(f'  [{label}] 04-queue-done')
    except Exception as e:
        print(f'  [{label}] 04 fail: {e}')

    # 6) 点 "再来 10 个新词" 按钮, 截新 queue 第一张
    try:
        page.locator('button:has-text("再学 10 个新词")').first.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUT, f'{label}-05-after-add.png'), full_page=True)
        print(f'  [{label}] 05-after-add-10')
    except Exception as e:
        print(f'  [{label}] 05 fail: {e}')

    # 6.5) 把新加的 10 张全部评掉, 回到 queue-done
    for i in range(15):
        try:
            page.locator('button:has-text("揭示答案")').first.click(timeout=1500)
            page.wait_for_timeout(200)
            page.locator('button[title="认识"]').first.click()
            page.wait_for_timeout(700)
        except Exception:
            break

    # 7) 回首页, 看新词计数
    try:
        page.locator('button:has-text("今日到这")').first.wait_for(timeout=3000)
        page.locator('button:has-text("今日到这")').first.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUT, f'{label}-06-home-after.png'), full_page=True)
        print(f'  [{label}] 06-home-after')
    except Exception as e:
        print(f'  [{label}] 06 fail: {e}')

    browser.close()


try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        run(p, iphone, 'p3')

    print(f'\nDone: screenshots in {OUT}')
except Exception:
    traceback.print_exc()
    sys.exit(1)
