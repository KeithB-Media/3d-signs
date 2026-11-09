// Renders the stacked sign from svg/layers.json (written by generate.py).
// Usage: node render.js -> renders/render_front.png, render_lit.png, render_angle.png,
//                          render_exploded.png, layer_sheet.png
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const base = __dirname;
const meta = JSON.parse(fs.readFileSync(path.join(base, 'svg', 'layers.json')));
const { w: W, h: H, layers, lights, red_lights: reds = [] } = meta;
const PX = 32;
const FH = Math.round(760 * (H + 0.8) / (W + 1.2));          // front view height for 760 px wide                                   // px per inch in the 3D views
const outDir = path.join(base, 'renders');
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}
const paths = (L, fill, edge) => L.pieces.map(p =>
  `<path d="${p.d}" fill="${fill ? fill(p.color) : p.color}" fill-rule="evenodd"` +
  (edge ? ` stroke="rgba(255,255,255,0.22)" stroke-width="0.025"` : '') + `/>`).join('');

// ---- straight-on view: each layer casts a soft shadow onto the ones below
function frontHTML(lit, dark) {
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0.12 : 0.03 + 0.06 * Math.min(i, 3) / 3;
    return `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.6}" flood-opacity="0.55"/></filter></defs>` +
      `<g filter="url(#sh${i})">${paths(L, dark ? c => shade(c, 0.35) : null, i >= 5 && !dark)}</g>`;
  }).join('\n');
  const glow = lit ? lights.map(([x, y]) =>
    `<circle cx="${x}" cy="${y}" r="1.1" fill="url(#glow)"/><circle cx="${x}" cy="${y}" r="0.13" fill="#fffef4"/>`).join('') +
    reds.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="0.7" fill="url(#rglow)"/><circle cx="${x}" cy="${y}" r="0.12" fill="#ff5a4a"/>`).join('') : '';
  const bg = dark ? '#1b1a19' : '#d9d4cb';
  return `<html><body style="margin:0;background:${bg}">
  <svg width="760" height="${FH}" viewBox="-0.6 -0.4 ${W + 1.2} ${H + 0.8}">
   <defs><radialGradient id="glow"><stop offset="0" stop-color="#fffbe6" stop-opacity="0.95"/>
     <stop offset="0.25" stop-color="#fff2b8" stop-opacity="0.45"/><stop offset="1" stop-color="#ffe9a0" stop-opacity="0"/></radialGradient>
     <radialGradient id="rglow"><stop offset="0" stop-color="#ff6a55" stop-opacity="0.9"/><stop offset="1" stop-color="#ff2a1a" stop-opacity="0"/></radialGradient>
     <linearGradient id="light" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.18"/>
     <stop offset="0.6" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.12"/></linearGradient></defs>
   ${groups}
   ${dark ? '' : `<rect x="0" y="0" width="${W}" height="${H}" fill="url(#light)" style="mix-blend-mode:soft-light"/>`}
   ${glow}
  </svg></body></html>`;
}

// ---- 3D views: orthographic tilt, slices painted bottom-to-top
function stackHTML(tiltDeg, gap, w, h, scale = PX) {
  const SL = 0.03, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const totalZ = layers.length * 0.125 + gap * (layers.length - 1);
  const cy = h / 2 + totalZ * sin * scale / 2;
  const at = (zz, inner) => `<g transform="translate(${w / 2},${cy - zz * sin * scale}) scale(${scale},${scale * cos}) translate(${-W / 2},${-H / 2})">${inner}</g>`;
  let body = '';
  layers.forEach((L, i) => {
    const n = Math.max(2, Math.round(L.t / SL));
    const base = L.z + i * gap;
    if (gap) body += `<g opacity="0.3" filter="url(#blur)">${at(base - 0.02 - gap * 0.4, paths(L, () => '#000'))}</g>`;
    for (let k = 0; k <= n; k++) body += at(base + k * L.t / n, paths(L, c => shade(c, 0.5 + 0.12 * k / n)));
    body += at(base + L.t, paths(L));
  });
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 40%,#f3efe7,#cfc8bb)">
  <svg width="${w}" height="${h}"><defs><filter id="blur"><feGaussianBlur stdDeviation="6"/></filter></defs>
  ${body}</svg></body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const shoot = async (html, file, w, h) => {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.setContent(html);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(outDir, file) });
    await page.close();
  };
  await shoot(frontHTML(false, false), 'render_front.png', 760, FH);
  await shoot(frontHTML(true, true), 'render_lit.png', 760, FH);
  await shoot(stackHTML(40, 0, 900, 900, 34), 'render_angle.png', 900, 900);
  await shoot(stackHTML(64, 1.6, 900, 1400, 26), 'render_exploded.png', 900, 1400);
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 14px system-ui;color:#333">
    <svg width="190" height="265" viewBox="0 0 ${W} ${H}">
    ${L.pieces.map(p => `<path d="${p.d}" fill="${p.color}" stroke="#555" stroke-width="0.04" fill-rule="evenodd"/>`).join('')}</svg>
    <div>Layer ${i + 1}</div><div style="font-weight:400;font-size:12px">${L.stem.replace(/^layer\d_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:16px;display:grid;grid-template-columns:repeat(5,200px);gap:14px">${cards}</body></html>`,
    'layer_sheet.png', 1090, 680);
  await browser.close();
})();
