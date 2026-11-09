'use strict';
// Hackathon cut, 90 s. Spec and claims ledger: docs/demo/hackathon-90s.md. Every scene is a pure function of time.
// What is real is labelled REAL (RUN / APP / MCP); everything drawn is labelled ILLUSTRATION; the arithmetic is labelled WHAT-IF.
window.__SCRIPT_URL = '/demo/video/hackathon/script.json';
window.__BADGES = {
  illus: { cls: 'illus', text: () => 'ILLUSTRATION' },
  grid: { cls: 'illus', text: () => 'ILLUSTRATION · FOUR WINDOWS' },
  real: { cls: '', text: () => 'REAL APP · SPED UP' },
  whatif: { cls: 'whatif', text: () => 'WHAT-IF · NOT MEASURED' }
};

const STEPS = ['Find a format', 'Plan the outline', 'Gather sources', 'Fix the style', 'Explain it to your AI'];
const COMMAND = 'In Google Docs, write a one-page overview of this project. In Google Slides, build a 10-slide deck. Then go to Naver Blog and write a post that promotes it.';
const HEAD1 = 'Every document starts from zero.';
let FT = null;      // footage placement (script.json)
let TRACE = null;   // real MCP trace summary (data/mcp-trace.json)

// ── small helpers ──
const makePane = (parent, x, y, w, h, title, tag, tagCls = '') => {
  const root = A(parent, `left:${x}px;top:${y}px;width:${w}px;height:${h}px;`, '', 'pane');
  A(root, '', `<i></i><i></i><i></i><span class="ptitle">${title}</span><span class="pstatus chip" style="opacity:0"></span><span class="ptag chip ${tagCls}">${tag}</span>`, 'pbar');
  const body = A(root, 'top:34px;', '', 'pbody');
  return { root, body, status: root.querySelector('.pstatus'), tag: root.querySelector('.ptag') };
};
const setStatus = (p, text, cls = '') => {
  if (p.status.textContent !== text) p.status.textContent = text;
  const c = `pstatus chip ${cls}`; if (p.status.className !== c) p.status.className = c;
  p.status.style.opacity = text ? 1 : 0;
};
const setText = (e, s) => { if (e.textContent !== s) e.textContent = s; };
const blinkOf = (t) => (Math.floor(t * 2.6) % 2 ? '▍' : ' ');
// Sequential typing windows for [{el, text}] between t0 and t1, proportional to length. Returns [{el,text,a,b}].
const schedule = (items, t0, t1) => {
  const total = items.reduce((n, i) => n + i.text.length, 0); let at = t0;
  return items.map((i) => { const d = (t1 - t0) * i.text.length / total; const r = { ...i, a: at, b: at + d }; at += d; return r; });
};
const runTyping = (plan, lt) => {
  const live = plan.find((p) => lt >= p.a && lt < p.b);
  plan.forEach((p) => { setText(p.el, typed(p.text, seg(lt, p.a, p.b)) + (p === live ? blinkOf(lt) : '')); });
};
const lineRows = (log, rows) => rows.map((r) => ({ ...r, el: A(log, `top:${10 + r.i * 24}px;`, `<b>›</b>${r.text}`, 'll') }));

// ── 1 · problem (light, illustration) ──
function buildProblem() {
  const s = addScene('problem', { badge: 'illus' });
  const head = A(s, 'left:80px;top:104px;font-size:100px;white-space:nowrap;', '', 'h');
  const row = A(s, 'left:0;top:300px;width:1920px;height:104px;display:flex;justify-content:center;gap:22px;');
  const cards = STEPS.map((txt, i) => {
    const hot = i === 4;
    const c = el('div', 'card', `<span class="mono" style="display:inline-flex;width:42px;height:42px;border-radius:50%;background:${hot ? '#e0714f' : 'var(--green)'};color:#fff;align-items:center;justify-content:center;font-size:20px;font-weight:500;margin-right:14px">${i + 1}</span><span class="h" style="font-size:26px;letter-spacing:-.02em;white-space:nowrap">${txt}</span>`, row,
      `position:relative;display:flex;align-items:center;height:104px;padding:0 26px;border-radius:24px;${hot ? 'border-color:#f0bfae;background:#fff3ee;' : ''}`);
    return c;
  });
  const again = el('span', 'chip coral', 'AGAIN', cards[4], 'position:absolute;right:16px;top:-17px;font-size:17px;padding:3px 14px;');
  const arrow = A(s, 'left:0;top:408px;width:1920px;height:120px;', '<svg width="1920" height="120" viewBox="0 0 1920 120"><path id="loop" d="" fill="none" stroke="#e0714f" stroke-width="4" stroke-linecap="round" stroke-dasharray="1" pathLength="1" stroke-dashoffset="1"/><path id="loophead" d="" fill="#e0714f"/></svg>');
  const loop = arrow.querySelector('#loop'), loopHead = arrow.querySelector('#loophead');
  const againTxt = A(s, 'left:0;top:496px;width:1920px;text-align:center;font-size:22px;color:#a8442a;letter-spacing:.14em;', 'THE SAME SETUP, EVERY TIME', 'mono');
  const defs = [
    { x: 70, label: 'Report', build: (c) => { A(c, 'left:30px;top:84px;right:30px;bottom:30px;background:#fff;border:2px solid #e3e8dd;border-radius:8px;');
      const t = A(c, 'left:52px;top:112px;font-size:30px;color:#b2bdb4;white-space:nowrap;', 'Untitled document', 'h');
      A(c, 'left:52px;top:176px;width:420px;height:12px;border-radius:6px;background:#eef1ea;'); A(c, 'left:52px;top:206px;width:360px;height:12px;border-radius:6px;background:#eef1ea;'); return t; } },
    { x: 690, label: 'Deck', build: (c) => { A(c, 'left:30px;top:84px;right:30px;bottom:30px;background:#e8eee4;border:2px solid #d3dccb;border-radius:8px;');
      const t = A(c, 'left:0;top:150px;width:540px;text-align:center;font-size:30px;color:#a7b3a9;white-space:nowrap;', 'Click to add title', 'h');
      A(c, 'left:0;top:206px;width:540px;text-align:center;font-size:20px;color:#b5c0b6;white-space:nowrap;', 'Click to add subtitle'); return t; } },
    { x: 1310, label: 'Blog post', build: (c) => { A(c, 'left:30px;top:84px;right:30px;bottom:30px;background:#fff;border:2px solid #e3e8dd;border-radius:8px;');
      const t = A(c, 'left:52px;top:112px;font-size:34px;color:#b2bdb4;white-space:nowrap;', 'Title', 'h');
      A(c, 'left:52px;top:184px;font-size:22px;color:#b9c3bb;white-space:nowrap;', 'Tell your story…'); return t; } }
  ];
  const blanks = defs.map((d) => {
    const c = A(s, `left:${d.x}px;top:540px;width:540px;height:350px;`, '', 'card');
    A(c, 'left:30px;top:22px;', `<span class="chip ghost" style="font-size:18px;padding:3px 14px">${d.label}</span>`);
    return { c, ph: d.build(c) };
  });
  const caret = A(s, 'left:0;top:0;width:3px;height:34px;background:var(--green);');
  const T = [5.0, 6.3, 7.6, 8.9, 10.6];
  s.update = (lt) => {
    setText(head, typed(HEAD1, seg(lt, 0.6, 2.9)));
    cards.forEach((c, i) => show(c, fade(lt, T[i], T[i] + 0.55), 22));
    show(again, fade(lt, T[4] + 0.5, T[4] + 1.0), -6);
    const p = seg(lt, 11.3, 12.9);
    const r5 = cards[4].getBoundingClientRect(), r1 = cards[0].getBoundingClientRect();
    if (r5.width && r1.width) {
      const x5 = r5.left + r5.width / 2, x1 = r1.left + r1.width / 2, y0 = r5.bottom - 408 + 10, yb = y0 + 44;
      loop.setAttribute('d', `M${x5} ${y0} V${yb - 18} Q${x5} ${yb} ${x5 - 18} ${yb} H${x1 + 18} Q${x1} ${yb} ${x1} ${yb - 18} V${y0 + 10}`);
      loop.setAttribute('stroke-dashoffset', String(1 - p));
      loopHead.setAttribute('d', `M${x1 - 12} ${y0 + 14} L${x1} ${y0 - 4} L${x1 + 12} ${y0 + 14} Z`);
      loopHead.style.opacity = p > 0.97 ? 1 : 0;
    }
    againTxt.style.opacity = fade(lt, 12.4, 13.0);
    blanks.forEach((b, i) => show(b.c, fade(lt, 1.3 + i * 0.25, 1.9 + i * 0.25), 26));
    // a caret blinks at the start of the first blank page
    const pr = blanks[0].ph.getBoundingClientRect();
    caret.style.left = `${pr.left - 8}px`; caret.style.top = `${pr.top - 2 - 0}px`; caret.style.opacity = (pr.width ? (Math.floor(lt * 2) % 2 ? 0 : 1) : 0) * fade(lt, 1.8, 2.2);
  };
}

// ── 2 · command (dark, illustration) ──
function buildCommand() {
  const s = addScene('command', { badge: 'illus' });
  const win = makePane(s, 330, 104, 1260, 790, 'Arise Browser · agent chat', 'ILLUSTRATION');
  win.root.style.background = '#faf9f4';
  const chat = A(win.body, 'left:0;right:0;top:0;bottom:178px;');
  const bubbleUser = A(chat, 'right:40px;top:30px;width:1000px;padding:22px 28px;border-radius:22px 22px 6px 22px;background:#e3efc9;color:#13261f;font-size:25px;line-height:1.45;', COMMAND);
  bubbleUser.setAttribute('data-box', '');
  const youLbl = A(chat, 'right:44px;top:6px;font-size:14px;color:#6a7d72;letter-spacing:.14em;', 'YOU', 'mono');
  const hello = A(chat, 'left:40px;top:34px;font-size:26px;color:#6a7d72;white-space:nowrap;', 'Ready when you are. What should we make?');
  const agentLbl = A(chat, 'left:40px;top:262px;font-size:14px;color:#6a7d72;letter-spacing:.14em;', 'AGENT', 'mono');
  const planRow = A(chat, 'left:40px;top:290px;display:flex;gap:14px;');
  const plan = ['Google Docs · one page', 'Google Slides · 10 slides', 'Naver Blog · promo post'].map((t, i) => el('span', 'chip lime', `${i + 1} · ${t}`, planRow, 'font-size:20px;padding:6px 18px;background:#e3efc9;border-color:#bfd95a;color:#13261f;'));
  const ask = A(chat, 'left:40px;top:358px;font-size:25px;color:#13261f;white-space:nowrap;', 'Before writing, ask Document Memory first:');
  const queries = ['one-page project overview', '10-slide pitch deck', 'promo blog post'];
  const calls = queries.map((q, i) => A(chat, `left:40px;top:${406 + i * 44}px;font-size:19px;color:#254b3c;white-space:nowrap;`, `<span style="color:#7fa02a">▸</span> document_template_search <span style="color:#6a7d72">“${q}”</span>`, 'mono'));
  const inputBox = A(win.body, 'left:36px;right:36px;bottom:26px;height:132px;border-radius:20px;background:#fff;border:2px solid #cfd8c8;');
  inputBox.setAttribute('data-box', '');
  const typedEl = A(inputBox, 'left:26px;top:18px;width:960px;font-size:25px;line-height:1.45;color:#13261f;', '');
  const ph = A(inputBox, 'left:26px;top:18px;font-size:25px;color:#a2afa6;white-space:nowrap;', 'Message the agent…');
  const send = A(inputBox, 'right:20px;bottom:18px;', '<span class="btn" style="font-size:22px;padding:8px 26px;">Send ↵</span>');
  const sendBtn = send.firstChild;
  s.update = (lt) => {
    const p = seg(lt, 0.6, 7.4), sent = lt >= 7.8;
    setText(typedEl, sent ? '' : typed(COMMAND, p) + (p > 0 && p < 1 ? blinkOf(lt) : ''));
    ph.style.opacity = sent || p > 0 ? 0 : 1;
    press(sendBtn, lt, 7.5, 0.4);
    hello.style.opacity = fade(lt, 0.3, 0.9) * (1 - fade(lt, 7.1, 7.6));
    show(bubbleUser, fade(lt, 7.9, 8.5), 18); youLbl.style.opacity = fade(lt, 7.9, 8.5);
    agentLbl.style.opacity = fade(lt, 8.5, 9.0);
    plan.forEach((c, i) => show(c, fade(lt, 8.6 + i * 0.4, 9.2 + i * 0.4), 10));
    show(ask, fade(lt, 10.0, 10.6), 8);
    calls.forEach((c, i) => show(c, fade(lt, 10.5 + i * 0.6, 11.0 + i * 0.6), 8));
  };
}

// ── 3 · four windows (dark): Docs (drawn) · Slides (REAL run) · Blog (drawn) · Document Memory (REAL MCP trace + REAL app) ──
function buildAgents() {
  const s = addScene('agents', { badge: 'grid' });
  const sl = FT.slides, ma = FT.memory_app;
  const docs = makePane(s, 60, 100, 888, 400, 'Google Docs · one-page overview', 'ILLUSTRATION');
  const slides = makePane(s, 972, 100, 888, 400, 'Google Slides · 10-slide deck', `REAL RUN · EARLIER PROJECT · ×${sl.speed}`, 'lime');
  const blog = makePane(s, 60, 516, 888, 400, 'Naver Blog · promo post', 'ILLUSTRATION');
  const mem = makePane(s, 972, 516, 888, 400, 'Document Memory · MCP + app', 'REAL · MCP + APP', 'lime');
  const panes = [docs, slides, blog, mem];

  // Docs (drawn): agent log + page
  const dLog = A(docs.body, '', '', 'plog');
  const dRows = lineRows(dLog, ['ask Document Memory', 'got: One-Page Overview', 'got: project notes', 'open Google Docs', 'type title', 'type · Purpose', 'type · The Problem', 'type · How It Works', 'type · What Runs Today', "type · What's Next", 'flag · launch date', 'ready for review'].map((text, i) => ({ i, text })));
  const dDoc = A(docs.body, 'left:230px;right:0;top:0;bottom:0;background:#e6ebf0;');
  A(dDoc, '', '<u style="left:14px;width:40px"></u><u style="left:62px;width:26px"></u><u style="left:96px;width:26px"></u><u style="left:130px;width:60px"></u><u style="left:198px;width:26px"></u>', 'tbstrip');
  const dSheet = A(dDoc, 'left:46px;top:30px;width:566px;height:330px;', '', 'sheet');
  const DOC = [['My Document Memory: Project Overview', null],
    ['Purpose', 'Helps people share how documents are made, so anyone can create the document they need with AI.'],
    ['The Problem', 'Every document starts from zero: find a format, plan the outline, gather sources, fix the style, then explain it all to an AI again.'],
    ['How It Works', 'Templates, references and finished documents are stored separately. An AI host searches them over MCP and creates an editable draft.'],
    ['What Runs Today', 'A Rust API with SQLite, a web app, a dmem command line and an MCP server with seven tools. Exports: DOCX, PPTX, Markdown, HTML.'],
    ["What's Next", 'Publishing templates for others and team libraries. Public launch date: [needs confirmation]']];
  const dItems = [];
  DOC.forEach(([h, p], i) => {
    if (i === 0) dItems.push({ el: A(dSheet, 'top:14px;font-size:17px;font-weight:800;color:#14222d;', '', 't'), text: h, row: 4 });
    else {
      const top = 44 + (i - 1) * 57;
      dItems.push({ el: A(dSheet, `top:${top}px;`, '', 'hd'), text: h, row: 4 + i });
      dItems.push({ el: A(dSheet, `top:${top + 18}px;height:34px;`, '', 'p'), text: p });
    }
  });
  const dPlan = schedule(dItems, 14.4, 30.0);
  const dHeads = dPlan.filter((i) => i.row);
  const dRowAt = [5.5, 12.9, 13.3, 13.8, ...dHeads.map((i) => i.a), dPlan[dPlan.length - 1].b - 1.2, 30.6];   // ask, got, got, open, type×6, flag, ready

  // Blog (drawn)
  const bLog = A(blog.body, '', '', 'plog');
  const bRows = lineRows(bLog, ['ask Document Memory', 'got: Promo Blog Post', 'got: project notes', 'open Naver Blog', 'type title', 'type · Hook', 'type · What It Does', 'type · How It Works', 'add tags', 'ready for review'].map((text, i) => ({ i, text })));
  const bDoc = A(blog.body, 'left:230px;right:0;top:0;bottom:0;background:#eaefec;');
  A(bDoc, '', '<span class="abs mono" style="left:14px;top:5px;font-size:11px;color:#5d7367;white-space:nowrap">Naver Blog · new post</span>', 'tbstrip');
  const bSheet = A(bDoc, 'left:46px;top:30px;width:566px;height:330px;', '', 'sheet');
  const BLOG = [['Stop starting every document from zero', 't'],
    ['Reports, decks, posts: every one begins with the same chores. Find a format. Plan the outline. Gather sources. Fix the style.', 'p', 154],
    ['My Document Memory keeps your templates, references and finished documents, so your AI starts from a good structure instead of a blank page.', 'p', 202],
    ['It flags anything it cannot confirm, links claims back to their source, and exports to DOCX, PPTX, Markdown or HTML.', 'p', 250],
    ['#DocumentMemory  #AIWriting  #Templates', 'g', 298]];
  A(bSheet, 'left:34px;right:30px;top:62px;height:76px;background:#dde5e0;border-radius:6px;', '<svg viewBox="0 0 120 40" width="120" height="40" style="position:absolute;left:223px;top:18px"><path d="M4 34 L34 8 L56 26 L72 14 L116 34 Z" fill="#b9c8be"/><circle cx="92" cy="9" r="5" fill="#cbd8ce"/></svg>');
  const bItems = BLOG.map(([text, kind, top]) => ({ text, el: kind === 't' ? A(bSheet, 'top:20px;font-size:20px;font-weight:800;color:#14222d;', '', 't') : A(bSheet, `top:${top}px;${kind === 'g' ? 'font-size:12px;color:#2a7a52;font-weight:700;' : 'height:34px;'}`, '', kind === 'g' ? 'p' : 'p') }));
  const bPlan = schedule(bItems, 16.6, 30.6);
  const bRowAt = [5.8, 15.2, 15.6, 16.0, bPlan[0].a, bPlan[1].a, bPlan[2].a, bPlan[3].a, bPlan[4].a, 31.2];   // ask, got, got, open, title, Hook, What It Does, How It Works, tags, ready

  // Slides (REAL run): a hole where the clip goes; the clip itself is composited by build.mjs
  A(slides.body, 'left:20px;top:0;width:848px;height:366px;', '', 'hole');
  window.__overlays.push({ id: 'slides-real-run', file: sl.file, x: 992, y: 134, w: 848, h: 366, from: sl.from, to: 62, hold: true });

  // Document Memory: the REAL MCP trace (left) and the REAL app (right, composited)
  const mLog = A(mem.body, '', '', 'plog'); mLog.style.width = '330px';
  const mRowT = [5.6, 6.4, 7.2, 8.0, 8.8, 12.4, 13.6, 14.8];
  const mRows = TRACE.calls.map((c, i) => {
    const q = c.arguments.query ? `“${c.arguments.query}”` : null;
    const detail = c.tool === 'document_memory_status' ? 'supported formats and vocabulary'
      : c.tool === 'document_memory_create' ? 'pinned: template v1 · reference v1'
      : `${q} · ${c.summary.count} match`;
    const ms = c.elapsed_ms < 10 ? c.elapsed_ms.toFixed(1) : String(Math.round(c.elapsed_ms));
    return { c, e: A(mLog, `top:${6 + i * 40}px;`, `<span class="tk">✓</span><span class="tn">${c.tool}</span><span class="tm">${ms} ms</span><span class="td">${detail}</span>`, 'trow') };
  });
  A(mem.body, 'left:336px;top:0;width:546px;height:366px;', '', 'hole');
  window.__overlays.push({ id: 'memory-real-app', file: ma.file, src: { from: ma.src_from }, speed: ma.speed, crop: { x: 240, y: 95, w: 1200, h: 805 }, x: 1308, y: 550, w: 546, h: 366, from: ma.from, to: 62, hold: true });
  const memTotal = `${TRACE.calls.length} calls · ${Math.round(TRACE.total_ms)} ms`;

  s.update = (lt) => {
    panes.forEach((p, i) => show(p.root, fade(lt, i * 0.15, 0.7 + i * 0.15), 26));
    // agent logs
    dRows.forEach((r, i) => { r.el.style.opacity = fade(lt, dRowAt[i], dRowAt[i] + 0.3); });
    bRows.forEach((r, i) => { r.el.style.opacity = fade(lt, bRowAt[i], bRowAt[i] + 0.3); });
    // typing
    runTyping(dPlan, lt); runTyping(bPlan, lt);
    // trace rows
    mRows.forEach((r, i) => { show(r.e, fade(lt, mRowT[i], mRowT[i] + 0.35), 6); });
    // statuses
    const working = (p, from, doneAt, doneText) => (lt < from ? setStatus(p, '') : lt < doneAt ? setStatus(p, '● WORKING', 'amber') : setStatus(p, doneText, 'lime'));
    working(docs, 1.0, 30.4, '✓ READY FOR REVIEW');
    working(slides, 1.4, 32.3, '✓ 10 / 10 SLIDES');
    working(blog, 1.2, 31.0, '✓ READY FOR REVIEW');
    (lt < 5.0 ? setStatus(mem, '') : lt < 15.6 ? setStatus(mem, '● ANSWERING', 'amber') : setStatus(mem, `✓ ${memTotal}`, 'lime'));
  };
}

// ── 4 · share (light): the REAL app, sped up ──
function buildShare() {
  const s = addScene('share', { badge: 'real' });
  const a = FT.share_public, b = FT.share_copy;
  const win = makePane(s, 70, 110, 1120, 734, 'My Document Memory · web app', `REAL APP · SCRIPTED CLICKS · ×${a.speed}`, 'lime');
  win.root.style.background = '#0b1814';
  A(win.body, 'left:0;top:0;width:1120px;height:700px;', '', 'hole');
  window.__overlays.push({ id: 'share-public', file: a.file, src: { from: a.src_from }, speed: a.speed, x: 70, y: 144, w: 1120, h: 700, from: a.from, to: b.from, hold: true });
  window.__overlays.push({ id: 'share-copy', file: b.file, src: { from: b.src_from }, speed: b.speed, x: 70, y: 144, w: 1120, h: 700, from: b.from, to: 75, hold: true });
  const X = 1230, W = 620;
  const cA = A(s, `left:${X}px;top:120px;width:${W}px;height:232px;`, '', 'card');
  A(cA, 'left:30px;top:22px;', 'SHARED LIBRARY', 'label');
  A(cA, 'left:30px;top:54px;width:560px;font-size:31px;line-height:1.18;', 'Credit travels with every template.', 'h');
  const att = A(cA, 'left:30px;top:142px;width:560px;height:68px;border-radius:14px;background:#f1f5ea;border:2px solid #dbe5cf;');
  A(att, 'left:18px;top:8px;font-size:22px;font-weight:700;white-space:nowrap;', 'Startup Pitch Deck');
  A(att, 'left:18px;top:38px;font-size:16px;color:#4f6a58;white-space:nowrap;', 'My Document Memory · v1 · CC0-1.0', 'mono');
  const cB = A(s, `left:${X}px;top:372px;width:${W}px;height:210px;`, '', 'card');
  A(cB, 'left:30px;top:22px;', 'COPY, KEEP THE CREDIT', 'label');
  A(cB, 'left:30px;top:60px;display:flex;align-items:center;gap:18px;', '<span class="chip">Public template</span><span class="h" style="font-size:30px;color:#254b3c">→</span><span class="chip lime">My template</span>');
  A(cB, 'left:30px;top:132px;width:560px;font-size:17px;line-height:1.5;color:#4f6a58;', 'Original: My Document Memory · v1 · CC0-1.0<br>The copy is yours to edit. The credit stays.', 'mono');
  const cC = A(s, `left:${X}px;top:602px;width:${W}px;height:242px;`, '', 'card');
  A(cC, 'left:30px;top:22px;', 'WHERE THIS STANDS', 'label');
  A(cC, 'left:30px;top:66px;', '<span class="chip lime">TODAY</span>');
  A(cC, 'left:150px;top:68px;font-size:24px;white-space:nowrap;', 'Built-in catalog you can copy');
  A(cC, 'left:30px;top:132px;', '<span class="chip amber">PLANNED</span>');
  A(cC, 'left:190px;top:134px;font-size:24px;white-space:nowrap;', 'Share with other people');
  const tagTxt = win.tag;
  s.update = (lt) => {
    show(cA, fade(lt, 1.0, 1.6), 18); show(cB, fade(lt, 7.6, 8.2), 18); show(cC, fade(lt, 9.6, 10.2), 18);
    setText(tagTxt, `REAL APP · SCRIPTED CLICKS · ×${lt + 62 < b.from ? a.speed : b.speed}`);
    setStatus(win, '');
  };
}

// ── 5 · saved (dark): what-if arithmetic, labelled ──
function buildSaved() {
  const s = addScene('saved', { badge: 'whatif' });
  const L = ledgerValues();
  A(s, 'left:80px;top:150px;', 'SETUP YOU SKIP', 'label');
  const rows = STEPS.map((t, i) => A(s, `left:80px;top:${204 + i * 92}px;display:flex;align-items:center;gap:20px;white-space:nowrap;`, `${icon('check', 46)}<span class="h" style="font-size:33px;letter-spacing:-.02em;color:#9db5a6;text-decoration:line-through;text-decoration-thickness:3px">${t}</span>`));
  const eq = (left, top, w, big, cap, cls = '') => A(s, `left:${left}px;top:${top}px;width:${w}px;`, `<div class="h ${cls}" style="font-size:92px;white-space:nowrap">${big}</div><div class="muted" style="font-size:24px;white-space:nowrap;margin-top:20px">${cap}</div>`);
  const b1 = eq(830, 132, 250, `${L.minutes}`, 'minutes per reuse');
  const op1 = A(s, 'left:1086px;top:140px;font-size:84px;color:#9fb7a6;', '×', 'h');
  const b2 = eq(1160, 132, 330, L.reusesText, 'reuses');
  const op2 = A(s, 'left:1490px;top:140px;font-size:84px;color:#9fb7a6;', '=', 'h');
  const b3 = eq(1556, 132, 304, '', 'hours', '');
  const hoursEl = b3.firstChild; hoursEl.style.color = 'var(--lime)';
  const chipW = A(s, 'left:830px;top:340px;', '<span class="chip amber" style="font-size:26px;padding:8px 22px">WHAT-IF · NOT A MEASUREMENT</span>');
  const foot = A(s, 'left:830px;top:404px;font-size:21px;color:#b9cabb;white-space:nowrap;', `Assumption: ${L.minutes} minutes saved per reuse. ${L.minutes} × ${L.reusesText} = ${L.totalMinutesText} min ≈ ${L.hours} h.`, 'mono');
  A(s, 'left:850px;top:462px;', 'ONE DOT = ONE REUSE', 'label');
  const grid = A(s, 'left:850px;top:494px;width:960px;height:400px;');
  const dots = []; for (let i = 0; i < 1000; i++) { const r = Math.floor(i / 40), c = i % 40; dots.push(A(grid, `left:${c * 24}px;top:${r * 16}px;width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.14);`)); }
  let lit = 0;
  s.update = (lt) => {
    rows.forEach((r, i) => show(r, fade(lt, 0.7 + i * 0.4, 1.2 + i * 0.4), 14, -10));
    show(b1, fade(lt, 3.5, 4.1), 14); show(op1, fade(lt, 5.3, 5.8), 0); show(b2, fade(lt, 5.5, 6.1), 14);
    show(op2, fade(lt, 7.3, 7.8), 0); show(b3, fade(lt, 7.5, 8.1), 14);
    setText(hoursEl, `≈ ${Math.round(L.hours * ease(seg(lt, 7.7, 9.6)))}`);
    show(chipW, fade(lt, 3.3, 3.9), 10); foot.style.opacity = fade(lt, 8.6, 9.2);
    const n = Math.round(1000 * ease(seg(lt, 5.6, 8.4)));
    if (n !== lit) { const lo = Math.min(n, lit), hi = Math.max(n, lit); for (let i = lo; i < hi; i++) dots[i].style.background = i < n ? 'var(--lime)' : 'rgba(255,255,255,.14)'; lit = n; }
  };
}
function ledgerValues() {
  const l = SCRIPT.ledger, total = l.whatif_minutes * l.whatif_reuses;
  return { minutes: l.whatif_minutes, reusesText: l.whatif_reuses.toLocaleString('en-US'), totalMinutesText: total.toLocaleString('en-US'), hours: l.whatif_hours };
}

// ── 6 · close (dark) ──
function buildClose() {
  const s = addScene('close', { badge: null, chrome: false });
  A(s, 'left:0;top:236px;width:1920px;text-align:center;', `<span class="biglogo ic" style="width:150px;height:150px">${logoSvg}</span>`);
  A(s, 'left:0;top:416px;width:1920px;text-align:center;font-size:84px;', 'my document memory', 'h');
  const tag = A(s, 'left:0;top:540px;width:1920px;text-align:center;font-size:66px;color:var(--lime);', 'Share the memory. Save the time.', 'h');
  const cred = A(s, 'left:210px;top:730px;width:1500px;text-align:center;font:400 19px/1.6 var(--mono);color:#9fb7a6;', 'Product screens: the real app, driven by scripted clicks. Slides window: a real agent run from an earlier project. Windows marked ILLUSTRATION are drawings.');
  s.update = (lt) => { show(tag, fade(lt, 0.5, 1.2), 14); cred.style.opacity = fade(lt, 1.2, 1.9) * 0.9; };
}

window.__buildScenes = async () => {
  FT = SCRIPT.footage;
  TRACE = await fetch('/demo/video/hackathon/data/mcp-trace.json').then((r) => r.json());
  buildProblem(); buildCommand(); buildAgents(); buildShare(); buildSaved(); buildClose();
};
