'use strict';
// S4 save your own form (spec §2 steps 1–3, §5) · S5 bring in forms others share (spec §3, §5). Concept drawings, sample data.

function buildS4() {
  const s = addScene('s4', { badge: 'concept' });
  const title = A(s, 'left:100px;top:104px;font-size:68px;white-space:nowrap;', tr('내 양식을 저장합니다.', 'Save your own form.'), 'h');
  const stepNames = [tr('1 올리기', '1 Upload'), tr('2 미리보기', '2 Preview'), tr('3 저장', '3 Save')];
  const pills = stepNames.map((t, i) => A(s, `left:${1250 + i * 190}px;top:124px;`, chip(t, 'ghost', 'font-size:22px')));

  // left: upload + reading
  const up = A(s, 'left:100px;top:240px;width:520px;height:630px;', '', 'card');
  A(up, 'left:30px;top:24px;', tr('1 · 파일 올리기', '1 · UPLOAD'), 'label');
  const drop = A(up, 'left:30px;top:70px;width:460px;height:200px;border:3px dashed #b8c7ad;border-radius:20px;');
  const hint = A(drop, 'left:0;top:80px;width:100%;text-align:center;font-size:22px;white-space:nowrap;', 'DOCX · PPTX · PDF · Markdown · TXT', 'muted mono');
  const file = A(up, 'left:60px;top:100px;width:400px;height:140px;border-radius:18px;background:#fff;border:2px solid var(--line);box-shadow:0 12px 30px rgba(19,47,40,.14);',
    `${icon('file', 64, 'position:absolute;left:24px;top:38px')}<div style="position:absolute;left:104px;top:32px;font-size:26px;font-weight:700;white-space:nowrap">${tr('팀 분기 보고서', 'Team quarterly report')}</div><div class="mono muted" style="position:absolute;left:104px;top:78px;font-size:21px">.docx</div>`);
  file.setAttribute('data-box', '');
  const page = A(up, 'left:110px;top:296px;width:300px;height:290px;background:#fff;border:2px solid var(--line);border-radius:10px;overflow:hidden;');
  [[20, 160, 14, '#254b3c'], [58, 90, 10, '#254b3c'], [78, 250, 8, '#cfd9c6'], [94, 208, 8, '#cfd9c6'], [124, 112, 10, '#254b3c'],
   [192, 70, 10, '#254b3c'], [212, 200, 8, '#cfd9c6'], [228, 170, 8, '#cfd9c6'], [254, 100, 10, '#254b3c'], [272, 180, 8, '#cfd9c6']]
    .forEach(([y, w, h, c]) => A(page, `left:24px;top:${y}px;width:${w}px;height:${h}px;border-radius:4px;background:${c};`));
  [0, 1, 2].forEach((k) => A(page, `left:${24 + k * 86}px;top:144px;width:78px;height:34px;border-radius:6px;background:#eef3e4;border:2px solid #b8c7ad;`));
  const scan = A(page, 'left:0;top:0;width:100%;height:4px;background:var(--lime);box-shadow:0 0 18px 6px rgba(216,239,120,.8);');
  const reading = A(up, 'left:30px;top:596px;font-size:21px;white-space:nowrap;', '', 'muted');

  // right: preview + confirm
  const pv = A(s, 'left:660px;top:240px;width:1160px;height:630px;', '', 'card');
  A(pv, 'left:30px;top:24px;', tr('2 · 미리보기와 확인', '2 · PREVIEW AND CONFIRM'), 'label');
  const sug = A(pv, 'right:30px;top:16px;', chip(tr('제안: 양식', 'Suggested: Form'), 'lime', 'font-size:22px'));
  const R = tr([['제목', '요약', '제목 · 문단 2개'], ['표', '지표', '3열'], ['목록', '위험', '글머리 목록'], ['목록', '요청', '글머리 목록']],
    [['HEADING', 'Summary', 'heading · 2 paragraphs'], ['TABLE', 'Key metrics', '3 columns'], ['LIST', 'Risks', 'bullet list'], ['LIST', 'Requests', 'bullet list']]);
  const srows = R.map(([ty, nm, meta], i) => {
    const r = A(pv, `left:30px;top:${84 + i * 84}px;width:540px;height:78px;border-radius:14px;background:#f6f8f0;border:2px solid var(--line);`,
      `<span class="mono" style="position:absolute;left:16px;top:26px;font-size:17px;font-weight:500;color:#4f7a3a;letter-spacing:.08em;white-space:nowrap">${ty}</span>
       <span style="position:absolute;left:140px;top:8px;font-size:28px;font-weight:700;white-space:nowrap">${nm}</span>
       <span class="muted" style="position:absolute;left:140px;top:46px;font-size:18px;white-space:nowrap">${meta}</span>`);
    r.setAttribute('data-box', ''); return r;
  });
  const styles = A(pv, 'left:30px;top:432px;font-size:21px;white-space:nowrap;', tr('스타일: 제목 1 · 본문 · 표 격자', 'Styles: Heading 1 · Body · Table grid'), 'muted mono');
  const labels = tr(['이름', '문서 종류', '태그', '공개 범위'], ['NAME', 'TYPE', 'TAGS', 'VISIBILITY']).map((t, k) => A(pv, `left:600px;top:${74 + k * 96}px;`, t, 'label'));
  const fName = A(pv, 'left:600px;top:98px;width:530px;', '', 'field');
  const fType = A(pv, 'left:600px;top:194px;width:530px;', tr('보고서', 'Report'), 'field');
  const fTags = A(pv, 'left:600px;top:290px;width:530px;display:flex;align-items:center;gap:8px;', chip(tr('분기', 'quarterly'), '', 'font-size:20px;padding:2px 14px') + chip(tr('팀', 'team'), '', 'font-size:20px;padding:2px 14px'), 'field');
  const fVis = A(pv, 'left:600px;top:386px;width:530px;display:flex;align-items:center;gap:10px;', `${icon('lock', 30)}<span>${tr('비공개 (기본)', 'Private (default)')}</span>`, 'field');
  const save = A(pv, 'left:600px;top:480px;', `<span class="btn">${tr('내 양식에 저장', 'Save to my forms')}</span>`);
  const saved = A(pv, 'left:600px;top:480px;', chip(`✓ ${tr('저장됨 · 팀 분기 보고서 v1', 'Saved · Team quarterly report v1')}`, 'dark', 'font-size:24px;padding:12px 26px'));
  const foot = A(pv, 'left:30px;top:568px;font-size:22px;white-space:nowrap;', tr('내가 확인하고 승인한 것만 메모리가 됩니다 · 버전으로 저장', 'Only what you review and approve becomes memory · saved as versions'), 'muted');
  const fieldBits = [[labels[0], fName], [labels[1], fType], [labels[2], fTags], [labels[3], fVis]];
  const nameText = tr('팀 분기 보고서', 'Team quarterly report');
  const readTxt = [tr('섹션·표·목록·스타일을 읽는 중…', 'Reading sections, tables, lists, styles…'), tr('읽기 완료', 'Done reading')];

  s.update = (lt) => {
    show(title, fade(lt, 0.3, 1.0), 16);
    const active = lt >= 15.4 ? 2 : lt >= 5.8 ? 1 : 0;
    pills.forEach((p, i) => { p.style.opacity = fade(lt, 0.8, 1.4); p.firstChild.className = 'chip ' + (i === active ? 'lime' : 'ghost'); });
    show(up, fade(lt, 0.8, 1.4), 16);
    hint.style.opacity = 1 - fade(lt, 2.2, 2.6);
    const drop2 = fade(lt, 2.0, 2.8); show(file, drop2, -50); file.style.opacity = drop2;
    show(page, fade(lt, 3.0, 3.6), 14);
    const sc = seg(lt, 3.6, 6.0); scan.style.top = `${lerp(0, 286, sc)}px`; scan.style.opacity = sc > 0 && sc < 1 ? 1 : 0;
    reading.textContent = readTxt[lt < 6.0 ? 0 : 1]; reading.style.opacity = fade(lt, 3.4, 3.9);
    show(pv, fade(lt, 5.2, 5.9), 18);
    sug.style.opacity = fade(lt, 6.0, 6.5);
    srows.forEach((r, i) => show(r, fade(lt, 6.4 + i * 1.1, 6.9 + i * 1.1), 10));
    styles.style.opacity = fade(lt, 10.8, 11.3);
    const FT = [10.6, 12.9, 13.4, 13.9];
    fieldBits.forEach(([l, f], k) => { const a = fade(lt, FT[k], FT[k] + 0.4); l.style.opacity = a; f.style.opacity = a; });
    fName.textContent = typed(nameText, seg(lt, 10.9, 12.6)) + (lt > 10.9 && lt < 12.7 ? '▌' : '');
    const vp = fade(lt, 14.2, 14.7) * (1 - fade(lt, 16.8, 17.2));
    fVis.style.borderColor = vp > 0.02 ? '#9fcb3a' : 'var(--line)'; fVis.style.boxShadow = `0 0 0 ${6 * vp}px rgba(216,239,120,${0.7 * vp})`;
    const sv = lt < 16.6;
    save.style.opacity = sv ? fade(lt, 15.0, 15.5) : 0; press(save, lt, 16.0, 0.5);
    saved.style.opacity = fade(lt, 16.6, 17.1); saved.style.transform = `scale(${lerp(0.94, 1, fade(lt, 16.6, 17.1))})`;
    foot.style.opacity = fade(lt, 17.2, 17.8);
  };
}

function buildS5() {
  const s = addScene('s5', { badge: 'concept' });
  const title = A(s, 'left:100px;top:104px;font-size:68px;white-space:nowrap;', tr('다른 사람의 양식도 가져옵니다.', 'Or bring in forms others share.'), 'h');
  // Form names are seed forms from docs/spec/template-library.md (DOC-01/02/03/07/08, SLIDE-01). Authors are sample handles.
  const F = tr([['회의록', '@sample-ops', '문서'], ['주간 업무보고', '@sample-ops', '문서'], ['사업 제안서', '@sample-studio', '문서'], ['스타트업 피치덱', '@sample-studio', '발표'], ['일일 업무일지', '@sample-ops', '문서'], ['견적서', '@sample-sales', '문서']],
    [['Meeting minutes', '@sample-ops', 'Doc'], ['Weekly report', '@sample-ops', 'Doc'], ['Business proposal', '@sample-studio', 'Doc'], ['Startup pitch deck', '@sample-studio', 'Deck'], ['Daily work log', '@sample-ops', 'Doc'], ['Quotation', '@sample-sales', 'Doc']]);
  const cards = F.map(([n, by, ty], i) => A(s, `left:${100 + (i % 2) * 444}px;top:${240 + Math.floor(i / 2) * 214}px;width:420px;height:190px;`,
    `<div class="h" style="position:absolute;left:26px;top:22px;font-size:33px;white-space:nowrap">${n}</div>
     <div class="mono muted" style="position:absolute;left:26px;top:74px;font-size:20px;white-space:nowrap">${by}</div>
     <div style="position:absolute;left:26px;top:122px;white-space:nowrap">${chip('v3', 'ghost', 'font-size:20px;padding:2px 14px')} ${chip('CC-BY-4.0', 'ghost', 'font-size:20px;padding:2px 14px')} ${chip(ty, '', 'font-size:20px;padding:2px 14px')}</div>`, 'card'));
  const pv = A(s, 'left:1000px;top:240px;width:820px;height:618px;', '', 'card');
  A(pv, 'left:30px;top:24px;', tr('미리보기', 'PREVIEW'), 'label');
  A(pv, 'left:30px;top:56px;font-size:46px;white-space:nowrap;', F[3][0], 'h');
  const meta = tr([['작성자', '@sample-studio'], ['버전', 'v3'], ['라이선스', 'CC-BY-4.0 (예시)'], ['상태', '게시됨']], [['AUTHOR', '@sample-studio'], ['VERSION', 'v3'], ['LICENSE', 'CC-BY-4.0 (sample)'], ['STATUS', 'Published']]);
  const mrows = meta.map(([k, v], i) => A(pv, `left:30px;top:${132 + i * 38}px;white-space:nowrap;`,
    `<span class="mono muted" style="display:inline-block;width:170px;font-size:19px;letter-spacing:.1em">${k}</span><span class="mono" style="font-size:22px;font-weight:500">${v}</span>`));
  const roles = tr(['표지', '문제', '해결', '시장', '팀', '요청'], ['Cover', 'Problem', 'Solution', 'Market', 'Team', 'Ask']);
  const thumbs = roles.map((r, i) => A(pv, `left:${30 + (i % 3) * 250}px;top:${300 + Math.floor(i / 3) * 112}px;width:232px;height:98px;border-radius:10px;background:#fff;border:2px solid var(--line);`,
    `<div style="position:absolute;left:14px;top:10px;font-size:22px;font-weight:800;white-space:nowrap">${r}</div>
     <div style="position:absolute;left:14px;top:50px;width:150px;height:8px;border-radius:4px;background:#cfd9c6"></div>
     <div style="position:absolute;left:14px;top:68px;width:104px;height:8px;border-radius:4px;background:#cfd9c6"></div>`));
  thumbs.forEach((t) => t.setAttribute('data-box', ''));
  const copy = A(pv, 'left:30px;top:540px;', `<span class="btn">${tr('내 라이브러리로 복사', 'Copy to my library')}</span>`);
  const toast = A(pv, 'left:30px;top:540px;', chip(`✓ ${tr('복사됨 · 작성자 표기 유지 · 원본은 그대로', 'Copied · attribution kept · original unchanged')}`, 'dark', 'font-size:22px;padding:12px 24px'));
  s.update = (lt) => {
    show(title, fade(lt, 0.3, 1.0), 16);
    cards.forEach((c, i) => {
      show(c, fade(lt, 0.9 + i * 0.4, 1.5 + i * 0.4), 16);
      if (i === 3) { const sel = fade(lt, 6.6, 7.1); c.style.borderColor = sel > 0.02 ? '#9fcb3a' : 'var(--line)'; c.style.boxShadow = `0 0 0 ${7 * sel}px rgba(216,239,120,${0.7 * sel}), 0 24px 60px rgba(19,47,40,.10)`; }
    });
    show(pv, fade(lt, 7.0, 7.7), 18);
    mrows.forEach((r, i) => { r.style.opacity = fade(lt, 8.0 + i * 0.6, 8.5 + i * 0.6); });
    thumbs.forEach((t, i) => show(t, fade(lt, 10.4 + i * 0.25, 10.9 + i * 0.25), 8));
    copy.style.opacity = lt < 13.8 ? fade(lt, 11.8, 12.3) : 0; press(copy, lt, 13.4, 0.5);
    toast.style.opacity = fade(lt, 13.8, 14.3); toast.style.transform = `scale(${lerp(0.94, 1, fade(lt, 13.8, 14.3))})`;
  };
}
