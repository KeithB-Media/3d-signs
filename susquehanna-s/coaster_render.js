// Preview of the engraved coaster on maple: node coaster_render.js [coaster/coaster_4in.svg]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const src = process.argv[2] || path.join(__dirname, 'coaster', 'coaster_4in.svg');
const slate = /slate/.test(src);
const svg = fs.readFileSync(src, 'utf8')
  .replace(/<\?xml[^>]*>/, '')
  .replace(/<g id="(cut|guide)">[\s\S]*?<\/g>/, '')
  .replace('fill="#000000"', slate ? 'fill="#b9bcbf" fill-opacity="0.9"' : 'fill="#3a2414" fill-opacity="0.92"')
  .replace(/width="[^"]*in" height="[^"]*in"/, 'width="600" height="600"');
const wood = `<html><body style="margin:0;background:#e9e5de;display:flex;align-items:center;justify-content:center;width:760px;height:760px">
<div style="position:relative;width:600px;height:600px;border-radius:50%;
  box-shadow:0 14px 30px rgba(0,0,0,.35), inset 0 0 0 7px rgba(120,80,40,.25);
  background:
    repeating-linear-gradient(83deg, rgba(150,100,50,.10) 0 3px, transparent 3px 11px),
    repeating-linear-gradient(97deg, rgba(120,80,40,.07) 0 2px, transparent 2px 17px),
    radial-gradient(circle at 35% 30%, #f1d9b0, #ddb57d 70%, #c99c62)">
  <div style="position:absolute;inset:0;filter:drop-shadow(0 0 0.6px rgba(40,20,5,.6))">${svg}</div>
</div></body></html>`;
const slateHtml = `<html><body style="margin:0;background:#f2f0ec;display:flex;align-items:center;justify-content:center;width:760px;height:760px">
<div style="position:relative;width:600px;height:600px;border-radius:6px;
  clip-path:polygon(0.6% 1.2%,30% 0.3%,62% 1.1%,99.2% 0.4%,99.7% 35%,98.9% 70%,99.6% 99.3%,70% 98.6%,40% 99.6%,0.8% 98.9%,0.2% 60%,1% 25%);
  background:
    radial-gradient(circle at 70% 60%, rgba(255,255,255,.04), transparent 40%),
    repeating-linear-gradient(12deg, rgba(255,255,255,.025) 0 2px, transparent 2px 9px),
    linear-gradient(160deg,#4a4c50,#3a3c40 60%,#33353a)">
  <div style="position:absolute;inset:0">${svg}</div>
</div></body></html>`;
const html = slate ? slateHtml : wood;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 760, height: 760 }, deviceScaleFactor: 2 });
  await p.setContent(html);
  await p.waitForTimeout(300);
  const out = src.replace(/\.svg$/, '_preview.png');
  await p.screenshot({ path: out });
  await b.close();
  console.log('wrote', path.relative(__dirname, out));
})();
