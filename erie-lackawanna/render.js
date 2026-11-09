// Renders both stacked signs from <sign>/svg/layers.json (written by generate.py).
// Usage: node render.js   -> square/renders/*.png and round/renders/*.png
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PX = 50;                               // 50 px per inch

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML(S) {
  const groups = S.layers.map((L, i) => {
    const s = L.z === 0 ? 0 : 0.05 + L.t * 0.35;
    return `<defs><filter id="sh${i}" x="-10%" y="-10%" width="120%" height="120%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.55}" flood-opacity="0.55"/></filter></defs>` +
      `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${L.z ? `url(#sh${i})` : 'url(#wall)'}"/>`;
  }).join('\n');
  return `<html><body style="margin:0;background:#d9d4cb">
  <svg width="900" height="900" viewBox="-1 -1 ${S.w + 2} ${S.h + 2}">
   <defs><filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.2" dy="0.3" stdDeviation="0.3" flood-opacity="0.45"/></filter>
    <radialGradient id="light" cx="0.3" cy="0.25" r="0.9">
      <stop offset="0" stop-color="#fff" stop-opacity="0.22"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.18"/></radialGradient></defs>
   ${groups}
   <path d="${S.layers[0].d}" fill="url(#light)" style="mix-blend-mode:soft-light"/>
  </svg></body></html>`;
}

// ---- 3D views: orthographic tilt, slices painted bottom-to-top (exact for a view from above)
function stackHTML(S, tiltDeg, rotDeg, gap, w, h) {
  const SL = 0.02, phi = tiltDeg * Math.PI / 180;
  const sin = Math.sin(phi), cos = Math.cos(phi);
  const levels = [...new Set(S.layers.map(L => L.z))].sort((a, b) => a - b);
  const top = Math.max(...S.layers.map(L => L.z + L.t)) + gap * (levels.length - 1);
  const cy = h / 2 + top * sin * PX / 2;
  const at = (zz, fill, d) => `<path transform="translate(${w / 2},${cy - zz * sin * PX}) scale(${PX},${PX * cos}) rotate(${rotDeg}) translate(${-S.w / 2},${-S.h / 2})" d="${d}" fill="${fill}" fill-rule="evenodd"/>`;
  let body = '';
  levels.forEach((z, li) => {
    const group = S.layers.filter(L => L.z === z);
    const base = z + li * gap;
    if (gap && li) body += `<g opacity="0.35" filter="url(#blur)">${group.map(L => at(base - 0.02 - gap * 0.5, '#000', L.d)).join('')}</g>`;
    const t = group[0].t, n = Math.max(2, Math.round(t / SL));
    for (let k = 0; k <= n; k++) body += group.map(L => at(base + k * t / n, shade(L.color, 0.55 + 0.1 * k / n), L.d)).join('');
    body += group.map(L => at(base + t, L.color, L.d)).join('');
  });
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 40%,#f3efe7,#cfc8bb)">
  <svg width="${w}" height="${h}"><defs><filter id="blur"><feGaussianBlur stdDeviation="6"/></filter></defs>
  <g filter="url(#blur)" opacity="0.4">${at(-0.3, '#000', S.layers[0].d)}</g>${body}</svg></body></html>`;
}

function sheetHTML(S) {
  const cards = S.layers.map(L => `<div style="text-align:center;font:600 15px system-ui;color:#333">
    <svg width="230" height="230" viewBox="-0.3 -0.3 ${S.w + 0.6} ${S.h + 0.6}">
    <rect width="${S.w}" height="${S.h}" fill="none" stroke="#ccc" stroke-width="0.05" stroke-dasharray="0.2 0.2"/>
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>${L.stem.replace(/_.*/, '').replace('layer', 'Layer ')}</div>
    <div style="font-weight:400;font-size:13px">${L.stem.replace(/^layer\w+?_/, '').replace(/_/g, ' ')}</div></div>`).join('');
  return `<html><body style="margin:0;background:#eeeae2;padding:20px;display:grid;grid-template-columns:repeat(3,250px);gap:18px">${cards}</body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  for (const name of ['square', 'round']) {
    const S = JSON.parse(fs.readFileSync(path.join(__dirname, name, 'svg', 'layers.json')));
    const outDir = path.join(__dirname, name, 'renders');
    fs.mkdirSync(outDir, { recursive: true });
    const shoot = async (html, file, w, h) => {
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
      await page.setContent(html);
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(outDir, file) });
      await page.close();
    };
    await shoot(frontHTML(S), 'render_front.png', 900, 900);
    await shoot(stackHTML(S, 38, 0, 0, 1000, 800), 'render_angle.png', 1000, 800);
    await shoot(stackHTML(S, 62, -20, 1.5, 1000, 1300), 'render_exploded.png', 1000, 1300);
    const rows = Math.ceil(S.layers.length / 3);
    await shoot(sheetHTML(S), 'layer_sheet.png', 850, 40 + rows * 300);
  }
  await browser.close();
})();
