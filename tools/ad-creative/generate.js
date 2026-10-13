#!/usr/bin/env node
// Product photo -> Instagram ad creative.
//   node generate.js --image photo.jpg --title "Light up your room" \
//     --price "₹1,366" --cta "Shop now" --brand "PROJECT M SHOP" \
//     --url projectmshop.com --format square --out ad.png
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const FONT = path.join(__dirname, 'fonts', 'Inter-Bold.ttf');
const FORMATS = {
  square:   { w: 1080, h: 1080, top: 110, imgH: 610, bottom: 60 },
  portrait: { w: 1080, h: 1350, top: 110, imgH: 800, bottom: 60 },
  story:    { w: 1080, h: 1920, top: 250, imgH: 1000, bottom: 250 },
};

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Returns { input, width, height } for a line of text rendered with Pango.
async function text(str, { size, color = '#ffffff', width, align = 'left' }) {
  const markup = `<span font="Inter Bold ${size}" foreground="${color}">${esc(str)}</span>`;
  const buf = await sharp({
    text: { text: markup, fontfile: FONT, rgba: true, width, align, wrap: 'word', spacing: Math.round(size * 0.12) },
  }).png().toBuffer();
  const m = await sharp(buf).metadata();
  return { input: buf, width: m.width, height: m.height };
}

const roundedMask = (w, h, r) =>
  Buffer.from(`<svg width="${w}" height="${h}"><rect width="${w}" height="${h}" rx="${r}" fill="#fff"/></svg>`);

async function loadImage(src) {
  if (/^https?:\/\//.test(src)) {
    const res = await fetch(src);
    if (!res.ok) throw new Error(`Could not download image (${res.status}): ${src}`);
    return Buffer.from(await res.arrayBuffer());
  }
  return fs.readFileSync(src);
}

async function generate(opts) {
  const f = FORMATS[opts.format || 'square'];
  if (!f) throw new Error(`format must be one of: ${Object.keys(FORMATS).join(', ')}`);
  const { w: W, h: H } = f;
  const PAD = 48;
  const accent = opts.accent || '#FFC83D';
  const photo = await sharp(await loadImage(opts.image)).rotate().toBuffer();
  const layers = [];

  // Blurred, darkened copy of the photo fills the canvas so nothing is cropped away.
  const bg = await sharp(photo).resize(W, H, { fit: 'cover' }).blur(40).modulate({ brightness: 0.5 }).png().toBuffer();

  // Product photo, scaled to fit its box whole, with rounded corners.
  const boxW = W - PAD * 2;
  const fitted = await sharp(photo).resize(boxW, f.imgH, { fit: 'inside' }).png().toBuffer();
  const fm = await sharp(fitted).metadata();
  const rounded = await sharp(fitted)
    .composite([{ input: roundedMask(fm.width, fm.height, 28), blend: 'dest-in' }]).png().toBuffer();
  const imgLeft = Math.round((W - fm.width) / 2);
  const imgTop = f.top + Math.round((f.imgH - fm.height) / 2);
  layers.push({ input: rounded, left: imgLeft, top: imgTop });

  // Top bar: brand left, url right.
  if (opts.brand) {
    const b = await text(opts.brand, { size: 28, color: '#ffffff' });
    layers.push({ input: b.input, left: PAD, top: f.top - 70 });
  }
  if (opts.url) {
    const u = await text(opts.url, { size: 24, color: accent });
    layers.push({ input: u.input, left: W - PAD - u.width, top: f.top - 68 });
  }

  // Headline under the photo.
  let y = f.top + f.imgH + 36;
  const head = await text(opts.title, { size: opts.format === 'story' ? 72 : 60, width: boxW });
  layers.push({ input: head.input, left: PAD, top: y });

  // Bottom row: price pill (left) + CTA pill (right), pinned above the bottom margin.
  const rowH = 84;
  const rowY = H - f.bottom - rowH;
  if (opts.price) {
    const p = await text(opts.price, { size: 44, color: '#111111' });
    const pw = p.width + 64;
    layers.push({ input: Buffer.from(`<svg width="${pw}" height="${rowH}"><rect width="${pw}" height="${rowH}" rx="${rowH / 2}" fill="${accent}"/></svg>`), left: PAD, top: rowY });
    layers.push({ input: p.input, left: PAD + 32, top: rowY + Math.round((rowH - p.height) / 2) });
  }
  if (opts.cta) {
    const c = await text(opts.cta, { size: 36, color: '#ffffff' });
    const cw = c.width + 72;
    const cl = W - PAD - cw;
    layers.push({ input: Buffer.from(`<svg width="${cw}" height="${rowH}"><rect x="2" y="2" width="${cw - 4}" height="${rowH - 4}" rx="${(rowH - 4) / 2}" fill="none" stroke="#fff" stroke-width="4"/></svg>`), left: cl, top: rowY });
    layers.push({ input: c.input, left: cl + 36, top: rowY + Math.round((rowH - c.height) / 2) });
  }

  return sharp(bg).composite(layers).png().toBuffer();
}

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) o[argv[i].slice(2)] = argv[++i];
  }
  return o;
}

if (require.main === module) {
  const o = parseArgs(process.argv.slice(2));
  if (!o.image || !o.title) {
    console.error('Usage: node generate.js --image <path|url> --title "Headline" [--price "₹1,366"] [--cta "Shop now"] [--brand NAME] [--url site.com] [--format square|portrait|story] [--accent "#FFC83D"] [--out ad.png]');
    process.exit(1);
  }
  generate(o).then((png) => {
    fs.writeFileSync(o.out || 'ad.png', png);
    console.log(`wrote ${o.out || 'ad.png'}`);
  }).catch((e) => { console.error(e.message); process.exit(1); });
}

module.exports = { generate };
