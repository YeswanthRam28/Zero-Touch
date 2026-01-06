import { chromium } from 'playwright';
import axe from 'axe-core';

(async function runAxe() {
  const url = process.argv[2] || 'http://localhost:5175/#/dashboard';
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    console.log('Opening', url);
    await page.goto(url, { waitUntil: 'networkidle' });

    // inject axe-core
    await page.addScriptTag({ content: axe.source });

    // run axe
    const results = await page.evaluate(async () => {
      // eslint-disable-next-line no-undef
      return await axe.run(document, {
        // a11y rules you may want to disable can be configured here
      });
    });

    console.log('Axe results:');
    console.log(JSON.stringify({ violations: results.violations, passes: results.passes }, null, 2));

    const violations = results.violations || [];
    if (violations.length === 0) {
      console.log('\nNo accessibility violations found by axe-core.');
    } else {
      console.log(`\nFound ${violations.length} accessibility violation(s):`);
      violations.forEach((v, i) => {
        console.log(`${i + 1}. ${v.id} — ${v.help}`);
        v.nodes.forEach((n) => {
          console.log(`   Target: ${n.target.join(', ')}`);
          console.log(`   Failure summary: ${n.failureSummary}`);
        });
      });
    }
  } catch (e) {
    console.error('Error running axe:', e);
    process.exitCode = 2;
  } finally {
    await browser.close();
  }
})();
