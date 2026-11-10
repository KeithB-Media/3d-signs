// Renders a stacked sign from <dir>/svg/layers.json (written by the generate*.py scripts).
// Usage: node render.js [dir]   -> <dir>/renders/render_front.png, render_angle.png, ...
//   node render.js  |  node render.js square  |  node render.js rectangle  |  node render.js round-ring
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const base = path.join(__dirname, process.argv[2] || '.');
const meta = JSON.parse(fs.readFileSync(path.join(base, 'svg', 'layers.json')));
const layers = meta.layers;
const W = meta.w, H = meta.h, D = Math.max(W, H);
const outDir = path.join(base, 'renders');
const outlineEl = (attrs) => meta.shape === 'circle'
  ? `<circle cx="${W / 2}" cy="${H / 2}" r="${W / 2}" ${attrs}/>`
  : `<rect x="0" y="0" width="${W}" height="${H}" rx="0.3" ${attrs}/>`;
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}

// page size for a view of the whole sign: longest side ~900 px (1400 for wide signs)
const frontW = W > H * 1.3 ? 1400 : Math.round(900 * (W + 2) / (H + 2));
const frontH = Math.round(frontW * (H + 2) / (W + 2));

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML() {
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>` +
      `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>`;
  }).join('\n');
  return `<html><body style="margin:0;background:#d9d4cb">
  <svg width="${frontW}" height="${frontH}" viewBox="-1 -1 ${W + 2} ${H + 2}">
   <defs>
    <filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.2" dy="0.3" stdDeviation="0.3" flood-opacity="0.45"/></filter>
    <radialGradient id="light" cx="0.3" cy="0.25" r="0.9">
      <stop offset="0" stop-color="#fff" stop-opacity="0.22"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.18"/></radialGradient>
   </defs>
   ${groups}
   ${outlineEl('fill="url(#light)" style="mix-blend-mode:soft-light"')}
  </svg></body></html>`;
}

// ---- 3D views: orthographic tilt, slices painted bottom-to-top (exact for a view from above)
function stackHTML(tiltDeg, rotDeg, gap, w, h) {
  const PX = Math.min(50, 0.8 * w / D);
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
  const wide = W > H * 1.3;
  await shoot(frontHTML(), 'render_front.png', frontW, frontH);
  if (wide) {
    await shoot(stackHTML(45, 0, 0, 1400, 800), 'render_angle.png', 1400, 800);
    await shoot(stackHTML(65, 0, 1.2, 1400, 1100), 'render_exploded.png', 1400, 1100);
  } else {
    await shoot(stackHTML(38, 0, 0, 1000, 800), 'render_angle.png', 1000, 800);
    await shoot(stackHTML(62, -20, 1.5, 1000, 1500), 'render_exploded.png', 1000, 1500);
  }
  const cw = 230, ch = Math.round(cw * (H + 0.6) / (W + 0.6)), cols = wide ? 2 : Math.min(4, layers.length);
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="${wide ? 2 * cw : cw}" height="${wide ? 2 * ch : ch}" viewBox="-0.3 -0.3 ${W + 0.6} ${H + 0.6}">${outlineEl('fill="none" stroke="#bbb" stroke-width="0.05" stroke-dasharray="0.2 0.2"')}
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>Layer ${i + 1}</div><div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\d_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  const cardW = (wide ? 2 * cw : cw) + 20, cardH = (wide ? 2 * ch : ch) + 80;
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(${cols},${cardW}px);gap:18px">${cards}</body></html>`,
    'layer_sheet.png', 40 + cols * (cardW + 18), 40 + Math.ceil(layers.length / cols) * (cardH + 18));
  await browser.close();
})();
