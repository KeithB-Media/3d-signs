// Renders a stacked sign from svg/<variant>/layers.json (written by generate.py).
// Usage: node render.js [variant ...]   (default: round round_rim panel panel_rim)
//   -> renders/<variant>/render_front.png, render_angle.png, render_exploded.png, layer_sheet.png
// Needs Playwright + Chromium.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML({ W, H, layers }) {
  const D = Math.max(W, H), m = D / 14;
  const sorted = [...layers].sort((a, b) => a.z - b.z);
  const groups = sorted.map((L, i) => {
    const s = i === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>` +
      `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>`;
  }).join('\n');
  const vw = W + 2 * m, vh = H + 2 * m, px = 900 / Math.max(vw, vh);
  return [`<html><body style="margin:0;background:#d9d4cb">
  <svg width="${vw * px}" height="${vh * px}" viewBox="${-m} ${-m} ${vw} ${vh}">
   <defs>
    <filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.2" dy="0.3" stdDeviation="0.3" flood-opacity="0.45"/></filter>
    <radialGradient id="light" cx="0.3" cy="0.25" r="0.9">
      <stop offset="0" stop-color="#fff" stop-opacity="0.22"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.18"/></radialGradient>
    <clipPath id="clip"><path d="${sorted[0].d}"/></clipPath>
   </defs>
   ${groups}
   <rect width="${W}" height="${H}" fill="url(#light)" clip-path="url(#clip)" style="mix-blend-mode:soft-light"/>
  </svg></body></html>`, Math.round(vw * px), Math.round(vh * px)];
}

// ---- 3D views: orthographic tilt, slices painted bottom-to-top (exact for a view from above)
function stackHTML({ W, H, layers }, tiltDeg, rotDeg, gap, w, h) {
  const D = Math.max(W, H), PX = 700 / D;
  const SL = 0.02 * D / 14, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const levels = [...new Set(layers.map(L => L.z))].sort((a, b) => a - b);
  const top = Math.max(...layers.map(L => L.z + L.t));
  const totalZ = top + gap * (levels.length - 1);
  const cy = h / 2 + totalZ * sin * PX / 2;
  const at = (zz, fill, d) => `<path transform="translate(${w / 2},${cy - zz * sin * PX}) scale(${PX},${PX * cos}) rotate(${rotDeg}) translate(${-W / 2},${-H / 2})" d="${d}" fill="${fill}" fill-rule="evenodd"/>`;
  let body = '';
  [...layers].sort((a, b) => a.z - b.z).forEach(L => {
    const n = Math.max(2, Math.round(L.t / SL));
    const base = L.z + levels.indexOf(L.z) * gap;
    if (gap) body += `<g opacity="0.35" filter="url(#blur)">${at(base - 0.02 - gap * 0.5, '#000', L.d)}</g>`;
    for (let k = 0; k <= n; k++) body += at(base + k * L.t / n, shade(L.color, 0.55 + 0.1 * k / n), L.d);
    body += at(base + L.t, L.color, L.d);
  });
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 40%,#f3efe7,#cfc8bb)">
  <svg width="${w}" height="${h}"><defs><filter id="blur"><feGaussianBlur stdDeviation="6"/></filter></defs>
  <g filter="url(#blur)" opacity="0.4">${at(-0.3, '#000', layers[0].d)}</g>${body}</svg></body></html>`;
}

function sheetHTML({ W, H, layers }) {
  const m = Math.max(W, H) * 0.03;
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="230" height="230" viewBox="${-m} ${-m} ${W + 2 * m} ${H + 2 * m}"><path d="${layers[0].d}" fill="none" stroke="#bbb" stroke-width="0.05" stroke-dasharray="0.2 0.2"/>
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>${L.stem.match(/^layer(\w+?)_/)[1].replace(/^(\d)/, 'Layer $1')}</div>
    <div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\w+?_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  const cols = layers.length;
  return [`<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(${cols},250px);gap:18px">${cards}</body></html>`,
    cols * 268 + 30, 340];
}

(async () => {
  const variants = process.argv.slice(2).length ? process.argv.slice(2) : ['round', 'round_rim', 'panel', 'panel_rim'];
  const browser = await chromium.launch();
  for (const v of variants) {
    const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'svg', v, 'layers.json')));
    const outDir = path.join(__dirname, 'renders', v);
    fs.mkdirSync(outDir, { recursive: true });
    const shoot = async (html, file, w, h) => {
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
      await page.setContent(html);
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(outDir, file) });
      await page.close();
    };
    const [fh, fw, fhh] = frontHTML(data);
    await shoot(fh, 'render_front.png', fw, fhh);
    await shoot(stackHTML(data, 38, 0, 0, 1000, 850), 'render_angle.png', 1000, 850);
    await shoot(stackHTML(data, 62, -20, 1.5, 1000, 1500), 'render_exploded.png', 1000, 1500);
    const [sh, sw, shh] = sheetHTML(data);
    await shoot(sh, 'layer_sheet.png', sw, shh);
    console.log(`renders/${v}/`);
  }
  await browser.close();
})();
