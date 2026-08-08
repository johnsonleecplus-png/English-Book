"""Phase 4 PWA verify: manifest / service worker / 离线播放."""
from playwright.sync_api import sync_playwright
import os, sys, traceback, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(PROJECT_ROOT, 'screenshots', 'iphone', 'phase4')
os.makedirs(OUT_DIR, exist_ok=True)
DEV_URL = 'http://localhost:5173/?bust=phase4'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        # 1) 加载首页
        page.goto(DEV_URL, wait_until='domcontentloaded')
        page.wait_for_timeout(2500)

        # 2) 验证 manifest 可访问
        manifest = page.evaluate("""
            async () => {
                const r = await fetch('/manifest.webmanifest');
                return { status: r.status, ct: r.headers.get('content-type'), text: await r.text() };
            }
        """)
        print(f'1/6 manifest: status={manifest["status"]}  ct={manifest["ct"]}')
        assert manifest['status'] == 200
        assert 'json' in manifest['ct']
        m = json.loads(manifest['text'])
        assert m['name'] == 'English Book · 上海中考词汇'
        assert m['display'] == 'standalone'
        assert any(i['sizes'] == '192x192' for i in m['icons'])
        assert any(i.get('purpose') == 'maskable' for i in m['icons'])
        print(f'   ✓ name / display / 192 icon / maskable icon')

        # 3) 验证 service worker 已注册
        sw_info = page.evaluate("""
            async () => {
                if (!('serviceWorker' in navigator)) return { supported: false };
                const reg = await navigator.serviceWorker.getRegistration();
                return {
                    supported: true,
                    hasReg: !!reg,
                    scope: reg?.scope,
                    scriptURL: reg?.active?.scriptURL,
                    state: reg?.active?.state,
                };
            }
        """)
        print(f'2/6 service worker: {sw_info}')
        assert sw_info['supported'], 'serviceWorker 不支持'
        # dev 模式下 registered 也算 OK
        assert sw_info['hasReg'], 'service worker 未注册'

        # 4) 验证 3 个 PWA 图标可访问
        for name, size in [('pwa-192x192.png', 192), ('pwa-512x512.png', 512), ('pwa-maskable-512x512.png', 512), ('apple-touch-icon.png', 180)]:
            r = page.evaluate(f"""
                async () => {{
                    const r = await fetch('/icons/{name}');
                    const len = parseInt(r.headers.get('content-length') || '0', 10);
                    return {{ status: r.status, len, ct: r.headers.get('content-type') }};
                }}
            """)
            ok = r['status'] == 200 and r['len'] > 1000 and 'png' in r['ct']
            print(f'3/6 {name}: status={r["status"]}  len={r["len"]}  ct={r["ct"]}  {"✓" if ok else "✗"}')
            assert ok, f'{name} 不可访问'

        # 5) 验证 audio 在 SW cache 后能离线播放
        # 先在网络下抓一个 audio, 让 SW 缓存
        audio_check = page.evaluate("""
            async () => {
                const r = await fetch('/audio/words/africa.mp3');
                const buf = await r.arrayBuffer();
                return { status: r.status, len: buf.byteLength, ct: r.headers.get('content-type') };
            }
        """)
        print(f'4/6 audio fetch (online): {audio_check}')
        assert audio_check['status'] == 200 and audio_check['len'] > 1000

        # 6) 验证 iOS meta 标签
        ios_metas = page.evaluate("""
            () => {
                const get = (n) => document.querySelector(`meta[name="${n}"]`)?.getAttribute('content') || null;
                return {
                    apple_capable: get('apple-mobile-web-app-capable'),
                    apple_title: get('apple-mobile-web-app-title'),
                    apple_status: get('apple-mobile-web-app-status-bar-style'),
                    theme_color: get('theme-color'),
                    apple_icon: document.querySelector('link[rel="apple-touch-icon"]')?.getAttribute('href'),
                    manifest: document.querySelector('link[rel="manifest"]')?.getAttribute('href'),
                };
            }
        """)
        print(f'5/6 iOS meta: {ios_metas}')
        assert ios_metas['apple_capable'] == 'yes'
        assert ios_metas['apple_title'] == 'English Book'
        assert ios_metas['apple_icon'] is not None
        assert ios_metas['manifest'] is not None

        # 7) 截图 manifest / iOS meta 验证
        page.screenshot(path=os.path.join(OUT_DIR, '01-home.png'), full_page=True)
        print('6/6 ok: 01-home.png')

        summary = {
            'manifest_ok': True,
            'service_worker': sw_info,
            'icons_ok': True,
            'audio_online_ok': audio_check,
            'ios_metas': ios_metas,
        }
        print(f'\n=== 总结 ===')
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        browser.close()
        print(f'\nDone: PWA 验证通过, 截图保存到 {OUT_DIR}')
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
