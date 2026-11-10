// Renders previews of the stacked sign from preview/layers.json (written by generate.py).
// Usage: node render.js   -> renders/front.png, renders/front_lit.png, renders/angle.png
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'preview', 'layers.json')));
const { w: W, h: H, layers, lamps } = data;
const outDir = path.join(__dirname, 'renders');
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}
const zs = [...new Set(layers.map(L => L.z))].sort((a, b) => a - b);

function lensGlow(lit) {
  return lamps.map((l, i) => lit[i] ? `
    <circle cx="${l.x}" cy="${l.y}" r="${l.r * 0.98}" fill="url(#lensOn)"/>
    <circle cx="${l.x}" cy="${l.y}" r="${l.r * 2.6}" fill="url(#halo)" style="mix-blend-mode:screen"/>` : '').join('');
}
const defs = `
  <radialGradient id="lensOn"><stop offset="0" stop-color="#fff2ea"/><stop offset="0.35" stop-color="#ff4a3a"/>
    <stop offset="1" stop-color="#e0141c" stop-opacity="0.9"/></radialGradient>
  <radialGradient id="halo"><stop offset="0.3" stop-color="#ff2a1a" stop-opacity="0.55"/>
    <stop offset="1" stop-color="#ff2a1a" stop-opacity="0"/></radialGradient>`;

function decorations(L, tf = '') {
  let s = '';
  if (L.engrave) s += `<path d="${L.engrave}" fill="${L.engrave_color}" fill-rule="evenodd"${tf}/>`;
  if (L.score) s += `<path d="${L.score}" fill="none" stroke="#777" stroke-width="0.02"${tf}/>`;
  return s;
}

// ---- straight-on view with soft shadows; optional lit lamps
function frontHTML(lit) {
  let body = '';
  zs.forEach(z => {
    const s = 0.05 + 0.04 * z;
    body += `<defs><filter id="sh${z}" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="${s * 0.7}" dy="${s}" stdDeviation="${s * 0.6}" flood-opacity="0.5"/></filter></defs><g filter="url(#sh${z})">`;
    layers.filter(L => L.z === z).forEach(L => { body += `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd"/>` + decorations(L); });
    body += '</g>';
  });
  const px = 30;
  return `<html><body style="margin:0;background:#e3ddd2">
  <svg width="${W * px}" height="${H * px}" viewBox="0 0 ${W} ${H}"><defs>${defs}</defs>${body}${lensGlow(lit)}</svg></body></html>`;
}

// ---- 3D view: orthographic yaw/pitch; slices painted back to front (exact for this view)
function stackHTML(yawDeg, pitchDeg, gap, vw, vh, lit) {
  const th = yawDeg * Math.PI / 180, ph = pitchDeg * Math.PI / 180;
  const a = Math.cos(th), b = -Math.sin(ph) * Math.sin(th), d = Math.cos(ph);
  const zOf = z => z * 0.125 + z * gap;
  const scale = Math.min(vw / (W + 4), vh / (H + 4));
  const tf = (zz) => ` transform="matrix(${a} ${b} 0 ${d} ${-Math.sin(th) * zz} ${Math.sin(ph) * Math.cos(th) * zz})"`;
  let body = '';
  zs.forEach(z => {
    const Ls = layers.filter(L => L.z === z);
    const z0 = zOf(z), n = 6;
    for (let k = 0; k <= n; k++) {
      const zz = z0 + 0.125 * k / n;
      Ls.forEach(L => { body += `<path d="${L.d}" fill="${shade(L.color, 0.62 + 0.12 * k / n)}" fill-rule="evenodd"${tf(zz)}/>`; });
    }
    Ls.forEach(L => {
      body += `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd"${tf(z0 + 0.125)}/>` + decorations(L, tf(z0 + 0.125));
    });
  });
  const zl = zOf(8) + 0.125;
  const glow = `<g${tf(zl)}>${lensGlow(lit)}</g>`;
  const cx = W / 2, cy = H / 2;
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 35%,#f1ece3,#cdc5b8)">
  <svg width="${vw}" height="${vh}"><defs>${defs}</defs>
  <g transform="translate(${vw / 2} ${vh / 2}) scale(${scale}) translate(${-cx * a} ${-cy})">${body}${glow}</g></svg></body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const shoot = async (html, file, w, h) => {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.setContent(html);
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(outDir, file) });
    await page.close();
  };
  const fw = Math.round(W * 30), fh = Math.round(H * 30);
  await shoot(frontHTML([false, false]), 'front.png', fw, fh);
  await shoot(frontHTML([true, false]), 'front_lit.png', fw, fh);
  await shoot(stackHTML(-32, 8, 0, 900, 1250, [false, true]), 'angle.png', 900, 1250);
  await browser.close();
})();
