'use strict';
// Extra scenes are registered only by the 120-second cut. All are explanatory illustrations.
window.__BADGES.example = { cls: 'illus', text: () => 'ILLUSTRATION · EXAMPLE DATA' };

function buildCompanyFormats() {
  const s = addScene('companies', { badge: 'example' });
  A(s, 'left:80px;top:132px;font-size:74px;white-space:nowrap;', 'Company formats, kept together.', 'h');
  A(s, 'left:80px;top:232px;font-size:28px;color:var(--muted);', 'Reports. Proposals. Meeting notes. Each with its own standard.');
  const library = A(s, 'left:80px;top:312px;width:1760px;height:552px;', '', 'card');
  A(library, 'left:28px;top:30px;', 'MY FORMATS', 'label');
  A(library, 'left:28px;top:72px;', '<span class="chip lime" style="font-size:17px">Private library</span>');
  const companies = SCRIPT.feature_examples.company_names;
  const tabs = companies.map((name, i) => A(library, `left:28px;top:${146 + i * 102}px;width:278px;height:76px;border-radius:16px;padding:23px 22px;font-size:25px;font-weight:700;`, name));
  const content = [
    ['Weekly report', 'Overview', 'Progress and blockers', 'Next steps'],
    ['Client proposal', 'Context and goals', 'Proposed approach', 'Decision and next steps'],
    ['Meeting notes', 'Agenda', 'Decisions', 'Owners and due dates']
  ];
  const cards = content.map(([title, ...sections], i) => {
    const card = A(library, `left:${354 + i * 458}px;top:30px;width:432px;height:488px;`, '', 'card');
    A(card, 'left:26px;top:26px;font-size:15px;', companies[i].toUpperCase(), 'label');
    A(card, 'left:26px;top:70px;width:380px;font-size:31px;', title, 'h');
    A(card, 'left:26px;top:126px;font-size:15px;color:var(--muted);', 'REUSABLE STRUCTURE', 'mono');
    sections.forEach((section, j) => {
      A(card, `left:26px;top:${178 + j * 72}px;width:380px;padding:17px 15px;background:#edf2e6;border-radius:10px;font-size:21px;white-space:nowrap;`, section);
    });
    A(card, 'left:26px;top:438px;font-size:16px;color:var(--muted);', 'Sections · version · attribution', 'mono');
    return card;
  });
  A(s, 'left:80px;top:890px;font-size:18px;color:var(--muted);', 'Example company formats · shared structure, private references.', 'mono');
  s.update = (lt) => {
    const active = Math.min(2, Math.max(0, Math.floor((lt - 1.8) / 2.3)));
    tabs.forEach((tab, i) => { tab.style.background = i === active ? '#d8ef78' : '#f0f3ea'; });
    cards.forEach((card, i) => {
      show(card, fade(lt, 0.6 + i * 0.35, 1.2 + i * 0.35), 16);
      card.style.borderColor = i === active ? '#829e38' : '#d7e0d1';
    });
  };
}

function buildSharedStandard() {
  const s = addScene('standards', { badge: 'example' });
  A(s, 'left:80px;top:132px;font-size:74px;white-space:nowrap;', 'One link. A common standard.', 'h');
  A(s, 'left:80px;top:232px;font-size:28px;color:#b9cabb;', 'Give your AI the method behind the document.');
  const memory = A(s, 'left:80px;top:320px;width:600px;height:540px;', '', 'card');
  A(memory, 'left:30px;top:26px;', 'PUBLIC TEMPLATE LINK', 'label');
  const u = new URL(SCRIPT.feature_examples.public_template_url);
  A(memory, 'left:30px;top:70px;font:400 20px/1.55 var(--mono);color:var(--lime);', `${u.host}<br>/v1/public/templates/<br>${u.pathname.split('/').at(-1)}`);
  const criteria = [['Structure', 'Sections and ordering'], ['Writing patterns', 'Tone and review prompts'], ['Design guidance', 'Layout intent and examples']];
  criteria.forEach(([title, sub], i) => {
    A(memory, `left:30px;top:${190 + i * 86}px;font-size:26px;font-weight:700;`, title);
    A(memory, `left:30px;top:${226 + i * 86}px;font-size:20px;color:#b9cabb;`, sub);
  });
  A(memory, 'left:30px;top:490px;font-size:17px;color:#b9cabb;', 'Private source files stay in your space.', 'mono');
  const host = A(s, 'left:760px;top:410px;width:410px;height:330px;', '', 'card');
  A(host, 'left:30px;top:26px;', 'YOUR AI HOST', 'label');
  ['Read the memory', 'Follow the standard', 'Review the result'].forEach((t, i) => A(host, `left:30px;top:${94 + i * 68}px;font-size:${i === 0 ? 32 : 28}px;white-space:nowrap;`, t, i === 0 ? 'h' : ''));
  const arrowA = A(s, 'left:696px;top:510px;font-size:56px;color:var(--lime);', '→', 'h');
  const arrowB = A(s, 'left:1186px;top:510px;font-size:56px;color:var(--lime);', '→', 'h');
  const tools = ['Google Docs', 'Google Slides', 'Naver Blog'].map((name, i) => {
    const card = A(s, `left:1260px;top:${320 + i * 190}px;width:580px;height:160px;`, '', 'card');
    A(card, 'left:28px;top:24px;font-size:31px;', name, 'h');
    A(card, 'left:28px;top:86px;font-size:21px;color:#b9cabb;', 'Outline · writing · review');
    A(card, 'right:22px;top:28px;', '<span class="chip lime" style="font-size:14px">Your standard</span>');
    return card;
  });
  A(s, 'left:80px;top:890px;font-size:18px;color:#b9cabb;', 'Across compatible tools through your AI host · human review still matters.', 'mono');
  s.update = (lt) => {
    show(memory, fade(lt, 0.3, 0.9), 18);
    show(host, fade(lt, 2.1, 2.8), 16);
    show(arrowA, fade(lt, 1.5, 2.0), 0); show(arrowB, fade(lt, 3.0, 3.5), 0);
    tools.forEach((card, i) => show(card, fade(lt, 3.6 + i * 0.55, 4.2 + i * 0.55), 18));
  };
}

function buildContributionCredit() {
  const s = addScene('community', { badge: 'example' });
  const rep = SCRIPT.feature_examples.reputation;
  A(s, 'left:80px;top:132px;font-size:70px;white-space:nowrap;', 'Useful memory earns its author credit.', 'h');
  A(s, 'left:80px;top:232px;font-size:28px;color:var(--muted);', 'Contribute. Get reviewed. Help someone else start faster.');
  const flow = A(s, 'left:80px;top:320px;width:720px;height:552px;', '', 'card');
  A(flow, 'left:30px;top:26px;', 'A CONTRIBUTION THAT TRAVELS', 'label');
  const steps = [
    ['Contribute a template', 'Keep the useful structure and attribution.'],
    ['Approved and public', 'The submitted snapshot is reviewed first.'],
    ['Someone else reuses it', 'Eligible reuse gives the author credit.']
  ].map(([head, sub], i) => {
    const card = A(flow, `left:30px;top:${82 + i * 135}px;width:660px;height:108px;border-radius:16px;background:#edf2e6;`, '', 'card');
    A(card, 'left:22px;top:20px;font-size:29px;white-space:nowrap;', head, 'h');
    A(card, 'left:22px;top:64px;font-size:20px;color:var(--muted);white-space:nowrap;', sub);
    return card;
  });
  A(flow, 'left:30px;top:505px;font-size:17px;color:var(--muted);', 'Your private reference files are not contributed.', 'mono');
  const board = A(s, 'left:880px;top:320px;width:960px;height:552px;', '', 'card');
  A(board, 'left:30px;top:26px;', 'EXAMPLE LEADERBOARD', 'label');
  A(board, 'left:30px;top:66px;font-size:43px;', 'Good work travels.', 'h');
  A(board, 'left:750px;top:83px;font-size:15px;', 'POINTS', 'label');
  const rows = ['Avery', 'Jordan', 'Morgan'].map((name, i) => {
    const row = A(board, `left:30px;top:${145 + i * 94}px;width:900px;height:82px;border:1px solid #dce4d5;border-radius:14px;background:#f1f5ed;`);
    A(row, 'left:20px;top:29px;font-size:19px;color:var(--muted);', `0${i + 1}`, 'mono');
    A(row, 'left:80px;top:15px;font-size:29px;', name, 'h');
    A(row, 'left:80px;top:54px;font-size:16px;color:var(--muted);', i === 0 ? 'Approved memory · reused by another member' : 'Reviewed public contribution');
    const score = A(row, 'left:728px;top:23px;font-size:35px;', '', 'h');
    return { row, score };
  });
  const bonus = A(board, 'left:30px;top:448px;', '', 'chip lime');
  A(board, 'left:30px;top:505px;font-size:16px;color:var(--muted);', rep.rule || 'Example data · contribution policy applies.', 'mono');
  s.update = (lt) => {
    steps.forEach((step, i) => show(step, fade(lt, 0.6 + i * 1.5, 1.2 + i * 1.5), 12));
    show(board, fade(lt, 2.6, 3.2), 18);
    const earned = lt >= 6.6;
    rows.forEach(({ row, score }, i) => {
      setText(score, String(i === 0 ? (earned ? rep.after : rep.before) : Math.max(0, rep.before - i * 2)));
      row.style.background = i === 0 && earned ? '#e3efbf' : '#f1f5ed';
    });
    setText(bonus, `+${rep.increment} for qualifying reuse`);
    show(bonus, fade(lt, 6.6, 7.1), 12);
  };
}

window.__buildExtraScenes = () => {
  buildCompanyFormats();
  buildSharedStandard();
  buildContributionCredit();
};
