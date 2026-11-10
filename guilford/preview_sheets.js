// Contact-sheet preview of nested strips: node preview_sheets.js <cut-sheets/xxx dir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const dir = path.join(__dirname, process.argv[2] || 'cut-sheets');
const files = fs.readdirSync(dir).filter(f => /^strip_\d+\.svg$/.test(f)).sort();
(async () => {
  const browser = await chromium.launch();
  const W = 1400, H = W / 4;
  const page = await browser.newPage({ viewport: { width: W + 40, height: 400 } });
  const rows = files.map(f => {
    const svg = fs.readFileSync(path.join(dir, f), 'utf8').replace(/<\?xml[^>]*>/, '')
      .replace('<g id="cut" fill="none"', '<g id="cut" fill="#d8c3a0"');
    const uri = 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
    return `<div style="font:600 14px system-ui;margin:8px 0 2px">${f}</div>` +
      `<img src="${uri}" style="display:block;width:${W}px;height:${H}px;background:#f6f1e7">`;
  }).join('');
  await page.setContent(`<html><body style="margin:20px;background:#fff">${rows}</body></html>`);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(dir, 'preview.png'), fullPage: true });
  await browser.close();
})();
