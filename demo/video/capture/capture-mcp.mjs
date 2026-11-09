#!/usr/bin/env node
// Records a REAL MCP session: dmem-mcp over stdio (newline-delimited JSON-RPC) against an isolated runtime.
//   node demo/video/capture/capture-mcp.mjs
// Writes demo/out/footage/mcp-trace.json (full results, git-ignored) and demo/video/hackathon/data/mcp-trace.json (summary the
// stage reads; no token, no secrets). Every call is timed with a monotonic clock around the request/response round trip.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { BIN, call, repo, seedFixtures, startRuntime } from './lib.mjs';

const rt = await startRuntime({ serveWeb: false });
const fx = await seedFixtures(rt);
const mcp = spawn(path.join(BIN, 'dmem-mcp'), [], { env: rt.env, stdio: ['pipe', 'pipe', 'pipe'] });
let buf = '', waiting = new Map(), nextId = 1;
mcp.stdout.on('data', (b) => {
  buf += b;
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    if (!line.trim()) continue;
    const msg = JSON.parse(line);
    const w = waiting.get(msg.id); if (w) { waiting.delete(msg.id); w(msg); }
  }
});
const rpc = (method, params) => new Promise((resolve, reject) => {
  const id = nextId++;
  const t0 = performance.now();
  const timer = setTimeout(() => reject(new Error(`${method} timed out`)), 20000);
  waiting.set(id, (msg) => { clearTimeout(timer); resolve({ msg, ms: performance.now() - t0 }); });
  mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
});
const text = (msg) => msg.result?.content?.map((c) => c.text).join('') ?? '';
const parse = (msg) => { try { return JSON.parse(text(msg)); } catch { return null; } };

const trace = { about: 'Real dmem-mcp stdio session against an isolated runtime (temp DB, random port, random token). elapsed_ms is the client-side round trip.', fixtures: { source_title: fx.source.title, templates: [fx.overview.title, fx.deck.title, fx.blog.title] }, calls: [] };
try {
  const init = await rpc('initialize', { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'capture-mcp', version: '1' } });
  mcp.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  trace.server = init.msg.result?.serverInfo;
  const listed = await rpc('tools/list', {});
  trace.tools = listed.msg.result.tools.map((t) => t.name);

  const run = async (tool, args, summarize) => {
    const { msg, ms } = await rpc('tools/call', { name: tool, arguments: args });
    const data = parse(msg);
    const entry = { index: trace.calls.length + 1, tool, arguments: args, elapsed_ms: Math.round(ms * 10) / 10, is_error: !!msg.result?.isError || !!msg.error, result: data ?? text(msg) };
    entry.summary = summarize(data);
    trace.calls.push(entry);
    if (entry.is_error) throw new Error(`${tool} failed: ${text(msg).slice(0, 200)}`);
    return data;
  };
  const found = (key) => (d) => { const items = d?.[key] ?? d?.items ?? []; return { count: items.length, top: items.slice(0, 3).map((x) => ({ id: x.id, title: x.title, version: x.version, sections: x.sections?.length ?? x.spans?.length ?? undefined })) }; };

  await run('document_memory_status', {}, (d) => ({ keys: Object.keys(d ?? {}).slice(0, 6) }));
  const t1 = await run('document_template_search', { query: 'one-page project overview' }, found('templates'));
  const t2 = await run('document_template_search', { query: '10-slide pitch deck' }, found('templates'));
  const t3 = await run('document_template_search', { query: 'promo blog post' }, found('templates'));
  const src = await run('document_source_search', { query: 'My Document Memory' }, found('sources'));
  const pick = (d, title) => (d?.templates ?? d?.items ?? []).find((x) => x.title === title);
  const sOverview = pick(t1, fx.overview.title), sDeck = pick(t2, fx.deck.title), sBlog = pick(t3, fx.blog.title);
  if (!sOverview || !sDeck || !sBlog) {
    for (const c of trace.calls) console.error(`  ${c.tool} ${JSON.stringify(c.arguments)} -> ${JSON.stringify(c.summary)}`);
    console.error('raw template search 1:', JSON.stringify(t1).slice(0, 600));
    throw new Error('a search did not return its demo template as a hit: adjust the fixture wording');
  }
  const sourceId = (src?.sources ?? src?.items ?? []).find((x) => x.title === fx.source.title)?.id ?? fx.source.id;
  const created = (d) => ({ id: d?.id, title: d?.title, version: d?.version, family: d?.family, template: d?.template, sources: d?.source_versions?.map((s) => ({ id: s.source_id, version: s.version })), blocks: d?.content?.blocks?.length, slides: d?.content?.slides?.length });
  await run('document_memory_create', { title: 'My Document Memory - One-Page Overview', template_id: sOverview.id, source_ids: [sourceId], outline_approved: false }, created);
  await run('document_memory_create', { title: 'My Document Memory - Pitch Deck', template_id: sDeck.id, source_ids: [sourceId], outline_approved: true }, created);
  await run('document_memory_create', { title: 'My Document Memory - Promo Post', template_id: sBlog.id, source_ids: [sourceId], outline_approved: false }, created);
  trace.total_ms = Math.round(trace.calls.reduce((a, c) => a + c.elapsed_ms, 0) * 10) / 10;
  trace.ok = trace.calls.length === 8 && trace.calls.every((c) => !c.is_error) && trace.tools.length === 7;
  // Pinned versions really exist in the store: read the three documents back over HTTP.
  const docs = (await call(rt, '/v1/documents')).items ?? [];
  trace.readback = docs.map((d) => ({ id: d.id, title: d.title, version: d.version, family: d.family, template: { id: d.template.template_id, version: d.template.version }, sources: d.source_versions.map((s) => ({ id: s.source_id, version: s.version })) }));
} finally {
  mcp.stdin.end(); mcp.kill('SIGTERM');
  await rt.stop();
}

const outFull = path.join(repo, 'demo/out/footage/mcp-trace.json');
const outSummary = path.join(repo, 'demo/video/hackathon/data/mcp-trace.json');
mkdirSync(path.dirname(outFull), { recursive: true }); mkdirSync(path.dirname(outSummary), { recursive: true });
writeFileSync(outFull, JSON.stringify(trace, null, 1));
const summary = { about: trace.about, server: trace.server, tools: trace.tools, total_ms: trace.total_ms, ok: trace.ok, fixtures: trace.fixtures, calls: trace.calls.map((c) => ({ index: c.index, tool: c.tool, arguments: c.arguments, elapsed_ms: c.elapsed_ms, is_error: c.is_error, summary: c.summary })), readback: trace.readback };
writeFileSync(outSummary, JSON.stringify(summary, null, 1));
console.log(`mcp trace: ${trace.calls.length} calls, ${trace.tools.length} tools, total ${trace.total_ms} ms, ok=${trace.ok}`);
for (const c of trace.calls) console.log(`  ${String(c.index).padStart(2)} ${c.tool.padEnd(26)} ${String(c.elapsed_ms).padStart(7)} ms  ${JSON.stringify(c.summary).slice(0, 150)}`);
process.exitCode = trace.ok ? 0 : 1;
