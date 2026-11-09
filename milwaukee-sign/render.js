// Renders the stacked sign from svg/layers.json (written by generate.py).
// Usage: node render.js [svg|svg_panel] -> renders/ (or renders_panel/)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const src = process.argv[2] || 'svg';
const { w: W, h: H, layers } = JSON.parse(fs.readFileSync(path.join(__dirname, src, 'layers.json')));
const PX = 50;
const outDir = path.join(__dirname, src === 'svg' ? 'renders' : 'renders_panel');
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}

function frontHTML(vw, vh) {
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>` +
      `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>`;
  }).join('\n');
  return `<html><body style="margin:0;background:#d9d4cb">
  <svg width="${vw}" height="${vh}" viewBox="-1 -1 ${W + 2} ${H + 2}">
   <defs>
    <filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.2" dy="0.3" stdDeviation="0.3" flood-opacity="0.45"/></filter>
    <linearGradient id="light" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.15"/></linearGradient>
   </defs>
   ${groups}
   <path d="${layers[0].d}" fill="url(#light)"/>
  </svg></body></html>`;
}

function stackHTML(tiltDeg, rotDeg, gap, w, h, px) {
  const SL = 0.02, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const totalZ = Math.max(...layers.map(L => L.z + L.t)) + gap * (layers.length - 1);
  const cy = h / 2 + totalZ * sin * px / 2;
  let body = '';
  const at = (zz, fill, d) => `<path transform="translate(${w / 2},${cy - zz * sin * px}) scale(${px},${px * cos}) rotate(${rotDeg}) translate(${-W / 2},${-H / 2})" d="${d}" fill="${fill}" fill-rule="evenodd"/>`;
  layers.forEach((L, i) => {
    const n = Math.max(2, Math.round(L.t / SL));
    const base = L.z + i * gap;
    if (gap) body += `<g opacity="0.35" filter="url(#blur)">${at(base - 0.02 - gap * 0.5, '#000', L.d)}</g>`;
    for (let k = 0; k <= n; k++) body += at(base + k * L.t / n, shade(L.color, 0.55 + 0.1 * k / n), L.d);
    body += at(base + L.t, L.color, L.d);
  });
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 40%,#f3efe7,#cfc8bb)">
  <svg width="${w}" height="${h}"><defs><filter id="blur"><feGaussianBlur stdDeviation="6"/></filter></defs>
  <g filter="url(#blur)" opacity="0.4">${at(-0.3, '#000', layers[0].d)}</g>${body}</svg></body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const shoot = async (html, file, w, h) => {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.setContent(html);
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(outDir, file) });
    await page.close();
  };
  await shoot(frontHTML(1300, 1300 * (H + 2) / (W + 2)), 'render_front.png', 1300, Math.round(1300 * (H + 2) / (W + 2)));
  await shoot(stackHTML(45, -12, 0, 1300, 800, 48), 'render_angle.png', 1300, 800);
  await shoot(stackHTML(60, -12, 1.4, 1300, 1000, 44), 'render_exploded.png', 1300, 1000);
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="400" height="${400 * (H + 0.6) / (W + 0.6)}" viewBox="-0.3 -0.3 ${W + 0.6} ${H + 0.6}">
    <rect width="${W}" height="${H}" fill="none" stroke="#bbb" stroke-width="0.05" stroke-dasharray="0.3 0.3"/>
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>Layer ${i + 1}</div><div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\d_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(3,420px);gap:18px">${cards}</body></html>`,
    'layer_sheet.png', 1340, 520);
  await browser.close();
})();
