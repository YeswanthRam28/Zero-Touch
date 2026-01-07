const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const logs = [];
  page.on('console', (msg) => {
    logs.push({ type: msg.type(), text: msg.text() });
    console.log(`[console:${msg.type()}] ${msg.text()}`);
  });
  page.on('pageerror', (err) => {
    logs.push({ type: 'pageerror', text: String(err) });
    console.error('[pageerror]', err);
  });
  page.on('requestfailed', (req) => {
    logs.push({ type: 'requestfailed', url: req.url(), status: req.failure() });
    console.log('[requestfailed]', req.url(), req.failure());
  });

  try {
    await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle' });
    // wait a bit to let runtime errors surface
    await page.waitForTimeout(6000);
    const screenshotPath = 'tools/frontend_screenshot.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('screenshot:', screenshotPath);
    const out = {
      timestamp: new Date().toISOString(),
      logs,
    };
    fs.writeFileSync('tools/console_logs.json', JSON.stringify(out, null, 2));
    console.log('wrote tools/console_logs.json');
  } catch (e) {
    console.error('error during capture', e);
  } finally {
    await browser.close();
  }
})();