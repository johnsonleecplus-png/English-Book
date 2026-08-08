"""截图 Home 页"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

OUT = Path(r"D:\10-English-Book\screenshots\iphone\tts-verify")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        viewport={'width': 393, 'height': 851},
        device_scale_factor=2.75,
        is_mobile=True,
        has_touch=True,
    )
    page = ctx.new_page()
    page.goto(f'http://127.0.0.1:5173/?cb=home&_={int(time.time())}', wait_until='domcontentloaded')
    page.wait_for_timeout(3000)

    page.screenshot(path=str(OUT / "home-compact.png"), full_page=True)
    print("home-compact.png saved")
    browser.close()
