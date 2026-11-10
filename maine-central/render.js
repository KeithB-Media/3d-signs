// Renders a stacked sign from <sign>/svg/layers.json (written by generate.py).
// Usage: node render.js square   |   node render.js round
//   -> <sign>/renders/render_front.png, render_angle.png, render_exploded.png, layer_sheet.png
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const sign = process.argv[2] || 'square';
const { w: W, h: H, round, layers } = JSON.parse(fs.readFileSync(path.join(__dirname, sign, 'svg', 'layers.json')));
const outDir = path.join(__dirname, sign, 'renders');
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML(pxW) {
  const pxH = Math.round(pxW * (H + 2) / (W + 2));
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>` +
      `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>`;
  }).join('\n');
  const light = round ? `<circle cx="${W / 2}" cy="${H / 2}" r="${W / 2}" fill="url(#light)"/>`
    : `<path d="${layers[0].d}" fill="url(#light)"/>`;
  return [`<html><body style="margin:0;background:#d9d4cb">
  <svg width="${pxW}" height="${pxH}" viewBox="-1 -1 ${W + 2} ${H + 2}">
   <defs>
    <filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.2" dy="0.3" stdDeviation="0.3" flood-opacity="0.45"/></filter>
    <radialGradient id="light" cx="0.3" cy="0.25" r="0.9">
      <stop offset="0" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.15"/></radialGradient>
   </defs>
   ${groups}
   ${light}
  </svg></body></html>`, pxW, pxH];
}

// ---- 3D views: orthographic tilt, slices painted bottom-to-top (exact for a view from above)
function stackHTML(tiltDeg, rotDeg, gap, w, h, PX) {
  const SL = 0.02, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const totalZ = layers.reduce((a, L) => a + L.t, 0) + gap * (layers.length - 1);
  const cy = h / 2 + totalZ * sin * PX / 2;
  let body = '', z = 0;
  const at = (zz, fill, d) => `<path transform="translate(${w / 2},${cy - zz * sin * PX}) scale(${PX},${PX * cos}) rotate(${rotDeg}) translate(${-W / 2},${-H / 2})" d="${d}" fill="${fill}" fill-rule="evenodd"/>`;
  layers.forEach((L, i) => {
    const n = Math.max(2, Math.round(L.t / SL));
    const base = z + i * gap;
    if (gap) body += `<g opacity="0.35" filter="url(#blur)">${at(base - 0.02 - gap * 0.5, '#000', L.d)}</g>`;
    for (let k = 0; k <= n; k++) body += at(base + k * L.t / n, shade(L.color, 0.55 + 0.1 * k / n), L.d);
    body += at(base + L.t, L.color, L.d);
    z += L.t;
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
  const PX = 900 / Math.max(W, H) * 0.95;
  const [fh, fw, fhh] = frontHTML(1000);
  await shoot(fh, 'render_front.png', fw, fhh);
  await shoot(stackHTML(38, 0, 0, 1000, 800, PX * 0.95), 'render_angle.png', 1000, 800);
  await shoot(stackHTML(62, -20, 1.5, 1100, 1400, PX * 0.85), 'render_exploded.png', 1100, 1400);

  const cw = 250, ch = Math.round(cw * H / W);
  const outline = round ? `<circle cx="${W / 2}" cy="${H / 2}" r="${W / 2}"` : `<rect width="${W}" height="${H}"`;
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="${cw}" height="${ch}" viewBox="-0.3 -0.3 ${W + 0.6} ${H + 0.6}">${outline} fill="none" stroke="#bbb" stroke-width="0.05" stroke-dasharray="0.2 0.2"/>
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>Layer ${i + 1}</div><div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\d_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  const cols = layers.length;
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(${cols},${cw}px);gap:18px">${cards}</body></html>`,
    'layer_sheet.png', 40 + cols * cw + (cols - 1) * 18, ch + 100);
  await browser.close();
})();
