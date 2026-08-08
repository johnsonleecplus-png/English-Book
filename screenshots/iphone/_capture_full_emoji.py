"""完整 emoji 模式验收: seed 25 个不同类型词 (concrete/abstract/null), 截彩色+灰阶
用法: python -X utf8 _capture_full_emoji.py
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emoji-full')
os.makedirs(OUT, exist_ok=True)

# 25 个测试词, 覆盖 concrete/abstract/null/edge cases
TEST_WORDS = [
    # MOCK (5)
    {'word': 'develop',     'cn': '发展',           'pos': 'v.',   'example': 'developing fast'},
    {'word': 'although',    'cn': '虽然',           'pos': 'conj.','example': 'although tired'},
    {'word': 'opportunity', 'cn': '机会',           'pos': 'n.',   'example': 'great opportunity'},
    {'word': 'kindness',    'cn': '善良',           'pos': 'n.',   'example': 'show kindness'},
    {'word': 'achieve',     'cn': '达到',           'pos': 'v.',   'example': 'achieve dream'},
    # 高频具体名词 (10)
    {'word': 'water',       'cn': '水',             'pos': 'n.',   'example': 'drink water'},
    {'word': 'school',      'cn': '学校',           'pos': 'n.',   'example': 'go to school'},
    {'word': 'friend',      'cn': '朋友',           'pos': 'n.',   'example': 'good friend'},
    {'word': 'book',        'cn': '书',             'pos': 'n.',   'example': 'read a book'},
    {'word': 'family',      'cn': '家庭',           'pos': 'n.',   'example': 'love family'},
    {'word': 'apple',       'cn': '苹果',           'pos': 'n.',   'example': 'eat apple'},
    {'word': 'dog',         'cn': '狗',             'pos': 'n.',   'example': 'pet dog'},
    {'word': 'cat',         'cn': '猫',             'pos': 'n.',   'example': 'feed cat'},
    {'word': 'house',       'cn': '房子',           'pos': 'n.',   'example': 'big house'},
    {'word': 'sun',         'cn': '太阳',           'pos': 'n.',   'example': 'bright sun'},
    # 高频具体动词 (5)
    {'word': 'eat',         'cn': '吃',             'pos': 'v.',   'example': 'eat food'},
    {'word': 'run',         'cn': '跑',             'pos': 'v.',   'example': 'run fast'},
    {'word': 'read',        'cn': '读',             'pos': 'v.',   'example': 'read book'},
    {'word': 'think',       'cn': '想',             'pos': 'v.',   'example': 'think hard'},
    {'word': 'sing',        'cn': '唱',             'pos': 'v.',   'example': 'sing song'},
    # 抽象词 (3) — emoji 可能 null
    {'word': 'although',    'cn': '虽然',           'pos': 'conj.','example': 'although'},
    {'word': 'since',       'cn': '自从',           'pos': 'prep.','example': 'since 2020'},
    {'word': 'however',     'cn': '然而',           'pos': 'adv.', 'example': 'however'},
    # 各种边界 (2)
    {'word': 'piano',       'cn': '钢琴',           'pos': 'n.',   'example': 'play piano'},
    {'word': 'butterfly',   'cn': '蝴蝶',           'pos': 'n.',   'example': 'see butterfly'},
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
                        key: 'main', dailyTarget: 30, newRatio: 0.5, seededAt: now,
                    }});
                    tx2.oncomplete = () => resolve();
                    tx2.onerror = () => reject(tx2.error);
                }}
            }};
            req.onerror = () => reject(req.error);
        }});
    }}""", TEST_WORDS)


def run_one(p, iphone, label, url_suffix, max_cards=10):
    browser = p.chromium.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()

    page.goto(f'http://127.0.0.1:5173/?{url_suffix}', wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    clear_and_seed(page, TEST_WORDS)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    page.locator('button:has-text("开始今日")').first.wait_for(timeout=3000)
    page.locator('button:has-text("开始今日")').first.click()
    page.wait_for_timeout(1500)

    # 切到图说模式
    page.locator('button:has-text("图说")').first.click()
    page.wait_for_timeout(500)

    captured = 0
    for i in range(max_cards):
        try:
            # 等当前卡片稳定
            page.wait_for_timeout(400)
            n = i + 1
            fname = f'{label}-{n:02d}.png'
            page.screenshot(path=os.path.join(OUT, fname), full_page=True)
            print(f'  [{label} {n}/{max_cards}] {fname}')
            captured += 1

            # 揭示 + 评分
            page.locator('button:has-text("揭示答案")').first.click(timeout=2000)
            page.wait_for_timeout(300)
            page.locator('button[title="认识"]').first.click()
            page.wait_for_timeout(800)
        except Exception as e:
            print(f'  [{label}] stop at {i+1}: {e}')
            break

    browser.close()
    return captured


try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        print('=== 彩色版 (默认) ===')
        n_color = run_one(p, iphone, 'color', 'bust=fullcolor')
        print(f'\n=== 灰阶版 (?grayscale=1) ===')
        n_gray = run_one(p, iphone, 'gray', 'bust=fullgray&grayscale=1')

    print(f'\nDone: {n_color + n_gray} screenshots in {OUT}')
except Exception:
    traceback.print_exc()
    sys.exit(1)
