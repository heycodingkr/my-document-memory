#!/usr/bin/env node
// Records REAL product footage: the real web app (English UI) served by an isolated runtime (temp DB, random port, random token),
// driven by a Playwright script with human pacing. The clicks are scripted (this is not an agent run) and the video says so.
//
//   node demo/video/capture/capture-product.mjs [--only library-preview,agent-prompt,create-draft,deck-editor,public-memories] [--keep-raw]
//
// Output (git-ignored): demo/out/footage/product/<clip>.mp4 (1440x900, 30 fps, H.264, no audio) and report.json (cue times).
// Frames come from the Chrome DevTools screencast (JPEG q92) and are assembled at a constant 30 fps with their real timestamps.
// The token is placed in sessionStorage before load, so the "connect" screen is never shown; it never reaches a file, log or frame.
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { mkdirSync, mkdtempSync, rmSync, statSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { repo, seedFixtures, sleep, startRuntime } from './lib.mjs';

const require = createRequire(path.join(repo, 'web/package.json'));
const { chromium } = require('@playwright/test');
const args = process.argv.slice(2);
const only = (args.includes('--only') ? args[args.indexOf('--only') + 1] : '').split(',').filter(Boolean);
const keepRaw = args.includes('--keep-raw');
const outDir = path.join(repo, 'demo/out/footage/product');
mkdirSync(outDir, { recursive: true });

const OVERLAY = `(() => {
  if (window.__cursorReady) return; window.__cursorReady = true;
  const boot = () => {
    const st = document.createElement('style');
    st.textContent = '#__cur{position:fixed;left:0;top:0;width:30px;height:30px;margin:-3px 0 0 -4px;z-index:2147483647;pointer-events:none;transform:translate(-120px,-120px);filter:drop-shadow(0 3px 5px rgba(0,0,0,.35))}'
      + '.__rip{position:fixed;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;border:3px solid #254b3c;background:rgba(216,239,120,.65);pointer-events:none;z-index:2147483646;animation:__rip .7s ease-out forwards}'
      + '@keyframes __rip{from{transform:scale(.4);opacity:1}to{transform:scale(3.4);opacity:0}}';
    document.documentElement.appendChild(st);
    const c = document.createElement('div'); c.id = '__cur';
    c.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2.5v16l4.4-3.9 2.8 6.4 2.8-1.2-2.8-6.2 5.8-.2z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(c);
    addEventListener('mousemove', (e) => { c.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)'; }, true);
    addEventListener('mousedown', (e) => { const r = document.createElement('div'); r.className = '__rip'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; document.documentElement.appendChild(r); setTimeout(() => r.remove(), 800); }, true);
  };
  if (document.documentElement) boot(); else document.addEventListener('DOMContentLoaded', boot);
})();`;

const ease = (p) => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);

async function recordClip(browser, rt, name, script) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, permissions: ['clipboard-read', 'clipboard-write'], baseURL: rt.base });
  await ctx.addInitScript((t) => { try { sessionStorage.setItem('dmem.token', t); } catch { /* opaque origin */ } }, rt.token);
  await ctx.addInitScript(OVERLAY);
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('requestfailed', (r) => errors.push('request failed: ' + new URL(r.url()).pathname));
  const external = [];
  page.on('request', (r) => { const u = r.url(); if (!u.startsWith(rt.base) && !u.startsWith('data:') && !u.startsWith('blob:')) external.push(u); });
  await page.goto('/#templates');
  await page.getByRole('heading', { name: 'Template library.' }).waitFor({ timeout: 15000 });
  await page.evaluate(() => document.fonts.ready);
  await sleep(500);

  // --- screencast recorder ---
  const client = await ctx.newCDPSession(page);
  const frames = [];
  client.on('Page.screencastFrame', (f) => { frames.push({ ts: f.metadata.timestamp, data: f.data }); client.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}); });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 92, everyNthFrame: 1, maxWidth: 1440, maxHeight: 900 });
  await page.mouse.move(700, 450); // first repaint so a frame exists
  for (let i = 0; i < 100 && !frames.length; i++) await sleep(50);
  if (!frames.length) throw new Error(`${name}: no screencast frame arrived`);
  const t0 = frames[0].ts;
  const cues = {};
  const cue = (n) => { cues[n] = Math.round((Date.now() / 1000 - t0) * 1000) / 1000; };
  let pos = { x: 700, y: 450 };
  const h = {
    page, cue, sleep,
    async glide(x, y, ms = 700) {
      const from = pos, steps = Math.max(10, Math.round(ms / 16));
      for (let i = 1; i <= steps; i++) { const p = ease(i / steps); await page.mouse.move(from.x + (x - from.x) * p, from.y + (y - from.y) * p); await sleep(ms / steps); }
      pos = { x, y };
    },
    async point(loc, ms = 700, dx = 0, dy = 0) {
      await loc.scrollIntoViewIfNeeded();
      const b = await loc.boundingBox(); if (!b) throw new Error('no box');
      await h.glide(b.x + b.width / 2 + dx, b.y + b.height / 2 + dy, ms);
    },
    async click(loc, ms = 700) { await h.point(loc, ms); await sleep(140); await page.mouse.down(); await sleep(70); await page.mouse.up(); await sleep(180); },
    async type(loc, text, { replace = false, delay = 45 } = {}) {
      await h.click(loc);
      if (replace) { await page.keyboard.press('ControlOrMeta+A'); await sleep(120); }
      await page.keyboard.type(text, { delay });
    },
    async wheel(x, y, total, ms = 900) { await h.glide(x, y, 350); const steps = Math.max(6, Math.round(ms / 40)); for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, total / steps); await sleep(ms / steps); } }
  };
  let failure = null;
  try { await script(h); await sleep(900); } catch (e) { failure = e; }
  await client.send('Page.stopScreencast').catch(() => {});
  await client.detach().catch(() => {});
  // Privacy assertions on the final page: no token, no e-mail looking text, no loopback URL text.
  let leaks = [];
  try {
    const text = await page.evaluate(() => document.body.innerText);
    if (text.includes(rt.token)) leaks.push('token');
    if (/[\w.+-]+@[\w-]+\.[\w.-]+/.test(text)) leaks.push('email');
    if (/localhost|127\.0\.0\.1/.test(text)) leaks.push('loopback url');
  } catch { /* page closed */ }
  await ctx.close();
  if (failure) throw new Error(`${name}: ${failure.message.split('\n')[0]}`);

  // --- assemble at constant 30 fps ---
  const tmp = mkdtempSync(path.join(os.tmpdir(), `mdm-frames-${name}-`));
  const lines = ['ffconcat version 1.0'];
  frames.forEach((f, i) => {
    const file = `f${String(i).padStart(6, '0')}.jpg`;
    writeFileSync(path.join(tmp, file), Buffer.from(f.data, 'base64'));
    const next = frames[i + 1]?.ts ?? f.ts + 0.9;
    lines.push(`file '${file}'`, `duration ${Math.max(0.001, next - f.ts).toFixed(4)}`);
  });
  lines.push(`file 'f${String(frames.length - 1).padStart(6, '0')}.jpg'`);
  writeFileSync(path.join(tmp, 'list.txt'), lines.join('\n'));
  const outFile = path.join(outDir, `${name}.mp4`);
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'), '-vf', 'fps=30,scale=1440:900:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-r', '30', '-an', '-movflags', '+faststart', outFile], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error(`${name}: ffmpeg failed`);
  if (!keepRaw) rmSync(tmp, { recursive: true, force: true });
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames:format=duration', '-of', 'json', outFile], { encoding: 'utf8' });
  const p = JSON.parse(probe.stdout);
  const info = { file: `footage/product/${name}.mp4`, duration_s: Math.round(Number(p.format.duration) * 100) / 100, width: p.streams[0].width, height: p.streams[0].height, fps: p.streams[0].r_frame_rate, bytes: statSync(outFile).size, screencast_frames: frames.length, cues, page_errors: errors, external_requests: external, leaks };
  console.log(`${name}: ${info.duration_s}s ${info.width}x${info.height} ${info.fps}, ${frames.length} frames, errors ${errors.length}, external ${external.length}, leaks ${leaks.join(',') || 'none'}`);
  return info;
}

const CLIPS = {
  // Search, open a built-in public template, see its author/version/license, copy it to the private library.
  async 'library-preview'(h) {
    const { page, cue } = h;
    cue('library'); await sleep(1100);
    await h.type(page.getByLabel('Library search'), 'pitch'); cue('typed'); await sleep(250);
    await page.keyboard.press('Enter'); await sleep(1300); cue('results');
    const card = page.locator('.template-card').filter({ hasText: 'Public template' }).filter({ hasText: 'Startup Pitch Deck' }).first();
    await h.point(card.locator('.card-preview'), 800); await sleep(500);
    await h.click(card.locator('.card-preview')); cue('preview');
    const modal = page.getByRole('dialog'); await modal.waitFor(); await sleep(1700);
    const copy = modal.getByRole('button', { name: 'Copy to my templates', exact: true });
    await h.point(copy, 900); cue('copy-hover'); await sleep(300);
    await h.click(copy);
    await modal.getByText(/Original: My Document Memory/).waitFor({ timeout: 8000 }); cue('copied'); await sleep(700);
    await h.wheel(720, 420, -1100, 1100); cue('original'); await sleep(2600);   // back to the top: the copy keeps its original author, version and license
  },
  // The handoff: approve the outline, name the document, pick the reference, copy the ready-made request for the agent.
  async 'agent-prompt'(h) {
    const { page, cue } = h;
    cue('library'); await sleep(900);
    const card = page.locator('.template-card').filter({ hasText: 'Public template' }).filter({ hasText: 'Startup Pitch Deck' }).first();
    await h.click(card.locator('.card-preview')); cue('preview');
    const modal = page.getByRole('dialog'); await modal.waitFor(); await sleep(1200);
    await h.click(modal.getByRole('checkbox', { name: 'I approve this slide outline and order.' })); cue('approved'); await sleep(400);
    await h.type(modal.getByLabel('New document title'), 'My Document Memory - Pitch Deck', { replace: true }); cue('titled'); await sleep(300);
    await h.click(modal.getByRole('checkbox', { name: /My Document Memory: project notes/ })); cue('reference'); await sleep(500);
    const area = modal.getByLabel('Agent prompt');
    await h.point(area, 600); await sleep(300);
    await h.wheel(720, 640, 420, 900); cue('prompt'); await sleep(900);
    const copyBtn = modal.getByRole('button', { name: 'Copy prompt', exact: true });
    await h.click(copyBtn, 800);
    await modal.getByText(/Prompt copied/).waitFor({ timeout: 8000 }); cue('copied'); await sleep(1800);
  },
  // From a template + a reference to an editable draft with open questions and source excerpts, edit, save v2.
  async 'create-draft'(h) {
    const { page, cue } = h;
    cue('library'); await sleep(900);
    const card = page.locator('.template-card').filter({ hasText: 'One-Page Project Overview' }).first();
    await h.click(card.locator('.card-preview')); cue('preview');
    const modal = page.getByRole('dialog'); await modal.waitFor(); await sleep(1300);
    await h.type(modal.getByLabel('New document title'), 'My Document Memory - One-Page Overview', { replace: true }); cue('titled'); await sleep(300);
    await h.click(modal.getByRole('checkbox', { name: /My Document Memory: project notes/ })); cue('reference'); await sleep(600);
    await h.click(modal.getByRole('button', { name: /Use this template/ })); cue('create');
    await page.getByLabel('Document title', { exact: true }).waitFor({ timeout: 10000 }); await sleep(1500); cue('editor');
    await h.wheel(900, 560, 760, 1500); cue('scrolled'); await sleep(500);
    await h.wheel(900, 560, -760, 1100); await sleep(400);
    const first = page.locator('textarea[aria-label^="Paragraph"]').first();
    await h.type(first, 'Helps people share how documents are made, so anyone can create the document they need with AI.', { replace: true, delay: 38 }); cue('edited'); await sleep(500);
    await h.click(page.getByRole('button', { name: 'Save', exact: true }));
    await page.getByRole('status').filter({ hasText: 'Saved · v2' }).waitFor({ timeout: 8000 }); cue('saved'); await sleep(1800);
  },
  // Slides: outline approval, then the editor with the slide list.
  async 'deck-editor'(h) {
    const { page, cue } = h;
    cue('library'); await sleep(800);
    await h.click(page.getByRole('group', { name: 'Template type' }).getByRole('button', { name: 'Slides', exact: true })); cue('slides-filter'); await sleep(1100);
    const card = page.locator('.template-card').filter({ hasText: '10-Slide Pitch Deck' }).first();
    await h.click(card.locator('.card-preview')); cue('preview');
    const modal = page.getByRole('dialog'); await modal.waitFor(); await sleep(1500);
    await h.click(modal.getByRole('checkbox', { name: 'I approve this slide outline and order.' })); cue('approved'); await sleep(400);
    await h.type(modal.getByLabel('New document title'), 'My Document Memory - Pitch Deck', { replace: true }); cue('titled'); await sleep(300);
    await h.click(modal.getByRole('checkbox', { name: /My Document Memory: project notes/ })); await sleep(400);
    await h.click(modal.getByRole('button', { name: /Use this template/ })); cue('create');
    await page.getByLabel('Slide title', { exact: true }).waitFor({ timeout: 10000 }); await sleep(1400); cue('editor');
    for (const i of [1, 2, 3]) { await h.click(page.locator('.slide-thumb').nth(i), 600); await sleep(900); }
    cue('browsed');
    await h.point(page.getByRole('button', { name: 'Export ↗' }), 800); cue('export'); await sleep(1400);
  },
  // Anonymous browse of the public library, when the current build offers it without sign-in.
  async 'public-memories'(h) {
    const { page, cue } = h;
    cue('library'); await sleep(700);
    const link = page.getByRole('button', { name: 'Public memories', exact: true }).first();
    await h.click(link); cue('public'); await sleep(1600);
    await h.click(page.getByRole('button', { name: 'Business Proposal public preview' })); cue('preview');
    const modal = page.getByRole('dialog'); await modal.waitFor(); await sleep(2600);
    await h.click(modal.getByRole('button', { name: 'Close', exact: true })); await sleep(500);
    await h.wheel(900, 600, 900, 1500); cue('footnote'); await sleep(2200);
  }
};

const rt = await startRuntime();
const report = { about: 'Real web app (English UI) from an isolated runtime, driven by a Playwright script (scripted clicks, not an agent run).', binaries: 'snapshot of target/debug at capture time', clips: {}, failures: {} };
let browser;
try {
  report.fixtures = Object.fromEntries(Object.entries(await seedFixtures(rt)).map(([k, v]) => [k, { title: v.title, version: v.version }]));
  browser = await chromium.launch({ channel: 'chrome', args: ['--force-device-scale-factor=1', '--hide-scrollbars', '--disable-lcd-text'] });
  for (const name of Object.keys(CLIPS)) {
    if (only.length && !only.includes(name)) continue;
    try { report.clips[name] = await recordClip(browser, rt, name, CLIPS[name]); }
    catch (e) { report.failures[name] = e.message; console.error(`FAILED ${name}: ${e.message}`); }
  }
} finally {
  await browser?.close().catch(() => {});
  await rt.stop();
}
writeFileSync(path.join(outDir, only.length ? 'report.partial.json' : 'report.json'), JSON.stringify(report, null, 1));
process.exitCode = Object.keys(report.failures).length ? 1 : 0;
