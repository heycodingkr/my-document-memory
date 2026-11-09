#!/usr/bin/env node
// Renders demo/video/stage.html into a silent 1080p MP4, an SRT and a poster, in one language.
// English is the default; add --lang ko for the Korean version (any command below works with either).
//
//   node demo/video/build.mjs --at 4,30,60                  PNG stills in /tmp/mdm-video/stills (quick layout check)
//   node demo/video/build.mjs --lint                        layout lint at every second and caption end; exit 1 on any issue
//   node demo/video/build.mjs                               full render -> demo/out/video/mdm-demo-day.en.mp4 (+ .en.srt, -poster.jpg)
//   node demo/video/build.mjs --lang ko                     the Korean version -> demo/out/video/mdm-demo-day.ko.mp4
//   node demo/video/build.mjs --from 96 --to 128 --out /tmp/s6.en.mp4      render only that range
//   node demo/video/build.mjs --cut hackathon               the 90 s hackathon cut -> demo/out/video/mdm-hackathon-90s.en.mp4 (same flags work; English only)
//
// The stage is a pure function of time (window.__render(t)), so a render does not depend on machine speed.
// There is no voice track: captions are burned in and make-voice.py adds a voice-over later.
// Real footage can be composited in a second ffmpeg pass: stage.html lists each clip in window.__overlays
// (source window, speed, crop, privacy masks, destination box, time range) and draws a dark hole where it goes.
// Needs Google Chrome (Playwright's `chrome` channel) and ffmpeg. Playwright is taken from, in order: this repo's web/
// (the SvelteKit app, same stack as web-agentic-memory), the repo root, demo/video, or the sibling
// ../web-agentic-memory/web install (used until this repo has its own web/).
// This is an offline video-render tool, not product code (the product server is Rust). Nothing listens on a port:
// Chrome loads the stage from a virtual origin and Playwright answers every request straight from disk.
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { overlayOutputLimitArgs, posterTimeForRange } from './render-options.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');

function loadPlaywright() {
  const anchors = [path.join(repo, 'web/package.json'), path.join(repo, 'package.json'), path.join(here, 'package.json'), path.resolve(repo, '../web-agentic-memory/web/package.json')];
  for (const a of anchors) { try { return createRequire(a)('@playwright/test'); } catch { /* try the next one */ } }
  throw new Error('Playwright (@playwright/test) not found. Install it in web/, or keep ../web-agentic-memory/web/node_modules available.');
}
const { chromium } = loadPlaywright();

const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const opt = (name, fallback) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : fallback; };
// A cut is one video built on the same stage engine: its own stage page, its own script.json and its own output name.
const CUTS = {
  'demo-day': { stage: 'demo/video/stage.html', script: 'demo/video/script.json', out: (l) => `mdm-demo-day.${l}.mp4`, langs: ['ko', 'en'] },
  hackathon: { stage: 'demo/video/hackathon/stage.html', script: 'demo/video/hackathon/script.json', out: (l) => `mdm-hackathon-90s.${l}.mp4`, langs: ['en'] }
};
const cutName = opt('--cut', 'demo-day');
const cut = CUTS[cutName];
if (!cut) throw new Error(`--cut must be one of ${Object.keys(CUTS).join(', ')}, got ${cutName}`);
const lang = opt('--lang', 'en');
if (!cut.langs.includes(lang)) throw new Error(`--lang must be ${cut.langs.join(' or ')} for the ${cutName} cut, got ${lang}`);
const fps = Number(opt('--fps', '30'));
const stills = opt('--at', '');
const textAt = opt('--text', '');   // print the visible on-screen text at these times as JSON (number/claims check)
const lint = flag('--lint');
const outMp4 = path.resolve(opt('--out', path.join(repo, 'demo/out/video', cut.out(lang))));
const from = Number(opt('--from', '0'));

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.txt': 'text/plain', '.json': 'application/json' };
const ORIGIN = 'http://stage.local';
function serveFromDisk(route, url) {
  const rel = decodeURIComponent(new URL(url).pathname);
  const file = path.resolve(repo, '.' + rel);
  if (!file.startsWith(repo + path.sep) || !existsSync(file) || !statSync(file).isFile()) return route.fulfill({ status: 404, contentType: 'text/plain', body: 'not found' });
  return route.fulfill({ status: 200, contentType: MIME[path.extname(file)] || 'application/octet-stream', headers: { 'Cache-Control': 'no-store' }, body: readFileSync(file) });
}

let problems = 0;
const problem = (...m) => { problems++; console.error(...m); };
const browser = await chromium.launch({ channel: 'chrome', args: ['--force-device-scale-factor=1', '--disable-lcd-text', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.route('**/*', (route) => {
  const u = route.request().url();
  if (u.startsWith(`${ORIGIN}/`)) return serveFromDisk(route, u);
  if (u.startsWith('data:') || u.startsWith('blob:')) return route.continue();
  problem('blocked external request:', u);
  return route.abort();
});
page.on('pageerror', (e) => problem('page error:', e.message));
page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) problem('console:', m.text()); });
page.on('requestfailed', (r) => { if (!r.url().startsWith('data:') && !/blocked/i.test(r.failure()?.errorText || '') && r.failure()?.errorText !== 'net::ERR_FAILED') problem('request failed:', r.url()); });
page.on('response', (r) => { if (r.status() >= 400) problem(`HTTP ${r.status()}:`, r.url()); });
await page.goto(`${ORIGIN}/${cut.stage}?lang=${lang}`);
await page.evaluate(() => window.__init());
await page.waitForFunction(() => window.__ready === true);
const total = await page.evaluate(() => window.__total);
const to = Number(opt('--to', String(total)));
const captions = await page.evaluate(() => window.__captions);
const overlays = await page.evaluate(() => window.__overlays || []);
const posterAt = await page.evaluate(() => window.__poster);

const stamp = (s) => { const ms = Math.round(s * 1000); const p = (n, w = 2) => String(n).padStart(w, '0'); return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`; };

if (lint) {
  const script = JSON.parse(readFileSync(path.join(repo, cut.script), 'utf8'));
  const times = new Set();
  for (let t = 0.5; t < total; t += 1) times.add(Number(t.toFixed(2)));
  for (const b of script.beats) { times.add(Number((b.end - 0.25).toFixed(2))); times.add(Number(((b.start + b.end) / 2).toFixed(2))); }
  const found = new Map();
  const sorted = [...times].sort((a, b) => a - b);
  for (const t of sorted) {
    const issues = await page.evaluate((x) => { window.__render(x); return window.__lint(); }, t);
    for (const i of issues) {
      const key = `${i.type}|${i.text}|${i.detail || ''}`;
      const f = found.get(key) || { ...i, first: t, last: t, count: 0 };
      f.last = t; f.count++; found.set(key, f);
    }
  }
  for (const f of found.values()) console.log(`[${f.type}] t=${f.first}–${f.last}s (${f.count}×) ${JSON.stringify(f.text)} ${f.detail || ''}`);
  console.log(`lint (${lang}): ${sorted.length} sample times, ${found.size} distinct issue(s), ${problems} page problem(s)`);
  process.exitCode = found.size || problems ? 1 : 0;
} else if (textAt) {
  const rows = [];
  for (const t of textAt.split(',').map(Number)) rows.push({ t, text: await page.evaluate((x) => { window.__render(x); return window.__visibleText(); }, t) });
  console.log(JSON.stringify(rows));
  process.exitCode = problems ? 1 : 0;
} else if (stills) {
  const dir = '/tmp/mdm-video/stills';
  mkdirSync(dir, { recursive: true });
  for (const t of stills.split(',').map(Number)) {
    await page.evaluate((x) => window.__render(x), t);
    const file = path.join(dir, `${cutName === 'demo-day' ? '' : `${cutName}-`}${lang}-${String(t).replace('.', '_')}.png`);
    await page.screenshot({ path: file, type: 'png' });
    console.log(file);
  }
  process.exitCode = problems ? 1 : 0;
} else {
  mkdirSync(path.dirname(outMp4), { recursive: true });
  const used = overlays.filter((o) => o.to > from && o.from < to);
  for (const o of used) if (!existsSync(path.resolve(repo, 'demo/out', o.file))) throw new Error(`overlay clip missing: demo/out/${o.file}`);
  const stageOut = used.length ? outMp4.replace(/\.mp4$/, '.stage.mp4') : outMp4;
  const frames = Math.round((to - from) * fps);
  const quality = used.length ? ['-preset', 'veryfast', '-crf', '14'] : ['-preset', 'medium', '-crf', '19'];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'warning', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-an',
    '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p', '-c:v', 'libx264', ...quality,
    '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', stageOut], { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise((resolve, reject) => { ff.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited with ${code}`)))); ff.stdin.on('error', () => {}); });
  const started = Date.now();
  for (let f = 0; f < frames; f++) {
    await page.evaluate((t) => window.__render(t), from + f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (f % 300 === 0) console.log(`frame ${f}/${frames}  (${Math.round((Date.now() - started) / 1000)} s)`);
  }
  ff.stdin.end();
  await closed;

  if (used.length) {
    // Second pass: put the real clips into their holes. Times are relative to the rendered range.
    const inputs = ['-i', stageOut];
    const chains = [];
    let last = '0:v';
    used.forEach((o, i) => {
      inputs.push('-i', path.resolve(repo, 'demo/out', o.file));
      const speed = o.speed || 1, src = o.src || {}, a = o.from - from, b = o.to - from;
      const f = [];
      if (src.from != null || src.to != null) f.push(`trim=start=${src.from ?? 0}${src.to != null ? `:end=${src.to}` : ''}`);
      f.push(`setpts=(PTS-STARTPTS)/${speed}+${a}/TB`);
      if (o.crop) f.push(`crop=${o.crop.w}:${o.crop.h}:${o.crop.x}:${o.crop.y}`);
      // masks are in cropped-frame pixels: a solid box, or { blur: n } for a soft patch
      const boxes = (o.mask || []).filter((m) => !m.blur), blurs = (o.mask || []).filter((m) => m.blur);
      const post = boxes.map((m) => `drawbox=x=${m.x}:y=${m.y}:w=${m.w}:h=${m.h}:color=${m.color || 'white'}:t=fill`);
      post.push(`scale=${o.w}:${o.h}:flags=lanczos`, `fps=${fps}`, 'format=yuv420p');
      if (!blurs.length) chains.push(`[${i + 1}:v]${[...f, ...post].join(',')}[ov${i}]`);
      else {
        let cur = `m${i}_0`;
        chains.push(`[${i + 1}:v]${f.join(',')}[${cur}]`);
        blurs.forEach((m, k) => {
          const baseL = `m${i}_${k}a`, part = `m${i}_${k}b`, next = `m${i}_${k + 1}`;
          const lr = Math.min(Math.floor(m.blur), Math.floor(Math.min(m.w, m.h) / 2) - 1), cr = Math.max(1, Math.min(lr, Math.floor(Math.min(m.w, m.h) / 4) - 1));
          chains.push(`[${cur}]split[${baseL}][${part}]`, `[${part}]crop=${m.w}:${m.h}:${m.x}:${m.y},boxblur=lr=${lr}:lp=3:cr=${cr}:cp=3[bl${i}_${k}]`, `[${baseL}][bl${i}_${k}]overlay=${m.x}:${m.y}[${next}]`);
          cur = next;
        });
        chains.push(`[${cur}]${post.join(',')}[ov${i}]`);
      }
      chains.push(`[${last}][ov${i}]overlay=${o.x}:${o.y}:eof_action=${o.hold ? 'repeat' : 'pass'}:enable='between(t,${a},${b})'[b${i}]`);
      last = `b${i}`;
    });
    const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'warning', ...inputs, '-filter_complex', chains.join(';'), '-map', `[${last}]`, '-an',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-movflags', '+faststart', ...overlayOutputLimitArgs(frames), outMp4], { stdio: 'inherit' });
    if (r.status !== 0) throw new Error('overlay pass failed');
    rmSync(stageOut, { force: true });
    console.log(`composited ${used.length} real clip(s): ${used.map((o) => o.id).join(', ')}`);
  }
  // Captions as SRT (times are absolute in the video; shifted by --from when rendering a partial range).
  const srt = captions.filter((c) => c[1] > from && c[0] < to).map((c, i) => `${i + 1}\n${stamp(Math.max(0, c[0] - from))} --> ${stamp(Math.min(c[1], to) - from)}\n${c[2]}\n`).join('\n');
  writeFileSync(outMp4.replace(/\.mp4$/, '.srt'), srt);
  const posterTime = posterTimeForRange(posterAt, from, to);
  const posterOffset = (posterTime - from).toFixed(3);
  const posterPath = outMp4.replace(/\.mp4$/, '-poster.jpg');
  const poster = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', posterOffset, '-i', outMp4, '-frames:v', '1', '-q:v', '2', posterPath], { stdio: 'inherit' });
  if (poster.status !== 0) throw new Error(`poster extraction failed at ${posterOffset}s`);
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size', '-of', 'default=nw=1', outMp4], { encoding: 'utf8' });
  console.log(`done: ${outMp4}\n${probe.stdout.trim()}`);
  process.exitCode = problems ? 1 : 0;
}
await browser.close();
