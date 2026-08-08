"""Phase 4 离线验证: 加载完页面后断网, 应仍能访问 + 播放 audio."""
from playwright.sync_api import sync_playwright
import os, sys, traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase4')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:4173/?bust=phase4offline'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        # 1) 在线加载 + 触发 SW 缓存
        page.goto(DEV_URL, wait_until='domcontentloaded')
        page.wait_for_timeout(2500)
        # 主动 fetch 几个文件让 SW 缓存
        page.evaluate("""
            async () => {
                // 预热 audio
                await fetch('/audio/words/africa.mp3');
                await fetch('/audio/words/a_couple_of.mp3');
            }
        """)
        # 等 SW 缓存生效
        page.wait_for_timeout(1500)
        # 等到激活
        page.evaluate("""
            async () => {
                const reg = await navigator.serviceWorker.ready;
                return reg.active?.state;
            }
        """)

        # 2) 断网
        context.set_offline(True)
        print('1/4 ok: 已断网 (context.set_offline(True))')

        # 3) 重新加载页面 → 应仍能加载 (SW 接管)
        try:
            page.reload(wait_until='domcontentloaded', timeout=10000)
            page.wait_for_timeout(1500)
            text = page.locator('body').text_content() or ''
            ok = 'English Book' in text or '今日' in text or '加载中' in text
            print(f'2/4 ok: 离线 reload 成功 (页面有内容: {ok})')
            page.screenshot(path=os.path.join(OUT_DIR, '02-offline-home.png'), full_page=True)
        except Exception as e:
            print(f'2/4 FAIL: 离线 reload 失败: {e}')
            page.screenshot(path=os.path.join(OUT_DIR, '02-offline-FAIL.png'), full_page=True)
            raise

        # 4) 离线 audio fetch (应仍能)
        audio_offline = page.evaluate("""
            async () => {
                try {
                    const r = await fetch('/audio/words/africa.mp3');
                    const buf = await r.arrayBuffer();
                    return { ok: true, status: r.status, len: buf.byteLength };
                } catch (e) {
                    return { ok: false, error: e.message };
                }
            }
        """)
        print(f'3/4 offline audio fetch: {audio_offline}')
        assert audio_offline.get('ok') and audio_offline.get('len', 0) > 1000, f'离线 audio 不可用: {audio_offline}'

        # 5) 离线 manifest 仍可访问
        m = page.evaluate("""
            async () => {
                try {
                    const r = await fetch('/manifest.webmanifest');
                    return { ok: r.ok, status: r.status };
                } catch (e) {
                    return { ok: false, error: e.message };
                }
            }
        """)
        print(f'4/4 offline manifest: {m}')
        assert m.get('ok'), f'离线 manifest 不可用: {m}'

        browser.close()
        print(f'\n✅ 离线验证全过')
        print(f'截图: {OUT_DIR}/02-offline-home.png')
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
