// Renders the stacked figure from svg/layers.json (written by generate.py).
// Usage: node render.js   -> renders/render_front.png, render_angle.png, render_exploded.png, layer_sheet.png
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'svg', 'layers.json')));
const { w: W, h: H, layers } = data;
const PX = 55;
const outDir = path.join(__dirname, 'renders');
fs.mkdirSync(outDir, { recursive: true });

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.round(Math.min(255, v * f)));
  return `rgb(${c.join(',')})`;
}
const mouth = "";

// ---- straight-on view: each layer casts a soft shadow onto the layers below
function frontHTML() {
  const groups = layers.map((L, i) => {
    const s = i === 0 ? 0 : 0.04 + L.z * 0.12;
    return `<defs><filter id="sh${i}" x="-20%" y="-20%" width="140%" height="140%">` +
      `<feDropShadow dx="${s * 0.8}" dy="${s}" stdDeviation="${s * 0.6}" flood-opacity="0.5"/></filter></defs>` +
      `<path d="${L.d}" fill="${L.color}" fill-rule="evenodd" filter="${i ? `url(#sh${i})` : 'url(#wall)'}"/>`;
  }).join('\n');
  const vw = 900, vh = Math.round(900 * (H + 1) / (W + 1));
  return [`<html><body style="margin:0;background:#e4ddd0">
  <svg width="${vw}" height="${vh}" viewBox="-0.5 -0.5 ${W + 1} ${H + 1}">
   <defs><filter id="wall" x="-10%" y="-10%" width="125%" height="125%"><feDropShadow dx="0.15" dy="0.25" stdDeviation="0.25" flood-opacity="0.4"/></filter></defs>
   ${groups}${mouth}
  </svg></body></html>`, vw, vh];
}

// ---- 3D view: figure stands upright in the base; orthographic, camera turned and raised.
// Each layer is a flat slice at depth z; painted back to front.
function standHTML(yawDeg, pitchDeg, gap, w, h) {
  const yaw = yawDeg * Math.PI / 180, pit = pitchDeg * Math.PI / 180;
  const cx = data.base_cx, by = data.base_y;      // ground line (y=0) sits on the base top
  // projection of (x, y_up, z_toward_viewer) -> screen
  const proj = (x, y, z) => {
    const X = x * Math.cos(yaw) + z * Math.sin(yaw);
    const Z = -x * Math.sin(yaw) + z * Math.cos(yaw);
    return [X, -(y * Math.cos(pit) - Z * Math.sin(pit))];
  };
  // matrix mapping SVG layer coords (u right, v down) at depth z
  const mat = (z) => {
    const [ox, oy] = proj(-cx, by, z);
    const [ux, uy] = proj(1, 0, 0);
    const [vx, vy] = proj(0, -1, 0);
    return `matrix(${ux} ${uy} ${vx} ${vy} ${ox} ${oy})`;
  };
  const SL = 0.02;
  let body = '';
  // base: a box drawn as stacked slices of the base plate (plate in the x-z plane)
  const bw = data.base.w, bd = 3.2, bt = 0.5;
  const plate = (yy, fill) => {
    const pts = [[-bw / 2, -bd / 2], [bw / 2, -bd / 2], [bw / 2, bd / 2], [-bw / 2, bd / 2]]
      .map(([x, z]) => proj(x, yy, z).join(',')).join(' ');
    return `<polygon points="${pts}" fill="${fill}"/>`;
  };
  for (let k = 0; k <= 20; k++) body += plate(-bt + bt * k / 20, shade('#C9A574', 0.6 + 0.2 * k / 20));
  body += plate(0, '#C9A574');
  const fig = layers.map((L, i) => ({ ...L, z0: L.z + i * 0 }));
  const zOff = -0.125;  // centre the 1/4" backer in the slot
  fig.forEach((L, i) => {
    const lvl = parseInt(L.stem.match(/layer(\d)/)[1]);
    const base = zOff + L.z + (lvl - 1) * gap;
    const n = Math.max(2, Math.round(L.t / SL));
    for (let k = 0; k <= n; k++)
      body += `<path transform="${mat(base + L.t * k / n)}" d="${L.d}" fill="${shade(L.color, 0.6 + 0.12 * k / n)}" fill-rule="evenodd"/>`;
    body += `<path transform="${mat(base + L.t)}" d="${L.d}" fill="${L.color}" fill-rule="evenodd"/>`;
    if (false)
      body += `<g transform="${mat(base + L.t)}">${mouth}</g>`;
  });
  // the tab sits inside the slot: redraw the base in front of the backer over it
  const front = (y0, y1, z0, fill) => {
    const pts = [[-bw / 2, y0, z0], [bw / 2, y0, z0], [bw / 2, y1, bd / 2], [-bw / 2, y1, bd / 2]];
    return `<polygon points="${pts.map(([x, y, z]) => proj(x, y, z).join(',')).join(' ')}" fill="${fill}"/>`;
  };
  for (let k = 0; k <= 20; k++) {
    const yy = -bt + bt * k / 20;
    const pts = [[-bw / 2, 0.13], [bw / 2, 0.13], [bw / 2, bd / 2], [-bw / 2, bd / 2]]
      .map(([x, z]) => proj(x, yy, z).join(',')).join(' ');
    body += `<polygon points="${pts}" fill="${k === 20 ? '#C9A574' : shade('#C9A574', 0.6 + 0.2 * k / 20)}"/>`;
  }
  const vh = (H + 2.4) * W * 1.3 / W, vw = vh * w / h;
  return `<html><body style="margin:0;background:radial-gradient(circle at 50% 40%,#f3efe7,#cfc8bb)">
  <svg width="${w}" height="${h}" viewBox="${-vw / 2} ${-H - 0.3} ${vw} ${H + 2.4}">
  <ellipse cx="0" cy="0.6" rx="${bw * 0.6}" ry="1.2" fill="#000" opacity="0.18" filter="url(#b)"/>
  <defs><filter id="b"><feGaussianBlur stdDeviation="0.3"/></filter></defs>${body}</svg></body></html>`;
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
  const [fh, fw, fhh] = frontHTML();
  await shoot(fh, 'render_front.png', fw, fhh);
  await shoot(standHTML(-28, 14, 0, 800, 1000), 'render_angle.png', 800, 1000);
  await shoot(standHTML(-55, 12, 0.9, 800, 1000), 'render_exploded.png', 800, 1000);
  const cards = layers.map(L => `<div style="text-align:center;font:600 14px system-ui;color:#333">
    <svg width="190" height="${Math.round(190 * H / W)}" viewBox="0 0 ${W} ${H}">
    <path d="${L.d}" fill="${L.color}" stroke="#555" stroke-width="0.03" fill-rule="evenodd"/></svg>
    <div>${L.stem.replace(/_/g, ' ')}</div></div>`).join('');
  await shoot(`<html><body style="margin:0;background:#eeeae2;padding:16px;display:grid;grid-template-columns:repeat(4,200px);gap:14px">${cards}</body></html>`,
    'layer_sheet.png', 880, Math.ceil(layers.length / 4) * (Math.round(190 * H / W) + 40) + 50);
  await browser.close();
})();
