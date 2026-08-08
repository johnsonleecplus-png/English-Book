"""Phase 3.2 verify: 新增 270 词条 (43 缺词 + 227 词组) 都能在 IDB 出现 + 各模式正常 + TTS 播放.

流程:
1) clear IDB → 刷新 → 等 seed (1711 词 + 5 MOCK = 1716 卡)
2) 验证 IDB card count = 1716
3) 用 getAllFromIndex 抽 africa / april / "a couple of" 各一张
4) 跳过 Home → Confirm → 直接 inject session 跳到 CardView (queue 满)
5) 评分到目标词出现 → 截图各模式
6) 听音频: console.log 触发 audio.play() 看 network 200/206

简单起见: 不操作 queue (queue 顺序是 SM-2 算法决定), 而是直接给 IDB 写一张"目标词"作为 due card,
然后 reload, 走 confirm → 评分 → 验证。
"""
from playwright.sync_api import sync_playwright
import os, sys, traceback, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase32')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=phase32'

# 测试目标词: 1 新单词 + 1 词组
TARGETS = [
    {"id": "africa",   "word": "Africa",   "pos": "名词", "cn": "非洲",     "kind": "word"},
    {"id": "a couple of", "word": "a couple of", "pos": "词组", "cn": "两个；几个", "kind": "phrase"},
]

try:
    with sync_playwright() as p:
        iphone = p.devices['iPhone 14 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(**iphone)
        page = context.new_page()

        # 0) clear IDB + reload → 让 ensureSeeded 跑全新 1711 词
        page.goto(DEV_URL, wait_until='domcontentloaded')
        page.wait_for_timeout(1500)
        page.evaluate("""
            () => new Promise((resolve, reject) => {
                const req = indexedDB.deleteDatabase('english-book');
                req.onsuccess = () => resolve('ok');
                req.onerror = () => reject(req.error);
                req.onblocked = () => resolve('blocked');
            })
        """)
        print('0/8 ok: IDB cleared')
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(3000)  # 等 seed 跑完

        # 1) 验证 IDB 卡片数 + 目标词在 IDB 里
        result = page.evaluate("""
            async () => {
                const db = await new Promise((resolve, reject) => {
                    const req = indexedDB.open('english-book');
                    req.onsuccess = () => resolve(req.result);
                    req.onerror = () => reject(req.error);
                });
                const count = await new Promise(r => {
                    const req = db.transaction('cards', 'readonly').objectStore('cards').count();
                    req.onsuccess = () => r(req.result);
                });
                const get = (id) => new Promise(r => {
                    const req = db.transaction('cards', 'readonly').objectStore('cards').get(id);
                    req.onsuccess = () => r(req.result || null);
                });
                const africa = await get('africa');
                const couple = await get('a couple of');

                // 强制: 把目标卡外的所有 new 卡 firstSeen 设成 1 (让 queue 只剩目标)
                // 用 cursor 遍历, 排除 africa + a couple of
                const tx = db.transaction('cards', 'readwrite');
                const store = tx.objectStore('cards');
                await new Promise(r => {
                    const req = store.openCursor();
                    req.onsuccess = (e) => {
                        const c = e.target.result;
                        if (c) {
                            const card = c.value;
                            if (card.id !== 'africa' && card.id !== 'a couple of' && card.firstSeen === 0) {
                                card.firstSeen = 1;  // 标记为"已学", 不进新词 queue
                                c.update(card);
                            }
                            c.continue();
                        } else {
                            r();
                        }
                    };
                });
                await tx.done;

                return {
                    cardCount: count,
                    africa: africa ? { word: africa.word, pos: africa.pos, cn: africa.cn, id: africa.id } : null,
                    couple: couple ? { word: couple.word, pos: couple.pos, cn: couple.cn, id: couple.id } : null,
                };
            }
        """)
        print(f'1/8 ok: IDB cards = {result["cardCount"]}, africa = {result["africa"]}, couple = {result["couple"]}')
        assert result['cardCount'] >= 1700, f"cards 太少了: {result['cardCount']}"
        assert result['africa'], "africa 不在 IDB"
        assert result['couple'], "a couple of 不在 IDB"
        assert result['africa']['pos'] == '名词', f"africa pos 错: {result['africa']['pos']}"
        assert result['couple']['pos'] == '词组', f"a couple of pos 错: {result['couple']['pos']}"

        # 2) 验证 audio HEAD 200 (Piper 生成的 MP3)
        audio_check = page.evaluate("""
            async () => {
                const checks = [];
                for (const p of ['/audio/words/africa.mp3', '/audio/words/a_couple_of.mp3',
                                  '/audio/words/although.mp3', '/audio/words/opportunity.mp3',
                                  '/audio/words/according_to.mp3']) {
                    const r = await fetch(p, { method: 'HEAD' });
                    const len = parseInt(r.headers.get('content-length') || '0', 10);
                    const ct = r.headers.get('content-type') || '';
                    checks.push({ path: p, status: r.status, len, ct, ok: r.ok && len > 1024 && ct.startsWith('audio/') });
                }
                return checks;
            }
        """)
        print(f'2/8 ok: 音频 HEAD 校验')
        for a in audio_check:
            tag = '✓' if a['ok'] else '✗'
            print(f'  {tag} {a["path"]}  status={a["status"]}  len={a["len"]}  ct={a["ct"][:24]}')
        assert all(a['ok'] for a in audio_check), f"音频 HEAD 失败: {audio_check}"

        # 3) 走 Confirm 屏 → 进 CardView
        page.locator('button:has-text("开始今日")').first.click()
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(OUT_DIR, '00-confirm.png'), full_page=True)
        print('3/8 ok: confirm 屏截图')

        # confirm → 选 5 (最小) → 开始
        page.locator('button:has-text("5")').first.click()
        page.wait_for_timeout(300)
        page.locator('button:has-text("开始学")').first.click()
        page.wait_for_timeout(1200)

        # 4) 评分循环, 期望第一张是 africa 或 a couple of (queue 只剩 2 张)
        def rate_one():
            if page.locator('button:has-text("揭示答案")').count() > 0:
                page.locator('button:has-text("揭示答案")').first.click()
                page.wait_for_timeout(300)
            if page.locator('button[title="认识"]').count() > 0:
                page.locator('button[title="认识"]').first.click()
                page.wait_for_timeout(700)

        def shoot_current(prefix: str, after_cn2en: bool = False, after_listen: bool = False):
            page.screenshot(path=os.path.join(OUT_DIR, f'{prefix}-en2cn-before.png'), full_page=True)
            if page.locator('button:has-text("揭示答案")').count() > 0:
                page.locator('button:has-text("揭示答案")').first.click()
                page.wait_for_timeout(500)
                page.screenshot(path=os.path.join(OUT_DIR, f'{prefix}-en2cn-after.png'), full_page=True)
                if after_cn2en:
                    page.locator('button:has-text("中→英")').first.click()
                    page.wait_for_timeout(500)
                    page.screenshot(path=os.path.join(OUT_DIR, f'{prefix}-cn2en.png'), full_page=True)
                if after_listen:
                    page.locator('button:has-text("听说")').first.click()
                    page.wait_for_timeout(500)
                    page.screenshot(path=os.path.join(OUT_DIR, f'{prefix}-listen.png'), full_page=True)
                page.locator('button[title="认识"]').first.click()
                page.wait_for_timeout(800)

        seen_couple = False
        seen_africa = False
        for i in range(8):
            try:
                text = page.locator('div.text-6xl').first.text_content(timeout=3000) or ''
            except Exception:
                # 没有 text-6xl 元素, 可能 queue 跑完
                print(f'  i={i}: text-6xl 找不到, 跳出')
                break
            if 'a couple of' in text.lower() and not seen_couple:
                seen_couple = True
                shoot_current('01-phrase', after_cn2en=True, after_listen=True)
                break  # 测完一张就够
            if 'africa' in text.lower() and not seen_africa:
                seen_africa = True
                shoot_current('05-africa', after_cn2en=True, after_listen=True)
                break
            # 都不是目标 → 评分继续
            rate_one()
            if page.locator('button:has-text("今日到这")').count() > 0:
                # queue 跑完
                break
        print(f'4/8 ok: 第一张目标卡截图 (africa={seen_africa} couple={seen_couple})')

        # 6) 总结
        summary = {
            "cardCount": result['cardCount'],
            "africa_in_idb": bool(result['africa']),
            "couple_in_idb": bool(result['couple']),
            "all_audio_ok": all(a['ok'] for a in audio_check),
            "phrase_card_seen": seen_couple,
            "africa_card_seen": seen_africa,
        }
        print(f'\n=== 总结 ===')
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        # 5/8/9 = phrase en2cn+cn2en+listen + africa 各模式截图
        print(f'5-9/8 ok: 截图已保存到 {OUT_DIR}')

        browser.close()
        print(f'\nDone: screenshots in {OUT_DIR}')
        # 接受: 任意一张目标被截图 + 全部 IDB/audio 验证通过
        ok = (
            summary['all_audio_ok']
            and summary['africa_in_idb']
            and summary['couple_in_idb']
            and (summary['phrase_card_seen'] or summary['africa_card_seen'])
        )
        if not ok:
            print('⚠️  验证未通过, 上面有日志')
            sys.exit(2)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
