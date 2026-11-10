// Pictures of a printed face: as printed (daylight) and lit from behind (glowing).
// Usage: node render_face.js <face dir with face_preview.svg>   (needs Playwright + Chromium)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dir = process.argv[2];
let svg = fs.readFileSync(path.join(dir, 'face_preview.svg'), 'utf8')
  .replace(/<circle[^>]*stroke-dasharray[^>]*\/>/, '');                    // drop the window guide
const meta = JSON.parse(fs.readFileSync(path.join(dir, 'face.json')));
const inner = svg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>$/, '');
const r = meta.disc_mm / 2, w = meta.window_mm / 2;

// lit: colours glow (brighter, a little bloom); full-thickness black stays black
const lit = inner.replace(/fill="(#[0-9a-f]{6})"/g, (m, c) => {
  const n = parseInt(c.slice(1), 16), rgb = [n >> 16, (n >> 8) & 255, n & 255];
  const lum = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;
  if (lum < 0.12) return `fill="${c}"`;
  const out = rgb.map(v => Math.min(255, Math.round(v * 1.25 + 25)));
  return `fill="rgb(${out.join(',')})"`;
});

const page = (body, bg) => `<html><body style="margin:0;background:${bg}">
<svg width="800" height="800" viewBox="${-r - 12} ${-r - 12} ${2 * r + 24} ${2 * r + 24}">
 <defs><clipPath id="win"><circle r="${w}"/></clipPath>
  <filter id="bloom" x="-20%" y="-20%" width="140%" height="140%">
   <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 </defs>
 <circle r="${r + 6}" fill="#1b1b1b"/>
 ${body}
 <circle r="${(w + r + 6) / 2}" fill="none" stroke="#2a2a2a" stroke-width="${r + 6 - w}"/>
</svg></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 800, height: 800 } });
  await p.setContent(page(`<g clip-path="url(#win)">${inner}</g>`, '#e9e5de'));
  await p.screenshot({ path: path.join(dir, 'face_daylight.png') });
  await p.setContent(page(`<g clip-path="url(#win)" filter="url(#bloom)">${lit}</g>`, '#0d0d10'));
  await p.screenshot({ path: path.join(dir, 'face_lit.png') });
  await b.close();
})();
