// Renders a stacked sign from <dir>/svg/layers.json (written by generate.py / generate_square.py).
// Usage: node render.js [dir]   -> <dir>/renders/render_front.png, render_angle.png, ...
//   node render.js          (round sign)      node render.js square   (square sign)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const base = path.join(__dirname, process.argv[2] || '.');
const meta = JSON.parse(fs.readFileSync(path.join(base, 'svg', 'layers.json')));
const layers = meta.layers;
const D = Math.max(meta.w, meta.h), PX = 50;   // 50 px per inch
const outDir = path.join(base, 'renders');
const outlineEl = (attrs) => meta.shape === 'circle'
  ? `<circle cx="${D / 2}" cy="${D / 2}" r="${D / 2}" ${attrs}/>`
  : `<rect x="0" y="0" width="${D}" height="${D}" rx="0.3" ${attrs}/>`;
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}
const svgURI = (d, fill) => 'data:image/svg+xml;base64,' + Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${D * PX}" height="${D * PX}" viewBox="0 0 ${D} ${D}">` +
  `<path d="${d}" fill="${fill}" fill-rule="evenodd"/></svg>`).toString('base64');

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML() {
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>` +
      `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>`;
  }).join('\n');
  return `<html><body style="margin:0;background:#d9d4cb">
  <svg width="900" height="900" viewBox="-1 -1 ${D + 2} ${D + 2}">
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
  const SL = 0.02, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const totalZ = layers.reduce((a, L) => a + L.t, 0) + gap * (layers.length - 1);
  const cy = h / 2 + totalZ * sin * PX / 2;
  let body = '', z = 0;
  const at = (zz, fill, d) => `<path transform="translate(${w / 2},${cy - zz * sin * PX}) scale(${PX},${PX * cos}) rotate(${rotDeg}) translate(${-D / 2},${-D / 2})" d="${d}" fill="${fill}" fill-rule="evenodd"/>`;
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
  await shoot(frontHTML(), 'render_front.png', 900, 900);
  await shoot(stackHTML(38, 0, 0, 1000, 800), 'render_angle.png', 1000, 800);
  await shoot(stackHTML(62, -20, 1.5, 1000, 1500), 'render_exploded.png', 1000, 1500);
  const cards = layers.map((L, i) => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="230" height="230" viewBox="-0.3 -0.3 ${D + 0.6} ${D + 0.6}">${outlineEl('fill="none" stroke="#bbb" stroke-width="0.05" stroke-dasharray="0.2 0.2"')}
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>Layer ${i + 1}</div><div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\d_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(${Math.min(4, layers.length)},250px);gap:18px">${cards}</body></html>`,
    'layer_sheet.png', 20 + Math.min(4, layers.length) * 268, 20 + Math.ceil(layers.length / 4) * 310);
  await browser.close();
})();
