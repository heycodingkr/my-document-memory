<script lang="ts">
 let {locale='en',onpublic}:{locale?:'en'|'ko';onpublic:()=>void}=$props();
 const copy={
  en:{
   kicker:'FREE TEMPLATES. YOUR CHOICE OF AI.',title:'Start free.',titleNext:'Bring the AI you already use.',summary:'Different templates. A lightweight model.',summaryNext:'The document tools you know.',
   benefits:[
    {index:'01 / FREE TEMPLATES',title:'A format for every task.',body:'Browse and reuse free templates for reports, meeting notes, project plans, and pitch decks. Keep the structure and writing rules for next time.'},
    {index:'02 / YOUR AI',title:'Luna can start here too.',body:'Give a lightweight model such as Luna the chosen template, writing rules, and source notes through your connected AI host. Review the facts and open questions.'},
    {index:'03 / FREE DOCUMENT TOOLS',title:'Finish in the tools you know.',body:'Export DOCX for Google Docs, PPTX for Google Slides, or Markdown for Notion. Review, edit, and make the document your own.'}
   ],
   browse:'Browse free templates',scope:'Browse and reuse our templates for free. Google Docs and Google Slides offer free editing with a Google Account; Notion offers a Free plan. AI host, model, and API costs depend on your provider; service plan limits apply.',planInfo:'Account and plan details:',
   evidence:'Early evidence: Luna + WAM memory',evidenceIntro:'In WAM’s 2026-10-31 Canva experiment, gpt-6-luna/max completed the full task and independent file checks in both conditions.',
   toolsOnly:'Tools only',withMemory:'Supplied WAM hints',toolsMetric:'474 seconds / 123 tool boundaries',memoryMetric:'423 seconds / 106 tool boundaries',report:'Read the original WAM report',
   limits:'A preliminary observation: one run per condition, with different templates and upload paths. Reported tokens were higher with hints; billing was unmeasured. General speed or cost savings are unproven. My Document Memory’s own document-writing benchmarks are pending.'
  },
  ko:{
   kicker:'무료 템플릿. 원하는 AI와 함께.',title:'무료로 시작하세요.',titleNext:'쓰던 AI와 함께.',summary:'여러 템플릿과 Luna 같은 경량 모델.',summaryNext:'익숙한 문서 도구에서 이어 쓰세요.',
   benefits:[
    {index:'01 / 무료 템플릿',title:'문서마다 알맞은 시작점.',body:'보고서, 회의록, 프로젝트 계획, 피치덱 템플릿을 무료로 찾아 재사용하세요. 문서 구조와 작성 규칙은 다음 작업에도 이어 쓸 수 있습니다.'},
    {index:'02 / 내가 쓰는 AI',title:'Luna 같은 경량 모델로도.',body:'연결된 AI 호스트를 통해 Luna 같은 경량 모델에 고른 템플릿, 작성 규칙, 참고 메모를 전달하세요. 작성된 내용의 사실과 확인할 항목을 검토하면 됩니다.'},
    {index:'03 / 무료 문서 도구',title:'익숙한 도구에서 마무리.',body:'Google Docs에는 DOCX, Google Slides에는 PPTX, Notion에는 Markdown으로 내보내 이어 쓰세요. 검토하고 수정해 나만의 문서로 완성하세요.'}
   ],
   browse:'무료 템플릿 둘러보기',scope:'템플릿 탐색과 재사용은 무료입니다. Google Docs와 Google Slides는 Google 계정으로 무료 편집할 수 있고, Notion은 Free 요금제를 제공합니다. AI 호스트·모델·API 비용과 각 서비스의 이용 한도는 선택한 제공업체에 따라 달라집니다.',planInfo:'계정과 요금제 안내:',
   evidence:'초기 실험: Luna + WAM 메모리',evidenceIntro:'2026-10-31 WAM의 Canva 실험에서 gpt-6-luna/max는 두 조건 모두 전체 작업과 독립 파일 검증을 통과했습니다.',
   toolsOnly:'도구만 사용',withMemory:'WAM 힌트 제공',toolsMetric:'474초 / 외부 도구 경계 123회',memoryMetric:'423초 / 외부 도구 경계 106회',report:'원본 WAM 실험 보고서',
   limits:'조건별 1회 실행한 예비 관찰이며, 템플릿과 업로드 경로가 달랐습니다. 힌트를 준 조건에서 보고된 토큰 수는 더 많았고 실제 청구 비용은 측정하지 않았습니다. 일반적인 속도·비용 절감은 아직 입증하지 못했습니다. My Document Memory 자체의 문서 작성 벤치는 준비 중입니다.'
  }
 } as const;
 const text=$derived(copy[locale]);
 const reportUrl='https://github.com/heycodingkr/web-agentic-memory/blob/04cb13318acb0c7dff7734b6613325c361deb827/docs/test/benchmarks/canva.md';
</script>

<section class="free-template-section" id="start-free" aria-labelledby="free-templates-title">
 <div class="section-heading"><div><span class="kicker">{text.kicker}</span><h2 id="free-templates-title">{text.title}<br/>{text.titleNext}</h2></div><p>{text.summary}<br/>{text.summaryNext}</p></div>
 <div class="template-benefits">
  {#each text.benefits as benefit}
   <article><span class="benefit-index">{benefit.index}</span><h3>{benefit.title}</h3><p>{benefit.body}</p></article>
  {/each}
 </div>
 <div class="free-template-action">
  <button class="browse-templates" onclick={onpublic}>{text.browse} <span aria-hidden="true">→</span></button>
  <div class="free-template-scope"><p>{text.scope}</p><p class="plan-links">{text.planInfo} <a href="https://workspace.google.com/products/docs/" target="_blank" rel="noreferrer noopener">Google Docs</a> · <a href="https://workspace.google.com/products/slides/" target="_blank" rel="noreferrer noopener">Google Slides</a> · <a href="https://www.notion.com/pricing" target="_blank" rel="noreferrer noopener">Notion</a></p></div>
 </div>
 <details class="memory-evidence">
  <summary>{text.evidence}</summary>
  <p>{text.evidenceIntro} {text.toolsOnly}: <strong>{text.toolsMetric}</strong>; {text.withMemory}: <strong>{text.memoryMetric}</strong>. <a href={reportUrl} target="_blank" rel="noreferrer noopener">{text.report} ↗</a></p>
  <p>{text.limits}</p>
 </details>
</section>

<style>
 .free-template-section{padding-block:32px 55px;scroll-margin-top:24px}
 .section-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:35px}
 .kicker{font-size:9px;letter-spacing:.12em;color:#728963}
 h2{font-size:34px;line-height:1.4;font-weight:550;margin:12px 0 0;letter-spacing:-.055em}
 .section-heading>p{font-size:12px;color:var(--landing-muted,#64756b);line-height:1.9;margin:0}
 .template-benefits{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
 article{min-width:0;padding:26px 24px;background:#edf2e6;border:1px solid #dce5d3;border-radius:6px}
 .benefit-index{font-size:9px;letter-spacing:.08em;color:#6d815f}
 h3{font-size:21px;line-height:1.5;font-weight:500;letter-spacing:-.035em;margin:14px 0 11px}
 article p{font-size:13px;line-height:1.85;color:var(--landing-muted,#64756b);margin:0}
 .free-template-action{display:flex;align-items:flex-start;gap:25px;margin-top:23px}
 .browse-templates{display:inline-flex;align-items:center;justify-content:center;gap:13px;flex:none;white-space:nowrap;padding:14px 19px;background:#617e48;color:#fffef5;border:1px solid #617e48;border-radius:4px;font:inherit;font-size:13px;cursor:pointer}
 .browse-templates:hover{background:#506d3b}
 .free-template-scope{font-size:12px;line-height:1.9;color:var(--landing-muted,#64756b)}
 .free-template-scope p{margin:0}.free-template-scope .plan-links{margin-top:7px}
 a{text-decoration:underline;text-underline-offset:3px;color:#45653b}
 .memory-evidence{margin-top:22px;padding-top:18px;border-top:1px solid var(--landing-line,#dce3d8);font-size:12px;line-height:1.9;color:var(--landing-muted,#64756b)}
 summary{cursor:pointer;font-size:13px;font-weight:550;color:#3b583e}
 .memory-evidence p{max-width:920px;margin:14px 0 0}
 summary:focus-visible,a:focus-visible,.browse-templates:focus-visible{outline:3px solid #527844;outline-offset:4px}
 @media(max-width:850px){.template-benefits{grid-template-columns:1fr}article{padding:23px}h3{font-size:22px}.free-template-action{flex-direction:column;gap:17px}h2{font-size:30px}}
 @media(max-width:580px){.free-template-section{padding-block:24px 36px}.section-heading{display:block;margin-bottom:24px}.section-heading>p{font-size:11px;margin-top:13px}h2{font-size:28px}.free-template-scope{font-size:11px}}
</style>
