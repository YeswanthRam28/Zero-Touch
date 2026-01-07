from playwright.sync_api import sync_playwright
from pathlib import Path

out = Path('landing/screenshots')
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    url = 'http://127.0.0.1:5175/#/dashboard'
    print('Navigating to', url)
    page.goto(url, wait_until='networkidle')

    viewports = [
        (1360, 800, 'desktop'),
        (900, 1200, 'tablet'),
        (375, 812, 'mobile')
    ]

    for w, h, name in viewports:
        print('Setting viewport', name, w, h)
        page.set_viewport_size({'width': w, 'height': h})
        # wait a bit for layout
        page.wait_for_timeout(500)
        path = out / f'dashboard_{name}.png'
        page.screenshot(path=str(path), full_page=False)
        print('Saved', path)

    browser.close()
print('Done')
