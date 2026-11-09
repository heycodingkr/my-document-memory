'use strict';
// S1 people have always made documents · S2 and still every document starts by hand · S3 give documents a memory.
// Dates and wording come from docs/demo/demo-video.md (claims H1–H6, P1).

function buildS1() {
  const s = addScene('s1', { badge: 'history' });
  const title = A(s, 'left:100px;top:100px;font-size:76px;white-space:nowrap;', tr('인류는 문서를 만들며 살아왔습니다.', 'People have always made documents.'), 'h');
  const sub = A(s, 'left:104px;top:198px;font-size:25px;white-space:nowrap;', tr('연도는 대략적인 시기입니다 · 가장 오래된 글쓰기 기록은 대부분 장부였습니다', 'Dates are approximate · the earliest written records were mostly accounts'), 'muted');
  const years = A(s, 'right:100px;top:106px;', chip(tr('5천 년 넘게', '5,000+ years'), 'dark', 'font-size:40px;padding:10px 30px;'));
  const N = [
    { y: tr('기원전 약 3300년', 'c. 3300 BCE'), n: tr('점토판', 'Clay tablets'), d: tr('최초의 기록은 대부분 장부', 'The first records were mostly accounts'), ic: 'tablet' },
    { y: tr('기원전 약 3000년', 'c. 3000 BCE'), n: tr('파피루스', 'Papyrus'), d: tr('말아서 보관하는 두루마리', 'Rolled up into scrolls'), ic: 'scroll' },
    { y: tr('1450년경', 'c. 1450'), n: tr('활판 인쇄기', 'Movable-type press'), d: tr('유럽에서 책을 찍어 내다', 'Books printed in Europe'), ic: 'press' },
    { y: tr('1870년대', '1870s'), n: tr('타자기', 'Typewriters'), d: tr('손글씨에서 활자로', 'From handwriting to type'), ic: 'typewriter' },
    { y: tr('1970–80년대', '1970s–80s'), n: tr('워드프로세서', 'Word processors'), d: tr('화면에서 고치고 저장', 'Edit on screen, then save'), ic: 'wp' },
    { y: '2006', n: 'Google Docs', d: tr('브라우저에서 함께 쓰는 문서', 'Documents in the browser'), ic: 'web' }
  ];
  const X = N.map((_, i) => 120 + i * 276), LY = 560, H = 214;
  const T = [1.0, 6.3, 7.7, 9.1, 10.5, 11.9];
  const base = A(s, `left:100px;top:${LY - 3}px;width:1720px;height:6px;border-radius:3px;background:#d3dccb;`);
  const ghosts = X.map((x) => A(s, `left:${x - 12}px;top:${LY - 12}px;width:24px;height:24px;border-radius:50%;background:#e4eadc;border:4px solid #cbd6c1;`));
  const prog = A(s, `left:100px;top:${LY - 3}px;width:0;height:6px;border-radius:3px;background:var(--green);`);
  const parts = N.map((n, i) => {
    const up = i % 2 === 0, top = up ? 250 : 652;
    const stem = A(s, `left:${X[i] - 2}px;top:${up ? top + H : LY}px;width:4px;height:${up ? LY - (top + H) : top - LY}px;background:#b8c7ad;`);
    const dot = A(s, `left:${X[i] - 14}px;top:${LY - 14}px;width:28px;height:28px;border-radius:50%;background:var(--lime);border:6px solid var(--deep);`);
    const card = A(s, `left:${X[i] - 40}px;top:${top}px;width:380px;height:${H}px;`, `${icon(n.ic, 60, 'position:absolute;left:26px;top:22px')}
      <div class="mono" style="position:absolute;left:104px;top:34px;font-size:23px;font-weight:500;color:#4f7a3a;white-space:nowrap">${n.y}</div>
      <div class="h" style="position:absolute;left:26px;top:94px;font-size:33px;white-space:nowrap">${n.n}</div>
      <div class="muted" style="position:absolute;left:26px;top:148px;width:330px;font-size:23px;line-height:1.3">${n.d}</div>`, 'card');
    return { up, stem, dot, card };
  });
  const P = [[0.6, 100], ...T.map((t, i) => [t, X[i]]), [12.6, 1820]];
  const lineX = (lt) => { if (lt <= P[0][0]) return P[0][1]; for (let i = 1; i < P.length; i++) if (lt <= P[i][0]) return lerp(P[i - 1][1], P[i][1], seg(lt, P[i - 1][0], P[i][0])); return P[P.length - 1][1]; };
  const punch = A(s, 'left:100px;top:350px;width:1720px;font-size:116px;line-height:1.1;', tr('도구는 바뀌었습니다.<br><span style="color:var(--green)">쓰는 손은 같았습니다.</span>', 'The tools changed.<br><span style="color:var(--green)">The hands never did.</span>'), 'h');
  s.update = (lt) => {
    const dim = lerp(1, 0.07, fade(lt, 13.4, 14.2));
    show(title, fade(lt, 0.0, 0.8) * lerp(1, 0.2, fade(lt, 13.4, 14.2)), 16);
    sub.style.opacity = fade(lt, 0.6, 1.4) * dim;
    show(years, fade(lt, 0.8, 1.5) * dim, 10);
    prog.style.width = `${Math.max(0, lineX(lt) - 100)}px`; prog.style.opacity = dim;
    base.style.opacity = fade(lt, 0.4, 1.0) * dim;
    ghosts.forEach((g) => { g.style.opacity = fade(lt, 0.6, 1.2) * dim; });
    parts.forEach((p, i) => {
      show(p.card, fade(lt, T[i], T[i] + 0.7) * dim, p.up ? -22 : 22);
      p.dot.style.opacity = fade(lt, T[i] - 0.2, T[i] + 0.3) * dim;
      p.stem.style.opacity = fade(lt, T[i] - 0.1, T[i] + 0.5) * dim;
    });
    show(punch, fade(lt, 13.8, 14.8), 22);
  };
}

function buildS2() {
  const s = addScene('s2', { badge: 'illus' });
  const title = A(s, 'left:100px;top:104px;font-size:68px;white-space:nowrap;', tr('그런데 지금도, 문서는 손으로 시작합니다.', 'And still, every document starts by hand.'), 'h');
  const win = A(s, 'left:100px;top:240px;width:760px;height:520px;', '', 'card');
  const bar = A(win, 'left:0;top:0;width:100%;height:56px;border-bottom:2px solid var(--line);');
  [['#e0714f', 24], ['#e6c14a', 46], ['#7fb069', 68]].forEach(([c, x]) => A(bar, `left:${x}px;top:20px;width:14px;height:14px;border-radius:50%;background:${c};`));
  A(bar, 'left:104px;top:13px;font-size:22px;white-space:nowrap;', tr('문서 / 보고서', 'Documents / Reports'), 'mono muted');
  const files = tr(['3분기_보고서.docx', '3분기_보고서_최종.docx', '3분기_보고서_최종_v2.docx', '3분기_보고서_진짜최종.docx', '3분기_보고서 (복사본 3).docx'],
    ['q3-report.docx', 'q3-report-final.docx', 'q3-report-final-v2.docx', 'q3-report-FINAL-real.docx', 'q3-report (copy 3).docx']);
  const frows = files.map((f, i) => {
    const r = A(win, `left:20px;top:${70 + i * 88}px;width:720px;height:76px;border-radius:14px;display:flex;align-items:center;`, `${icon('file', 40, 'margin:0 18px')}<span class="mono" style="font-size:25px;font-weight:500">${f}</span>`);
    r.setAttribute('data-box', ''); return r;
  });
  const chores = tr(['지난번 파일을 찾고', '양식을 복사하고', '같은 사실을 다시 쓰고', '말투를 맞추고', '이름과 날짜를 고친다'],
    [`Find last time's file`, 'Copy the form', 'Retype the same facts', 'Match the tone', 'Fix names and dates']);
  const CT = [2.0, 6.6, 8.4, 10.2, 11.4];
  const crows = chores.map((c, i) => {
    const r = A(s, `left:920px;top:${240 + i * 102}px;width:900px;height:88px;display:flex;align-items:center;padding:0 22px;`,
      `<span style="color:#c9553a;font-weight:800;font-size:34px;width:60px;text-align:center">${i + 1}</span><span style="font-size:35px;font-weight:700">${c}</span>`, 'card');
    A(r, 'right:24px;top:24px;', chip(tr('또', 'again'), 'coral', 'font-size:24px')); return r;
  });
  const note = A(s, 'left:104px;top:800px;font-size:22px;white-space:nowrap;', tr('일러스트 · 흔한 작업 순서를 묶은 예시', 'Illustration · a composite of common steps'), 'muted');
  const Q = A(s, 'left:100px;top:230px;width:1720px;font-size:50px;white-space:nowrap;', tr('어떤 틀로? 어떤 사실로? 어떤 말투로?', 'Which form? Which facts? Which voice?'), 'h');
  const words = tr([['틀', '사람 머릿속에'], ['사실', '옛 파일 속에'], ['말투', '각자의 습관 속에']], [['Form', `in someone's head`], ['Facts', 'in old files'], ['Voice', 'in personal habit']]);
  const tcards = words.map(([w, d], i) => A(s, `left:${100 + i * 590}px;top:340px;width:540px;height:270px;border-color:#f0bfae;`,
    `<div class="h" style="position:absolute;left:36px;top:40px;font-size:100px;color:#a8442a;white-space:nowrap">${w}</div><div class="muted" style="position:absolute;left:38px;top:196px;font-size:30px;white-space:nowrap">${d}</div>`, 'card'));
  const none = A(s, 'left:100px;top:670px;width:1720px;font-size:64px;color:#a8442a;white-space:nowrap;', tr('그걸 기억해 주는 곳이 없습니다.', 'Nothing remembers them.'), 'h');
  s.update = (lt) => {
    const out = 1 - fade(lt, 12.0, 12.6);
    show(title, fade(lt, 0.0, 0.8), 16);
    show(win, fade(lt, 0.6, 1.2) * out, 16);
    frows.forEach((r, i) => show(r, fade(lt, 1.0 + i * 0.45, 1.6 + i * 0.45), 12));
    const sel = fade(lt, 4.6, 5.0);
    frows[4].style.background = sel > 0.01 ? `rgba(216,239,120,${0.45 * sel})` : 'transparent';
    frows[4].style.boxShadow = `inset 0 0 0 ${3 * sel}px #c9e168`;
    crows.forEach((r, i) => show(r, fade(lt, CT[i], CT[i] + 0.6) * out, 14));
    note.style.opacity = fade(lt, 1.2, 2.0) * out;
    show(Q, fade(lt, 12.6, 13.4), 14);
    tcards.forEach((c, i) => show(c, fade(lt, 13.0 + i * 1.1, 13.7 + i * 1.1), 18));
    show(none, fade(lt, 16.2, 17.0), 14);
  };
}

function buildS3() {
  const s = addScene('s3', { badge: 'concept' });
  const name = A(s, 'left:100px;top:110px;font-size:140px;white-space:nowrap;color:#f3f1e8;', 'My Document Memory', 'h');
  const sub = A(s, 'left:104px;top:306px;font-size:58px;color:var(--lime);white-space:nowrap;', tr('문서에 기억을 줍니다.', 'Give documents a memory.'), 'h');
  const defs = [
    { ic: 'form', q: tr('어떤 틀로 쓸까?', 'Which form to use?'), n: tr('양식', 'Forms'), d: tr('섹션 순서, 스타일, 채울 항목. 내 양식과 공유 양식.', 'Section order, styles and slots. Yours and shared.') },
    { ic: 'refs', q: tr('무슨 사실을 써도 될까?', 'Which facts may I write?'), n: tr('참고자료', 'References'), d: tr('내 정책·사실·프로젝트 문서. 문단 단위 출처.', 'Your policies, facts and project docs, with sources.') },
    { ic: 'rules', q: tr('어떤 말투로 쓸까?', 'How should it sound?'), n: tr('작성 규칙', 'Writing rules'), d: tr('어조, 용어, 표기, 편집 규칙.', 'Tone, terms, notation and editing rules.') }
  ];
  const cards = defs.map((d, i) => A(s, `left:${100 + i * 590}px;top:410px;width:540px;height:340px;`,
    `${icon(d.ic, 64, 'position:absolute;left:32px;top:30px')}
     <div class="mono" style="position:absolute;left:32px;top:112px;font-size:24px;color:var(--lime);white-space:nowrap">${d.q}</div>
     <div class="h" style="position:absolute;left:32px;top:150px;font-size:50px;white-space:nowrap">${d.n}</div>
     <div class="muted bal" style="position:absolute;left:32px;top:232px;width:476px;font-size:26px;line-height:1.35">${d.d}</div>`, 'card'));
  const steps = [tr('요청', 'Your request'), tr('양식 + 참고자료 + 작성 규칙 불러오기', 'Recall form + references + rules'), tr('양식대로 만든 문서', 'A document in your form')];
  const flow = A(s, 'left:100px;top:792px;display:flex;align-items:center;gap:18px;white-space:nowrap;',
    steps.map((t, i) => (i ? '<span style="color:var(--lime);font-size:34px;font-weight:800">→</span>' : '') + chip(t, i === 2 ? 'lime' : '', 'font-size:28px;padding:10px 26px')).join(''));
  s.update = (lt) => {
    show(name, fade(lt, 0.4, 1.3), 24);
    show(sub, fade(lt, 1.8, 2.6), 16);
    cards.forEach((c, i) => show(c, fade(lt, 6.6 + i * 2.0, 7.3 + i * 2.0), 24));
    [...flow.children].forEach((c, k) => { c.style.opacity = fade(lt, 14.0 + k * 0.5, 14.5 + k * 0.5); });
  };
}
