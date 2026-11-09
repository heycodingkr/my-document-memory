// Shared helpers for the capture scripts: an isolated runtime (temp DB, free port, random token) and fixture seeding.
// Nothing here touches the dev servers on 3847/5174 or data/dmem.sqlite3. The token lives only in memory and in the env of
// the child processes this file starts; it is never printed or written.
//
// Binaries and the web build are snapshots in $MDM_CAPTURE_DIR (default /tmp/mdm-capture): bin/{dmem-server,dmem,dmem-mcp} and web/.
// Refresh them with:  mkdir -p /tmp/mdm-capture/bin && cp target/debug/dmem{,-server,-mcp} /tmp/mdm-capture/bin/ && cp -R web/dist /tmp/mdm-capture/web
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createServer } from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const here = path.dirname(fileURLToPath(import.meta.url));
export const repo = path.resolve(here, '../../..');
export const SCRATCH = process.env.MDM_CAPTURE_DIR || '/tmp/mdm-capture';
export const BIN = path.join(SCRATCH, 'bin');
export const WEB = path.join(SCRATCH, 'web');
export const NOTES = path.join(repo, 'demo/video/hackathon/fixtures/my-document-memory-notes.md');
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function freePort() {
  return new Promise((resolve, reject) => {
    const s = createServer();
    s.once('error', reject);
    s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => resolve(port)); });
  });
}

// Start dmem-server on a free loopback port with a temp DB. Resolves to { base, token, env, stop }.
export async function startRuntime({ serveWeb = true } = {}) {
  for (const name of ['dmem-server', 'dmem', 'dmem-mcp']) if (!existsSync(path.join(BIN, name))) throw new Error(`missing snapshot binary: ${path.join(BIN, name)}`);
  if (serveWeb && !existsSync(path.join(WEB, 'index.html'))) throw new Error(`missing web snapshot: ${WEB}`);
  const port = await freePort();
  if (port === 3847 || port === 5174) throw new Error('refusing to use a dev-server port');
  const tmp = mkdtempSync(path.join(os.tmpdir(), 'mdm-capture-run-'));
  const token = randomBytes(32).toString('base64url');
  const base = `http://127.0.0.1:${port}`;
  const env = { ...process.env, DMEM_TOKEN: token, DMEM_ADDR: `127.0.0.1:${port}`, DMEM_URL: base, DMEM_DATABASE: path.join(tmp, 'library.sqlite3'), DMEM_WEB_DIR: WEB, DMEM_WEB_ORIGIN: base };
  const log = [];
  const child = spawn(path.join(BIN, 'dmem-server'), [], { cwd: repo, env, stdio: ['ignore', 'pipe', 'pipe'] });
  const keep = (b) => { log.push(String(b)); if (log.length > 50) log.shift(); };
  child.stdout.on('data', keep); child.stderr.on('data', keep);
  let exited = false; child.on('exit', () => { exited = true; });
  const stop = async () => {
    if (!exited) { child.kill('SIGTERM'); for (let i = 0; i < 50 && !exited; i++) await sleep(100); if (!exited) child.kill('SIGKILL'); }
    rmSync(tmp, { recursive: true, force: true });
  };
  process.once('exit', () => { if (!exited) child.kill('SIGKILL'); });
  for (let i = 0; i < 200; i++) {
    if (exited) throw new Error(`dmem-server exited early: ${log.join('').replaceAll(token, '***').slice(-400)}`);
    try { const r = await fetch(`${base}/healthz`); if (r.ok) return { base, token, env, tmp, pid: child.pid, stop }; } catch { /* not ready yet */ }
    await sleep(50);
  }
  await stop();
  throw new Error('dmem-server did not become ready');
}

// Authenticated JSON request. Errors never contain the token.
export async function call(rt, p, { method = 'GET', json, form } = {}) {
  const headers = { Authorization: `Bearer ${rt.token}` };
  if (json !== undefined) headers['Content-Type'] = 'application/json';
  const res = await fetch(rt.base + p, { method, headers, body: json !== undefined ? JSON.stringify(json) : form });
  const text = await res.text();
  if (!res.ok) throw new Error(`${method} ${p} -> ${res.status} ${text.slice(0, 200)}`);
  return text ? JSON.parse(text) : null;
}

// Real fixtures through the real HTTP API (the same calls the web app makes). English, en-US, synthetic.
export async function seedFixtures(rt) {
  const form = new FormData();
  form.append('title', 'My Document Memory: project notes');
  form.append('file', new Blob([readFileSync(NOTES)], { type: 'text/markdown' }), 'my-document-memory-notes.md');
  const source = await call(rt, '/v1/sources', { method: 'POST', form });
  const tpl = (title, summary, provider, doc_type, sections) => call(rt, '/v1/templates', { method: 'POST', json: { title, summary, form: { provider, doc_type, locale: 'en-US' }, sections, tags: [] } });
  const overview = await tpl('One-Page Project Overview', 'A one-page overview of a project: purpose, problem, how it works, what runs today, and what is next.', 'docx', 'report',
    ['Purpose', 'The Problem', 'How It Works', 'What Runs Today', "What's Next"]);
  const deck = await tpl('10-Slide Pitch Deck', 'A ten-slide pitch deck for a project, from the problem to what is next.', 'pptx', 'pitch_deck',
    ['Title', 'The Problem', 'The Insight', 'The Solution', 'How It Works', 'The Memory (Template, Reference, Document)', 'Agents and MCP', 'Sharing', 'Status', "What's Next"]);
  const blog = await tpl('Promo Blog Post', 'A promotional blog post: hook, problem, what it does, how it works, and how to try it.', 'docx', 'report',
    ['Hook', 'The Problem', 'What It Does', 'How It Works', 'Try It']);
  return { source, overview, deck, blog };
}
