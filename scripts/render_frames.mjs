#!/usr/bin/env node
// Export frames from a page that follows the render contract (references/craft.md): window.TIMELINE,
// window.renderFrame(t, canvas) (it may return a Promise), and optionally window.READY (a Promise the page resolves once
// every image, plate and font it needs is decoded).
//   every frame:  node render_frames.mjs <page.html> <out dir> [--from N] [--to M]       -> <out>/f0000.png ...
//   stills:       node render_frames.mjs <page.html> --still 1.5,3.25 <out.png> [--scale 0.5]   (side by side)
// Run it with the project folder as the working directory: Playwright is resolved from there
// (npm i -D playwright, then npx playwright install chromium). Before the first frame it waits for READY, loads every
// @font-face the page declares and renders one throwaway frame. It fails (exit 1), before writing the frame, on a page
// error, a console error, a file that does not load, a font that does not load, a file still loading when a frame is
// captured, a page that calls renderFrame on its own during the render (a preview loop), or READY or a frame taking
// over 60 s.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const USAGE = 'usage: node render_frames.mjs <page.html> <out dir> [--from N] [--to M]\n'
  + '       node render_frames.mjs <page.html> --still t1,t2 <out.png> [--scale k]';
const LIMIT_MS = 60000;
const die = (msg, code = 2) => { console.error(msg); process.exit(code); };

const opts = {}, pos = [];
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  if (!argv[i].startsWith('--')) { pos.push(argv[i]); continue; }
  const k = argv[i].slice(2);
  if (!['from', 'to', 'still', 'scale'].includes(k) || i + 1 >= argv.length) die(`bad option ${argv[i]}\n${USAGE}`);
  opts[k] = argv[++i];
}
if (pos.length !== 2) die(USAGE);
const [pageFile, out] = pos;
if (!fs.existsSync(pageFile)) die(`no such page: ${pageFile}`);

let chromium;
try { ({ chromium } = createRequire(path.join(process.cwd(), 'x.js'))('playwright')); }
catch { die('playwright is not installed in this folder: run  npm i -D playwright  then  npx playwright install chromium'); }

// a file:// page is its own origin per file: without this flag, drawing a local image taints the canvas (the export
// throws) and fetch() of a local JSON fails
const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage();
const problems = [], pending = new Set();
// a page error, a console error or a file that fails is fatal at once (after 200 ms, to collect the related messages),
// rather than when the frame's time limit runs out
let dying = false;
const fatal = (msg) => {
  problems.push(msg);
  if (dying) return;
  dying = true;
  setTimeout(async () => { console.error(problems.join('\n')); await browser.close().catch(() => {}); process.exit(1); }, 200);
};
page.on('pageerror', (e) => fatal('page error: ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') fatal('console error: ' + m.text()); });
page.on('request', (r) => { if (!r.url().startsWith('data:')) pending.add(r); });
page.on('requestfinished', (r) => pending.delete(r));
page.on('requestfailed', (r) => { pending.delete(r); fatal(`did not load: ${r.url()} (${r.failure()?.errorText})`); });
// wait until no file is loading (so a late failure is caught), then stop on any problem
const stopIfProblems = async () => {
  for (const t0 = Date.now(); pending.size && Date.now() - t0 < LIMIT_MS;) await new Promise((r) => setTimeout(r, 20));
  if (pending.size) problems.push('still loading after 60 s: ' + [...pending].map((r) => r.url()).join(', '));
  if (!problems.length) return;
  console.error(problems.join('\n'));
  await browser.close();
  process.exit(1);
};
const inPage = (fn, arg) => page.evaluate(fn, arg).catch((e) => { problems.push(e.message.split('\n')[0]); return null; });

await page.goto(pathToFileURL(path.resolve(pageFile)).href);
try { await page.waitForFunction(() => window.TIMELINE && window.renderFrame, null, { timeout: 30000 }); }
catch { problems.push('the page did not define window.TIMELINE and window.renderFrame within 30 s'); }
await stopIfProblems();
// READY, then every declared font face (document.fonts.ready does not load a face nothing has drawn with yet); then
// route the page's own calls of window.renderFrame through a counter, so a preview loop is caught
const badFonts = await inPage(async (ms) => {
  const limit = (p, what) => Promise.race([p, new Promise((_, no) => setTimeout(() => no(new Error(`${what} did not finish within ${ms / 1000} s`)), ms))]);
  if (window.READY) await limit(window.READY, 'window.READY');
  const faces = [...document.fonts];
  await Promise.all(faces.map((f) => f.load().catch(() => {})));
  const rf = window.renderFrame;
  window.__render = { rf, foreign: 0, limit };
  window.renderFrame = function (...a) { window.__render.foreign++; return rf.apply(this, a); };
  return faces.filter((f) => f.status === 'error').map((f) => f.family);
}, LIMIT_MS);
if (badFonts?.length) problems.push('fonts that did not load: ' + badFonts.join(', '));
await stopIfProblems();
const T = await page.evaluate(() => ({ w: TIMELINE.width, h: TIMELINE.height, fps: TIMELINE.fps,
  n: Math.round(TIMELINE.duration * TIMELINE.fps) }));

// render frame t at scale k; the PNG comes back only if nothing went wrong while it was drawn
const grab = async (t, k) => {
  const r = await inPage(async ([t, k, ms]) => {
    const c = document.createElement('canvas'); c.width = TIMELINE.width; c.height = TIMELINE.height;
    await window.__render.limit(Promise.resolve(window.__render.rf(t, c)), `renderFrame(${t})`);
    let png = c;
    if (k !== 1) {
      png = document.createElement('canvas'); png.width = Math.round(c.width * k); png.height = Math.round(c.height * k);
      const g = png.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(c, 0, 0, png.width, png.height);
    }
    return { b64: png.toDataURL('image/png').split(',')[1], foreign: window.__render.foreign };
  }, [t, k, LIMIT_MS]);
  if (pending.size) problems.push(`frame at ${t} s was captured while these were still loading: `
    + [...pending].map((q) => q.url()).join(', ') + ' (load them in window.READY, or await them in renderFrame)');
  if (r?.foreign) problems.push(`the page called window.renderFrame on its own ${r.foreign} times during the render `
    + '(a preview loop?): skip it when navigator.webdriver is true');
  await stopIfProblems();
  return r.b64;
};
await grab(0, 1); // thrown away: lets anything the first draw starts (a font, an image decode) finish
await page.evaluate(() => document.fonts.ready);
await stopIfProblems();

if (opts.still) {
  const times = opts.still.split(',').map(Number), k = Number(opts.scale ?? '1');
  const last = (T.n - 1) / T.fps;
  if (times.some((t) => !(t >= 0 && t <= last))) die(`--still times must be numbers from 0 to ${last.toFixed(3)} s (the last frame)`);
  if (!(k > 0 && k <= 4)) die('--scale must be over 0 and at most 4');
  const width = times.length * Math.round(T.w * k) + 16 * (times.length - 1);
  if (width > 32000) die(`${times.length} stills at --scale ${k} make an image ${width} px wide, over the browser's limit: lower --scale or pass fewer times`);
  const shots = [];
  for (const t of times) shots.push(await grab(Math.round(t * T.fps) / T.fps, k));
  const b64 = await page.evaluate(async ([shots, gap]) => {
    const imgs = await Promise.all(shots.map((s) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = 'data:image/png;base64,' + s; })));
    const c = document.createElement('canvas'); c.width = imgs.reduce((a, i) => a + i.width, 0) + gap * (imgs.length - 1); c.height = imgs[0].height;
    const g = c.getContext('2d'); g.fillStyle = '#222'; g.fillRect(0, 0, c.width, c.height);
    let x = 0; for (const i of imgs) { g.drawImage(i, x, 0); x += i.width + gap; }
    return c.toDataURL('image/png').split(',')[1];
  }, [shots, times.length > 1 ? 16 : 0]);
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, Buffer.from(b64, 'base64'));
  console.log(`still ${out}: t = ${times.join(', ')} s`);
} else {
  const from = Number(opts.from ?? '0'), last = T.n - 1;
  let to = Number(opts.to ?? String(last));
  if (!Number.isInteger(from) || !Number.isInteger(to) || from < 0 || from > Math.min(to, last)) die(`--from and --to must be frame numbers with 0 <= from <= to <= ${last}`);
  if (to > last) { console.error(`--to ${to} is past the last frame; stopping at ${last}`); to = last; }
  fs.mkdirSync(out, { recursive: true });
  const stale = fs.readdirSync(out).filter((f) => /^f\d+\.png$/.test(f) && Number(f.slice(1, -4)) > last);
  if (stale.length) die(`${out} holds ${stale.length} frames past this film's last frame (${last}), left by a longer export: render into a new folder (one per version)`);
  // the film's clock, next to its frames, so sheet.py and flicker.py read the fps instead of assuming it
  fs.writeFileSync(path.join(out, 'timeline.json'), JSON.stringify({ width: T.w, height: T.h, fps: T.fps, frames: T.n }) + '\n');
  const t0 = Date.now();
  for (let f = from; f <= to; f++) {
    const b64 = await grab(f / T.fps, 1);
    fs.writeFileSync(path.join(out, `f${String(f).padStart(4, '0')}.png`), Buffer.from(b64, 'base64'));
    if ((f - from) % 48 === 47) console.log(`  ${f - from + 1}/${to - from + 1} frames`);
  }
  console.log(`frames ${from}..${to} -> ${out} in ${((Date.now() - t0) / 1000).toFixed(1)} s (${T.w}x${T.h} @ ${T.fps} fps)`);
}
await stopIfProblems();
await browser.close();
