'use strict';
// S6 create in your form (spec §2 steps 6–7 and §6): new-document dialog → three-panel editor (forms/references on the left,
// document in the middle, form/rules/sources/to-confirm on the right) → deck outline approval → slides.
// A concept drawing with sample data, not a recording.

function buildS6() {
  const s = addScene('s6', { badge: 'concept' });
  const esc = (x) => x.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const title = A(s, 'left:100px;top:100px;font-size:60px;white-space:nowrap;', tr('양식대로 만듭니다.', 'Create in your form.'), 'h');
  const win = A(s, 'left:100px;top:186px;width:1720px;height:720px;overflow:hidden;', '', 'card');

  // top bar
  const bar = A(win, 'left:0;top:0;width:100%;height:54px;border-bottom:2px solid var(--line);background:#fbfaf4;');
  A(bar, 'left:18px;top:9px;width:34px;height:34px;', `<span class="ic" style="width:34px;height:34px">${logoSvg}</span>`);
  A(bar, 'left:66px;top:10px;font-size:26px;white-space:nowrap;', tr('4분기 보고서', 'Q4 report'), 'h');
  A(bar, 'left:268px;top:12px;', chip(tr('초안', 'Draft'), 'ghost', 'font-size:18px;padding:2px 12px'));
  const tabDoc = A(bar, 'left:700px;top:9px;', chip(tr('문서', 'Document'), 'lime', 'font-size:20px;padding:4px 18px'));
  const tabDeck = A(bar, 'left:830px;top:9px;', chip(tr('발표 자료', 'Deck'), 'ghost', 'font-size:20px;padding:4px 18px'));
  A(bar, 'left:1380px;top:9px;', `<span class="btn ghost" style="font-size:20px;padding:4px 18px">${tr('버전', 'Versions')}</span>`);
  A(bar, 'left:1520px;top:9px;', `<span class="btn" style="font-size:20px;padding:4px 18px">${tr('내보내기 ▾', 'Export ▾')}</span>`);

  // left panel: libraries
  const lp = A(win, 'left:0;top:54px;width:290px;height:664px;background:#f6f7f0;border-right:2px solid var(--line);');
  const item = (y, txt, sel) => { const e = A(lp, `left:12px;top:${y}px;width:264px;height:34px;line-height:34px;padding-left:12px;border-radius:8px;font-size:19px;white-space:nowrap;`, txt); e.setAttribute('data-box', ''); if (sel) e.style.background = '#e1efb0'; return e; };
  const gl = (y, txt) => A(lp, `left:16px;top:${y}px;`, txt, 'label');
  gl(18, tr('내 양식', 'MY FORMS'));
  const itemQ = item(46, tr('분기 보고서 v1', 'Quarterly report v1'), true);
  item(84, tr('회의록 v1', 'Meeting minutes v1'));
  const itemDeck = item(122, tr('스타트업 피치덱 v3', 'Startup pitch deck v3'));
  gl(180, tr('공유 양식', 'SHARED FORMS')); item(208, tr('주간 업무보고', 'Weekly report')); item(246, tr('사업 제안서', 'Business proposal'));
  gl(308, tr('참고자료', 'REFERENCES')); item(336, 'q3-report.pdf'); item(374, 'sales-notes.md');
  gl(436, tr('최근 문서', 'RECENT')); item(464, tr('3분기 보고서', 'Q3 report'));

  // right panel: form, rules, sources, to confirm
  const rp = A(win, 'left:1150px;top:54px;width:566px;height:664px;background:#fbfaf4;border-left:2px solid var(--line);');
  const rl = (y, txt, css = '') => A(rp, `left:24px;top:${y}px;${css}`, txt, 'label');
  rl(20, tr('양식', 'FORM'));
  const formVal = A(rp, 'left:24px;top:46px;font-size:27px;font-weight:800;white-space:nowrap;', '');
  const formSub = A(rp, 'left:24px;top:84px;font-size:20px;white-space:nowrap;', '', 'muted');
  rl(134, tr('작성 규칙', 'WRITING RULES'));
  A(rp, 'left:24px;top:160px;font-size:24px;font-weight:700;white-space:nowrap;', tr('쉽고 짧은 문장 · v1', 'Plain, short sentences · v1'));
  rl(226, tr('출처', 'SOURCES'));
  const src1 = A(rp, 'left:24px;top:254px;font-size:22px;white-space:nowrap;', '<span class="src">[1]</span> q3-report.pdf · p.4 · ¶2');
  const src2 = A(rp, 'left:24px;top:294px;font-size:22px;white-space:nowrap;', '<span class="src">[2]</span> sales-notes.md · §2');
  const tcLabel = rl(372, tr('확인 필요', 'TO CONFIRM'), 'color:#a8442a;');
  const tcBox = A(rp, 'left:24px;top:400px;width:518px;height:100px;border:2px dashed #e0714f;border-radius:16px;background:#fdf1ec;',
    `${icon('warn', 40, 'position:absolute;left:20px;top:26px')}<div class="tcName" style="position:absolute;left:78px;top:14px;font-size:26px;font-weight:800;color:#a8442a;white-space:nowrap"></div><div class="muted" style="position:absolute;left:78px;top:56px;font-size:19px;white-space:nowrap">${tr('참고자료에 없습니다', 'Not in your references')}</div>`);
  tcBox.setAttribute('data-box', '');
  const tcName = tcBox.querySelector('.tcName');

  // document view
  const docView = A(win, 'left:290px;top:54px;width:860px;height:664px;background:#eceee5;');
  const paper = A(docView, 'left:50px;top:22px;width:760px;height:620px;background:#fff;border:2px solid var(--line);border-radius:6px;box-shadow:0 10px 30px rgba(19,47,40,.10);');
  paper.setAttribute('data-box', '');
  const mk = (css, html, cls) => A(paper, css, html, cls);
  const head = (top, txt) => ({ h: mk(`left:44px;top:${top}px;font-size:26px;font-weight:800;color:var(--green);white-space:nowrap;`, txt), g: mk(`left:12px;top:${top + 2}px;font-size:18px;color:#a9b8ae;`, '⋮⋮', 'mono') });
  const eTitle = mk('left:44px;top:28px;font-size:36px;white-space:nowrap;', '', 'h');
  const hSum = head(96, tr('요약', 'Summary')), hMet = head(214, tr('주요 지표', 'Key metrics')), hRisk = head(366, tr('위험', 'Risks')), hReq = head(486, tr('요청', 'Requests'));
  const line = (top) => mk(`left:44px;top:${top}px;font-size:22px;white-space:nowrap;`, '');
  const l1 = line(136), l2 = line(168), r1 = line(406), r2 = line(438), q1 = line(526);
  const tbl = mk('left:44px;top:254px;width:672px;height:92px;border:2px solid var(--line);border-radius:8px;overflow:hidden;');
  tbl.setAttribute('data-box', '');
  A(tbl, 'left:0;top:0;width:100%;height:34px;background:#f3f6ec;');
  [180, 360].forEach((x) => A(tbl, `left:${x}px;top:0;width:2px;height:100%;background:var(--line);`));
  const th = tr(['가입자', '활성화율', '매출'], ['SIGNUPS', 'ACTIVATION', 'REVENUE']);
  [0, 180, 360].forEach((x, i) => A(tbl, `left:${x + 14}px;top:7px;font-size:15px;white-space:nowrap;`, th[i], 'mono muted'));
  const v1 = A(tbl, 'left:14px;top:42px;font-size:28px;font-weight:800;white-space:nowrap;', '');
  const v2 = A(tbl, 'left:194px;top:42px;font-size:28px;font-weight:800;white-space:nowrap;', '');
  const ph = A(tbl, 'left:372px;top:48px;font-size:17px;white-space:nowrap;padding:2px 8px;border:2px dashed #e0714f;border-radius:6px;background:#fbe4dc;color:#a8442a;', tr('{{확인 필요: 4분기 매출}}', '{{to confirm: Q4 revenue}}'), 'mono');
  ph.setAttribute('data-box', '');

  // deck view
  const deckView = A(win, 'left:290px;top:54px;width:860px;height:664px;background:#eceee5;');
  const outline = A(deckView, 'left:50px;top:22px;width:760px;height:620px;background:#fff;border:2px solid var(--line);border-radius:6px;box-shadow:0 10px 30px rgba(19,47,40,.10);');
  outline.setAttribute('data-box', '');
  A(outline, 'left:44px;top:26px;font-size:34px;white-space:nowrap;', tr('목차', 'Outline'), 'h');
  A(outline, 'right:44px;top:32px;', chip(tr('스타트업 피치덱 v3', 'Startup pitch deck v3'), 'lime', 'font-size:20px'));
  const roles = tr(['표지', '문제', '해결', '시장', '팀', '요청'], ['Cover', 'Problem', 'Solution', 'Market', 'Team', 'Ask']);
  const orows = roles.map((r, i) => {
    const e = A(outline, `left:44px;top:${100 + i * 66}px;width:668px;height:56px;border-radius:12px;background:#f6f8f0;border:2px solid var(--line);display:flex;align-items:center;`,
      `<span class="mono" style="width:70px;text-align:center;color:#4f7a3a;font-weight:500;font-size:22px">0${i + 1}</span><span style="font-size:28px;font-weight:700">${r}</span>`);
    e.setAttribute('data-box', ''); return e;
  });
  const approve = A(outline, 'left:44px;top:524px;', `<span class="btn">${tr('목차 승인', 'Approve outline')}</span>`);
  const approveHint = A(outline, 'left:290px;top:536px;font-size:20px;white-space:nowrap;', tr('승인하면 슬라이드별로 만듭니다', 'Approve to build slide by slide'), 'muted');
  const grid = A(deckView, 'left:50px;top:22px;width:760px;height:620px;');
  const frames = roles.map((r, i) => {
    const f = A(grid, `left:${(i % 3) * 262}px;top:${80 + Math.floor(i / 3) * 196}px;width:236px;height:158px;border-radius:10px;background:#fff;border:2px solid var(--line);box-shadow:0 8px 20px rgba(19,47,40,.08);`,
      `<div style="position:absolute;left:14px;top:12px;font-size:24px;font-weight:800;white-space:nowrap">${r}</div>
       <div style="position:absolute;left:14px;top:62px;width:160px;height:9px;border-radius:4px;background:#cfd9c6"></div>
       <div style="position:absolute;left:14px;top:84px;width:112px;height:9px;border-radius:4px;background:#cfd9c6"></div>`);
    f.setAttribute('data-box', ''); return f;
  });
  const mflag = A(frames[3], 'left:14px;top:114px;font-size:14px;white-space:nowrap;padding:1px 8px;border:2px dashed #e0714f;border-radius:6px;background:#fbe4dc;color:#a8442a;', tr('{{확인 필요: 시장 규모}}', '{{to confirm: size}}'), 'mono');
  const gridNote = A(grid, 'left:0;top:496px;font-size:22px;white-space:nowrap;', tr('슬라이드별로 만들고, 만들 때마다 검사합니다', 'Built slide by slide, checked as it goes'), 'muted');

  // modal: new document
  const scrim = A(win, 'left:0;top:0;width:100%;height:100%;background:rgba(19,38,31,.5);');
  const dlg = A(win, 'left:420px;top:90px;width:880px;height:540px;', '', 'card');
  A(dlg, 'left:36px;top:26px;font-size:36px;white-space:nowrap;', tr('새 문서', 'New document'), 'h');
  const dl = (y, txt) => A(dlg, `left:36px;top:${y}px;`, txt, 'label');
  const L = [dl(92, tr('목적', 'PURPOSE')), dl(188, tr('양식', 'FORM')), dl(284, tr('참고자료', 'REFERENCES')), dl(380, tr('작성 규칙', 'WRITING RULES'))];
  const dPurpose = A(dlg, 'left:36px;top:116px;width:808px;', '', 'field');
  const dForm = A(dlg, 'left:36px;top:212px;width:808px;display:flex;align-items:center;gap:12px;', `<span>${tr('분기 보고서 · v1', 'Quarterly report · v1')}</span>${chip(tr('내 양식', 'yours'), 'lime', 'font-size:18px;padding:2px 12px')}`, 'field');
  const dRef1 = A(dlg, 'left:36px;top:308px;width:394px;display:flex;align-items:center;gap:10px;', `${icon('check', 26)}<span>q3-report.pdf</span>`, 'field');
  const dRef2 = A(dlg, 'left:450px;top:308px;width:394px;display:flex;align-items:center;gap:10px;', `${icon('check', 26)}<span>sales-notes.md</span>`, 'field');
  const dRules = A(dlg, 'left:36px;top:404px;width:808px;', tr('쉽고 짧은 문장 · v1', 'Plain, short sentences · v1'), 'field');
  const dBtn = A(dlg, 'right:36px;top:476px;', `<span class="btn">${tr('만들기', 'Create')}</span>`);

  const T = {
    title: tr('4분기 보고서', 'Q4 report'),
    l1: tr('출시는 계획대로 진행 중입니다.', 'Launch is on track.'), l2: tr('이번 주 결정이 필요한 안건이 두 건 있습니다.', 'Two items need a decision this week.'),
    r1: tr('• 협력사 지연으로 베타가 1주 늦어질 수 있습니다.', '• A vendor delay may move the beta by a week.'), r2: tr('• 지원 문의 대기열이 목표를 넘었습니다.', '• The support queue is above target.'),
    q1: tr('• 외주 인력 1명 추가 승인', '• Approve one extra contractor.'), purpose: tr('4분기 팀 보고서', 'Q4 team report')
  };
  s.update = (lt) => {
    show(title, fade(lt, 0.3, 1.0), 14);
    show(win, fade(lt, 0.7, 1.4), 20);
    // dialog
    const out = 1 - fade(lt, 6.5, 7.1);
    const scr = fade(lt, 0.9, 1.4) * out; scrim.style.opacity = scr; scrim.style.display = scr > 0.001 ? 'block' : 'none';
    const dg = fade(lt, 1.3, 1.9) * out; show(dlg, dg, 14); dlg.style.display = dg > 0.001 ? 'block' : 'none';
    [[L[0], dPurpose, 1.9], [L[1], dForm, 3.8], [L[2], dRef1, 4.4], [null, dRef2, 4.9], [L[3], dRules, 5.4]].forEach(([l, f, at]) => { const a = fade(lt, at, at + 0.4); if (l) l.style.opacity = a; f.style.opacity = a; });
    dPurpose.textContent = typed(T.purpose, seg(lt, 2.2, 3.6)) + (lt > 2.2 && lt < 3.7 ? '▌' : '');
    dBtn.style.opacity = fade(lt, 5.6, 6.0); press(dBtn, lt, 6.2, 0.4);
    // document drafting
    const fadeEl = (e, a) => { e.style.opacity = fade(lt, a, a + 0.4); };
    const typeAt = (e, text, a, b, mark) => { const p = seg(lt, a, b); e.style.opacity = lt >= a ? 1 : 0; e.innerHTML = esc(typed(text, p)) + (mark && p >= 1 ? ` <span class="src">${mark}</span>` : ''); };
    const docA = 1 - fade(lt, 20.8, 21.3);
    docView.style.opacity = docA; docView.style.display = docA > 0.001 ? 'block' : 'none';
    eTitle.textContent = typed(T.title, seg(lt, 7.0, 7.8)); eTitle.style.opacity = lt >= 7.0 ? 1 : 0;
    [[hSum, 8.0], [hMet, 11.0], [hRisk, 15.0], [hReq, 17.8]].forEach(([h, a]) => { fadeEl(h.h, a); fadeEl(h.g, a); });
    typeAt(l1, T.l1, 8.3, 9.4, '[1]'); typeAt(l2, T.l2, 9.7, 10.8);
    fadeEl(tbl, 11.2);
    typeAt(v1, '1,240', 11.5, 12.0, '[2]'); typeAt(v2, '38%', 12.3, 12.8, '[1]');
    ph.style.opacity = fade(lt, 13.2, 13.6);
    const ring = fade(lt, 14.2, 14.5) * (1 - fade(lt, 17.0, 17.5)) * (0.55 + 0.45 * Math.sin((lt - 14.2) * 5));
    ph.style.boxShadow = `0 0 0 ${7 * ring}px rgba(224,113,79,${0.35 * ring})`;
    typeAt(r1, T.r1, 15.3, 16.4, '[2]'); typeAt(r2, T.r2, 16.5, 17.6); typeAt(q1, T.q1, 18.1, 19.2);
    src1.style.opacity = fade(lt, 9.6, 10.0); src2.style.opacity = fade(lt, 12.2, 12.6);
    // mode switch: document → deck
    const deckMode = lt >= 21.4;
    tabDoc.firstChild.className = 'chip ' + (deckMode ? 'ghost' : 'lime'); tabDeck.firstChild.className = 'chip ' + (deckMode ? 'lime' : 'ghost');
    itemQ.style.background = deckMode ? 'transparent' : '#e1efb0'; itemQ.style.fontWeight = deckMode ? 400 : 700;
    itemDeck.style.opacity = deckMode ? fade(lt, 21.4, 21.9) : 0; itemDeck.style.background = '#e1efb0'; itemDeck.style.fontWeight = 700;
    formVal.textContent = deckMode ? tr('스타트업 피치덱 · v3', 'Startup pitch deck · v3') : tr('분기 보고서 · v1', 'Quarterly report · v1');
    formSub.textContent = deckMode ? tr('@sample-studio 작성 · CC-BY-4.0 · 내 복사본', 'by @sample-studio · CC-BY-4.0 · your copy') : tr('섹션 4개 · 내 양식', '4 sections · yours');
    tcName.textContent = deckMode ? tr('시장 규모', 'Market size') : tr('4분기 매출', 'Q4 revenue');
    const tcA = deckMode ? fade(lt, 28.8, 29.3) : fade(lt, 14.6, 15.1) * (1 - fade(lt, 20.6, 21.0));
    tcBox.style.opacity = tcA; tcLabel.style.opacity = tcA;
    // deck: outline first, approve, then slides
    deckView.style.display = lt >= 21.3 ? 'block' : 'none'; deckView.style.opacity = fade(lt, 21.4, 21.9);
    const ol = 1 - fade(lt, 25.8, 26.2); outline.style.opacity = ol; outline.style.display = ol > 0.001 ? 'block' : 'none';
    orows.forEach((r, i) => show(r, fade(lt, 21.9 + i * 0.45, 22.4 + i * 0.45), 8));
    approve.style.opacity = fade(lt, 24.4, 24.8); press(approve, lt, 25.2, 0.45); approveHint.style.opacity = fade(lt, 24.6, 25.0);
    frames.forEach((f, i) => show(f, fade(lt, 26.3 + i * 0.7, 26.8 + i * 0.7), 10, 0, 0.96));
    mflag.style.opacity = fade(lt, 28.8, 29.2);
    gridNote.style.opacity = fade(lt, 30.6, 31.0);
  };
}
