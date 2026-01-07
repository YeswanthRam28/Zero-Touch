import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:5175/#/dashboard', { waitUntil: 'networkidle' });
  const headings = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(h => ({ tag: h.tagName, text: h.innerText, id: h.id || null }));
  });
  console.log('Headings on page:', headings);
  await browser.close();
})();
