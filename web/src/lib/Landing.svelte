<script lang="ts">
 import {onDestroy,onMount} from 'svelte';
 import AgentSetup from './AgentSetup.svelte';
 import DocumentPreview from './DocumentPreview.svelte';
 import FreeTemplates from './FreeTemplates.svelte';
 import ServiceLogo from './ServiceLogo.svelte';
 import WorkflowDemo from './WorkflowDemo.svelte';
 import {landingCopy,type LandingLocale} from './landing-copy';
 type Tool='docs'|'slides'|'notion';
 let {token=$bindable(''),connected=false,working=false,error='',onconnect,onreturn,onlogin,onpublic,onsignup,onleaderboard}:{token:string;connected:boolean;working:boolean;error:string;onconnect:()=>Promise<void>;onreturn:()=>void;onlogin:()=>void;onpublic:()=>void;onsignup:()=>void;onleaderboard:()=>void;}=$props();
 let locale=$state<LandingLocale>('en');
 let selected=$state<Tool>('docs');
 let model=$state('Codex');
 let copyStatus=$state<'success'|'manual'|''>('');
 const page=$derived(landingCopy[locale].landing);
 const tools=$derived(page.tools);
 const outputExamples=$derived(page.documentExamples.cards);
 const useCases=$derived(page.useCases.items);
 const active=$derived(tools.find(tool=>tool.id===selected)!);
 const activeOutput=$derived(outputExamples[selected]);
 const prompt=$derived([page.prompt.prefix,active.request,page.prompt.suffix].join(String.fromCharCode(10)+String.fromCharCode(10)));
 const mcpConfig=JSON.stringify({mcpServers:{'document-memory':{command:'/absolute/path/my-document-memory/target/debug/dmem-mcp',env:{DMEM_URL:'http://127.0.0.1:3847',DMEM_TOKEN:'<DMEM_TOKEN from your .env>'}}}},null,2);
 onMount(()=>{
  try{
   const saved=window.localStorage.getItem('dmem.landing-locale');
   if(saved==='en'||saved==='ko')locale=saved;
  }catch{}
 });
 $effect(()=>{
  const selectedLocale=locale;
  const copy=landingCopy[selectedLocale];
  document.documentElement.lang=selectedLocale;
  document.title=copy.title;
  document.querySelector('meta[name="description"]')?.setAttribute('content',copy.description);
 });
 onDestroy(()=>{
  document.documentElement.lang='en';
  document.title=landingCopy.en.title;
  document.querySelector('meta[name="description"]')?.setAttribute('content',landingCopy.en.description);
 });
 function toggleLanguage(){
  locale=locale==='en'?'ko':'en';
  copyStatus='';
  try{window.localStorage.setItem('dmem.landing-locale',locale);}catch{}
 }
 function selectTool(tool:Tool){selected=tool;copyStatus='';}
 function toolKey(event:KeyboardEvent,index:number){
  let next=index;
  if(event.key==='ArrowRight')next=(index+1)%tools.length;
  else if(event.key==='ArrowLeft')next=(index+tools.length-1)%tools.length;
  else if(event.key==='Home')next=0;
  else if(event.key==='End')next=tools.length-1;
  else return;
  event.preventDefault();selectTool(tools[next].id);document.getElementById('example-tab-'+tools[next].id)?.focus();
 }
 async function copyPrompt(){
  try{
   if(!navigator.clipboard?.writeText)throw new Error('clipboard_unavailable');
   await navigator.clipboard.writeText(prompt);
   copyStatus='success';
  }catch{copyStatus='manual';}
 }
</script>

<div class="landing" data-locale={locale}>
 <a class="skip-link" href="#intro">{page.skip}</a>
 <header class="landing-header">
  <a class="wordmark" href="#intro" aria-label={page.brandHome}>
   <svg width="29" height="33" viewBox="0 0 34 38" fill="none" aria-hidden="true"><path d="M7 2h15l8 8v25H7zM22 2v9h8M12 17h13M12 23h10M12 29h7M2 8v29h22" stroke="currentColor" stroke-width="1.7"/></svg>
   <span>my document <strong>memory<span>.</span></strong></span>
  </a>
  <nav class="landing-nav" aria-label={page.navLabel}>
   <div class="landing-links">
    <a href="#about">{page.nav.about}</a>
    <a href="#how-it-works">{page.nav.how}</a>
    <a class="examples-nav" href="#document-examples">{page.nav.examples}</a>
    <a href="#connect-agent">{page.nav.connect}</a>
    <a href="https://github.com/heycodingkr/my-document-memory" target="_blank" rel="noreferrer noopener">{page.nav.github}</a>
   </div>
   <div class="nav-actions">
    <button class="language-toggle" aria-label={landingCopy[locale].languageButtonAria} onclick={toggleLanguage}>{landingCopy[locale].languageButton}</button>
    <button class="text-button" onclick={onleaderboard}>{locale==='ko'?'리더보드':'Leaderboard'}</button>
    <button class="text-button" onclick={onpublic}>{page.nav.public}</button>
    {#if connected}<button class="nav-library" onclick={onreturn}>{page.nav.space}</button>{:else}<button class="nav-library" onclick={onlogin}>{page.nav.signIn} <span aria-hidden="true">↗</span></button><button class="nav-library" onclick={onsignup}>{locale==='ko'?'가입하기':'Create account'}</button>{/if}
   </div>
  </nav>
 </header>

 <main id="intro">
  <section class="hero section-width" aria-labelledby="hero-title">
   <div class="hero-copy">
    <span class="kicker"><i aria-hidden="true"></i> {page.hero.kicker}</span>
    <h1 id="hero-title">{page.hero.title} <br/><span>{page.hero.subtitle}</span></h1>
    <p class="hero-description">{page.hero.description}<br class="desktop-break"/> {page.hero.descriptionNext}</p>
    <p class="hero-detail">{page.hero.detail}<br class="desktop-break"/> {page.hero.detailNext}</p>
    <div class="hero-actions"><a class="action action-primary" href="#get-started">{page.hero.getStarted} →</a><a class="action action-text" href="#workflow-demo">{page.hero.watchDemo} <span aria-hidden="true">↓</span></a></div>
    <div class="hero-resources"><button onclick={connected?onreturn:onlogin}>{connected?page.hero.openSpace+' →':page.hero.startEmail+' →'}</button><a href="https://github.com/heycodingkr/my-document-memory" target="_blank" rel="noreferrer noopener">{page.hero.viewGithub} ↗</a><span>{page.hero.resources}</span></div>
    <div class="model-picker"><label for="example-model">{page.hero.modelLabel}</label><select id="example-model" aria-label={page.hero.modelAria} bind:value={model}><option>Codex</option><option>Claude</option><option>Muse</option></select><span class="ai-brands" aria-label={page.hero.brandsAria}><span><ServiceLogo service="codex"/>OpenAI</span><span><ServiceLogo service="claude"/>Claude</span><span>Muse</span></span></div>
   </div>

   <div class="workflow-example">
    <div class="example-caption"><span><i aria-hidden="true"></i> {page.workflowExample.caption}</span><span>{page.workflowExample.label}</span></div>
    <div class="tool-tabs" role="tablist" aria-label={page.workflowExample.tabsAria}>
     {#each tools as tool,i}<button id={'example-tab-'+tool.id} role="tab" aria-selected={selected===tool.id} aria-controls="example-panel" tabindex={selected===tool.id?0:-1} class:chosen={selected===tool.id} onclick={()=>selectTool(tool.id)} onkeydown={(event)=>toolKey(event,i)}><span class={'tool-icon '+tool.id} aria-hidden="true"><ServiceLogo service={tool.id}/></span>{tool.name}</button>{/each}
    </div>
    <div class="example-body" id="example-panel" role="tabpanel" aria-labelledby={'example-tab-'+selected} tabindex="0">
     <div class="context-strip"><span class="context-symbol" aria-hidden="true">✳</span><div><strong>{page.workflowExample.contextTitle}</strong><span>{page.workflowExample.contextDetail}</span></div><span class="context-check" aria-hidden="true">✓</span></div>
     <div class={'hero-output '+activeOutput.kind}><DocumentPreview kind={activeOutput.kind} locale={locale}/></div>
     <div class="hero-output-title"><strong>{activeOutput.title}</strong><span>{activeOutput.destination}</span></div>
     <div class="example-footer"><span><span class="tiny-dot"></span> {model} {locale==='en'?'with the same context':'· 같은 맥락 사용'}</span><a href={activeOutput.href} target="_blank" rel="noreferrer noopener" aria-label={activeOutput.ariaLabel}>{page.workflowExample.openExample} ↗</a></div>
    </div>
    <p class="example-disclosure">{page.workflowExample.previewNote}</p>
   </div>
  </section>

  <section class="about-section section-width" id="about" aria-labelledby="about-title">
   <div class="section-heading about-heading"><div><span class="kicker">{page.about.kicker}</span><h2 id="about-title">{page.about.title}<br/>{page.about.titleNext}</h2></div><p>{page.about.summary}</p></div>
   <p class="about-story">{page.about.story}</p>
   <div class="about-values">{#each page.about.items as item}<article><span class="about-index">{item.index}</span><h3>{item.title}</h3><p>{item.description}</p></article>{/each}</div>
  </section>

  <section class="memory-savings section-width" id="expected-savings" aria-labelledby="savings-title">
   <div class="section-heading"><div><span class="kicker">{page.savings.kicker}</span><h2 id="savings-title">{page.savings.title}</h2></div><p>{page.savings.description}</p></div>
   <dl class="savings-metrics">{#each page.savings.metrics as metric}<div><dt>{metric.label}</dt><dd>{metric.value}</dd></div>{/each}</dl>
   <p class="savings-example">{page.savings.example}</p>
   <p class="savings-note">{page.savings.note} <a href="https://github.com/heycodingkr/web-agentic-memory/blob/f0fdcb434916cb5ed6819546ac12ce00a3fe5e0d/web/src/lib/landing.ts#L63" target="_blank" rel="noreferrer noopener">{page.savings.source} ↗</a></p>
  </section>

  <section class="document-examples section-width" id="document-examples" aria-labelledby="document-examples-title">
   <div class="section-heading"><div><span class="kicker">{page.documentExamples.kicker}</span><h2 id="document-examples-title">{page.documentExamples.title}<br/>{page.documentExamples.titleNext}</h2></div><p>{page.documentExamples.summary}<br/>{page.documentExamples.summaryNext}</p></div>
   <div class="example-gallery">{#each Object.values(outputExamples) as example}
    <a class={'document-example '+example.kind} href={example.href} target="_blank" rel="noreferrer noopener" aria-label={example.ariaLabel}>
     <div class="example-art"><DocumentPreview kind={example.kind} locale={locale}/></div>
     <div class="example-card-copy"><span class="example-kind">{example.label} <span aria-hidden="true">↗</span></span><h3>{example.title}</h3><p>{example.description}</p><span class="example-destination">{example.destination}</span><span class="example-open">{page.workflowExample.openExample} ↗</span></div>
    </a>
   {/each}</div>
   <p class="examples-note">{page.documentExamples.note}</p>
  </section>

  <div class="section-width"><WorkflowDemo {model} {locale}/></div>

  <section class="how-section section-width" id="how-it-works" aria-labelledby="how-title">
   <div class="section-heading"><div><span class="kicker">{page.how.kicker}</span><h2 id="how-title">{page.how.title}<br/>{page.how.titleNext}</h2></div><p>{page.how.summary}<br/>{page.how.summaryNext}</p></div>
   <ol class="how-steps">{#each page.how.steps as step}<li><span class="how-number">{step.index}</span><h3>{step.title}</h3><p>{step.description}</p><span class="how-example">{step.example}</span></li>{/each}</ol>
   <div class="browser-setup"><div><span class="kicker">{page.how.browserSetup.kicker}</span><h3>{page.how.browserSetup.title}</h3><p>{page.how.browserSetup.description}</p></div><div class="browser-downloads"><a class="action action-primary" href="https://arisebrowser.com/#download" target="_blank" rel="noreferrer noopener">{page.how.browserSetup.arise}</a><a class="action chrome-download" href="https://www.google.com/chrome/" target="_blank" rel="noreferrer noopener">{page.how.browserSetup.chrome}</a><a class="browser-setup-guide" href="https://arisebrowser.com/blog/connect-ai-agent-to-browser-mcp/" target="_blank" rel="noreferrer noopener">{page.how.browserSetup.guide} ↗</a></div></div>
  </section>

  <div class="section-width"><FreeTemplates {locale} {onpublic}/></div>

  <section class="destinations use-cases section-width" id="what-it-does" aria-labelledby="destinations-title">
   <div class="section-heading compact"><div><span class="kicker">{page.useCases.kicker}</span><h2 id="destinations-title">{page.useCases.title}<br/>{page.useCases.titleNext}</h2></div><p>{page.useCases.summary}<br/>{page.useCases.summaryNext}</p></div>
   <div class="destination-list">
    {#each useCases as example}<a class="destination" href={example.url} target="_blank" rel="noreferrer noopener"><span class={'tool-icon '+example.id} aria-hidden="true"><ServiceLogo service={example.id}/></span><div><h3>{example.name} <span aria-hidden="true">↗</span></h3><p class="case-kind">{example.kind}</p><p class="case-request">“{example.request}”</p><span class="format-route"><strong>{page.useCases.memoryLabel}</strong>{example.memory}</span></div></a>{/each}
    <aside class="same-memory"><span class="kicker">{page.useCases.sameMemory.kicker}</span><h3>{page.useCases.sameMemory.title}<br/>{page.useCases.sameMemory.titleNext}</h3><p>{page.useCases.sameMemory.description}</p><small>{page.useCases.sameMemory.goal}</small></aside>
   </div>
   <p class="route-note">{page.useCases.routeNote}</p>
  </section>

  <section class="principles" id="document-memory" aria-labelledby="principles-title">
   <div class="section-width principles-inner"><div><span class="kicker">{page.principles.kicker}</span><h2 id="principles-title">{page.principles.title}<br/>{page.principles.titleNext}</h2><p>{page.principles.summary}<br/>{page.principles.summaryNext}</p></div><dl>{#each page.principles.items as item}<div><dt><span>{item.label}</span>{item.title}</dt><dd>{item.description}<br/>{item.descriptionNext}</dd></div>{/each}</dl></div>
  </section>

  <div class="section-width"><AgentSetup {onlogin} {onpublic} {connected} {onreturn} {locale}/></div>

  <section class="getting-started section-width" id="get-started" aria-labelledby="start-title">
   <div class="section-heading"><div><span class="kicker">{page.gettingStarted.kicker}</span><h2 id="start-title">{page.gettingStarted.title}</h2></div><p>{page.gettingStarted.summary}<br/>{page.gettingStarted.summaryNext}</p></div>
   <div class="start-grid">
    <ol class="steps">{#each page.gettingStarted.steps as step,i}<li><span class="step-number">{String(i+1).padStart(2,'0')}</span><div><h3>{step.title}</h3><p>{step.description}</p>{#if 'link' in step&&step.link}<a href="#library-connection">{step.link} →</a>{/if}{#if 'aside' in step&&step.aside}<span class="step-aside">{step.aside}</span>{/if}</div></li>{/each}</ol>
    <div class="prompt-example"><div class="prompt-heading"><span class="kicker">{page.gettingStarted.promptKicker}</span><span class="prompt-mark" aria-hidden="true">↗</span></div><h3>{model} {page.gettingStarted.promptHeading}</h3><span class="prompt-destination">{page.gettingStarted.promptDestination} · {active.name}</span><pre aria-label={page.gettingStarted.promptAria}>{prompt}</pre><div class="prompt-actions"><span>{page.gettingStarted.promptHint}</span><button class="copy-button" onclick={copyPrompt}>{page.gettingStarted.copy} <span aria-hidden="true">⧉</span></button></div><p class="copy-status" role="status" aria-live="polite">{copyStatus==='success'?(locale==='en'?'Request copied. Paste it into your connected AI.':'요청을 복사했습니다. 연결된 AI에 붙여 넣으세요.'):copyStatus==='manual'?(locale==='en'?'Automatic copying is unavailable. Select the request and copy it manually.':'자동 복사를 사용할 수 없습니다. 요청을 선택해 직접 복사하세요.'):''}</p></div>
   </div>
   <details class="setup-details"><summary>{page.gettingStarted.setupSummary}</summary><div class="setup-grid"><div><span class="setup-number">{page.gettingStarted.webSetup.index}</span><h3>{page.gettingStarted.webSetup.title}</h3><p>{page.gettingStarted.webSetup.description}</p><pre><code>node scripts/dev.mjs</code></pre><p>{page.gettingStarted.webSetup.tokenInfo}</p></div><div><span class="setup-number">{page.gettingStarted.aiSetup.index}</span><h3>{page.gettingStarted.aiSetup.title}</h3><p>{page.gettingStarted.aiSetup.description}</p><pre aria-label={page.gettingStarted.aiSetup.configAria}><code>{mcpConfig}</code></pre><p>{page.gettingStarted.aiSetup.statusInfo}</p></div></div></details>
  </section>

  <section class="browser-section section-width" aria-labelledby="browser-title"><div class="browser-graphic" aria-hidden="true"><div class="browser-chrome"><i></i><i></i><i></i><span>{page.browser.graphicLabel}</span></div><div class="browser-flow"><span>AI</span><span class="flow-line">↔</span><span class="browser-name"><ServiceLogo service="arise"/>Arise<span>Browser</span></span><span class="flow-line">↔</span><span>WEB</span></div><div class="browser-bottom">{page.browser.graphicBottom}</div></div><div class="browser-copy"><span class="kicker">{page.browser.kicker}</span><h2 id="browser-title">{page.browser.title}<br/>{page.browser.titleNext}</h2><p>{page.browser.description}</p><div class="browser-links"><a href="https://arisebrowser.com/" target="_blank" rel="noreferrer noopener">{page.browser.explore} ↗</a><a href="https://arisebrowser.com/blog/connect-ai-agent-to-browser-mcp/" target="_blank" rel="noreferrer noopener">{page.browser.guide} ↗</a></div><small>{page.browser.note}</small></div></section>

  <section class="connection-section section-width" id="library-connection" aria-labelledby="connection-title"><div><span class="kicker">{page.connection.kicker}</span><h2 id="connection-title">{page.connection.title}<br/>{page.connection.titleNext}</h2><p>{page.connection.description}</p></div><div class="connection-content">{#if connected}<p class="connected-label"><span class="tiny-dot"></span> {page.connection.connected}</p><button class="action action-primary" onclick={onreturn}>{page.connection.return} →</button>{:else}<form onsubmit={(event)=>{event.preventDefault();void onconnect();}}><label for="token">{page.connection.tokenLabel}</label><div class="token-row"><input id="token" type="password" autocomplete="off" bind:value={token} required minlength="16" placeholder={page.connection.tokenPlaceholder}/><button class="action action-primary" disabled={working}>{working?page.connection.connecting:page.connection.openLibrary+' →'}</button></div><small>{page.connection.tokenHelp}</small>{#if error}<p class="connection-error" role="alert">{locale==='ko'?page.connection.error:error}</p>{/if}</form>{/if}<p class="scope-note">{page.connection.scope}</p></div></section>
 </main>

 <footer class="landing-footer section-width"><span class="footer-wordmark">my document memory<span>.</span></span><p>{page.footer.tagline}</p><a class="source-link" href="https://github.com/heycodingkr/my-document-memory" target="_blank" rel="noreferrer noopener">{page.footer.source} ↗</a><span class="pricing-note">{page.footer.pricing}<br/>{page.footer.pricingNext}</span></footer>
</div>

<style>
 .landing{--landing-muted:#64756b;--landing-line:#dce3d8;background:#fafbf7;color:#263e32;overflow-wrap:break-word}
 .section-width{width:min(1160px,calc(100% - 96px));margin-inline:auto}
 .kicker{display:block;font-size:10px;font-weight:650;letter-spacing:.13em;line-height:1.7;color:#6c7d64}
 .skip-link{position:absolute;left:20px;top:-60px;background:#244e3c;color:#fff;padding:12px;z-index:10}.skip-link:focus{top:12px}
 .landing-header{max-width:1440px;margin:auto;padding:27px 48px;display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:1px solid var(--landing-line)}
 .wordmark{display:flex;align-items:center;gap:10px;line-height:1.1;letter-spacing:-.04em;font-size:13px;flex:none}.wordmark strong{display:block;font-size:24px;font-weight:600}.wordmark strong span{color:#8ca275}
 .landing-nav{display:flex;align-items:center;gap:22px;font-size:12px}.landing-links>a{color:#5d7062}.nav-library{display:flex;gap:20px;align-items:center;background:#eaf0e2;padding:12px 17px;border:1px solid #dbe4d2;border-radius:5px;font-size:12px;font-weight:600}
 .hero{display:grid;grid-template-columns:1.12fr 1fr;gap:54px;align-items:center;padding-top:78px;padding-bottom:69px}
 .hero .kicker{display:flex;align-items:center;gap:9px;font-size:9px;letter-spacing:.11em}.hero-copy .kicker i,.example-caption i{width:6px;height:6px;display:inline-block;background:#8ca16c;border-radius:50%}
 .hero h1{font-size:clamp(32px,3.35vw,48px);font-weight:600;line-height:1.4;letter-spacing:-.065em;margin:24px 0}.hero h1>span{color:#6b835a}
 .hero-description{font-size:18px;line-height:1.8;letter-spacing:-.03em;margin-bottom:15px}.hero-detail{font-size:13px;color:var(--landing-muted);line-height:1.95;margin-bottom:29px;letter-spacing:-.015em}
 .hero-actions{display:flex;gap:12px;align-items:center}.action{display:inline-flex;align-items:center;justify-content:center;gap:18px;font-size:12px;font-weight:600;padding:14px 21px;border-radius:5px;line-height:1.5;white-space:nowrap}.action-primary{background:#284f3c;color:#fff;border:1px solid #284f3c}.action-primary:hover:enabled,.action-primary[href]:hover{background:#386347}.action-text{padding-inline:12px;color:#5c7257}.action-text span{font-size:16px}
 .model-picker{display:flex;align-items:center;gap:10px;padding-top:28px;font-size:10px;color:#6d7d69}.model-picker select{font-size:11px;background:#f4f6ef;border-color:#dce4d5;padding:7px 23px 7px 10px;border-radius:4px;color:#3b563c;min-width:95px}.model-picker>span{font-size:10px;color:#7b8876}
 .workflow-example{min-width:0;position:relative;padding-top:7px}.example-caption{display:flex;justify-content:space-between;font-size:8px;letter-spacing:.08em;color:#758268;margin:0 2px 13px}.example-caption>span:first-child{display:flex;align-items:center;gap:7px}
 .tool-tabs{display:flex;background:#f0f3e9;border:1px solid #d9e1d1;border-bottom:0;border-radius:9px 9px 0 0;padding:9px 9px 0;gap:3px}.tool-tabs button{display:flex;align-items:center;justify-content:center;gap:7px;flex:1;padding:10px 6px 13px;border-radius:5px 5px 0 0;color:#7b8972;font-size:10px;white-space:nowrap;border:1px solid transparent;border-bottom:0}.tool-tabs button.chosen{background:#fffef9;color:#334f37;border-color:#dde4d5;box-shadow:0 2px 0 #fffef9}.tool-icon{width:26px;height:30px;display:inline-grid;place-items:center;border-radius:3px;font-family:Arial,sans-serif;font-size:15px;font-weight:600;flex:none}.tool-icon.docs{color:#fff;background:#6d8e9c}.tool-icon.slides{color:#fff;background:#b99c59}.tool-icon.notion{color:#465044;background:#fff;border:1px solid #bfc7b9;font-family:Georgia,serif}.tool-tabs .tool-icon{width:16px;height:19px;font-size:10px;border-radius:2px}
 .example-body{background:#fffef9;padding:19px;border:1px solid #d9e1d1;border-top:0;border-radius:0 0 9px 9px;box-shadow:0 14px 28px #3b51200a;min-width:0}.context-strip{display:flex;align-items:center;gap:10px;padding:11px 13px;background:#f0f4e9;border:1px solid #e2e8d9;border-radius:5px}.context-symbol{font-size:25px;color:#7b925f}.context-strip strong{display:block;font-size:10px;font-weight:600;margin-bottom:3px}.context-strip div>span{font-size:9px;color:#7c8972}.context-check{margin-left:auto;background:#e0e8d1;width:22px;height:22px;display:grid;place-items:center;border-radius:50%;font-size:11px;color:#6b8050}
 .example-footer{display:flex;justify-content:space-between;align-items:center;gap:9px;font-size:8px;color:#859177}.example-footer>span:first-child{display:flex;align-items:center;gap:5px}.tiny-dot{display:inline-block;width:5px;height:5px;background:#85a069;border-radius:50%;flex:none}.example-disclosure{font-size:9px;color:#85917e;text-align:center;margin:13px 0 0;line-height:1.7}
 .destinations{padding:20px 0 56px}.section-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:35px}.section-heading h2{font-size:34px;line-height:1.4;font-weight:550;margin:12px 0 0;letter-spacing:-.055em}.section-heading>p{font-size:12px;color:var(--landing-muted);line-height:1.9;margin:0}.section-heading.compact{margin-bottom:25px}.compact h2{font-size:25px;margin-top:10px}.compact .kicker{font-size:8px}
 .destination-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-block:1px solid var(--landing-line)}.destination{display:flex;align-items:flex-start;gap:17px;padding:25px 23px 25px 0}.destination+.destination{border-left:1px solid var(--landing-line);padding-left:30px}.destination h3{font-size:15px;letter-spacing:-.025em;font-weight:550;margin:0 0 7px}.destination h3>span{color:#8e9a80;font-size:13px;display:inline-block;margin-left:9px}.destination p{font-size:10px;color:#7d8a73;margin:0 0 13px}.format-route{font-size:10px;color:#4e6b48}.destination:hover h3{color:#6b8755}.route-note{font-size:10px;line-height:1.9;margin:14px 0 0;color:#7d8975}
 .principles{background:#edf2e6;border-block:1px solid #e3e9db;scroll-margin-top:24px}.principles-inner{display:grid;grid-template-columns:1fr 1fr;gap:100px;padding-block:59px}.principles .kicker{font-size:8px}.principles h2{font-size:32px;font-weight:500;line-height:1.65;letter-spacing:-.055em;margin:15px 0 16px}.principles p{font-size:12px;line-height:1.95;color:#728267;margin:0}.principles dl{margin:0}.principles dl>div{padding:17px 0;border-bottom:1px solid #d8e2cf}.principles dl>div:first-child{padding-top:0}.principles dl>div:last-child{border-bottom:0;padding-bottom:0}.principles dt{font-size:15px;letter-spacing:-.025em;font-weight:550}.principles dt>span{display:block;font-size:7px;letter-spacing:.13em;color:#81916f;font-weight:500;margin-bottom:7px}.principles dd{font-size:11px;line-height:1.9;color:#76856c;margin:7px 0 0}
 .getting-started{padding-block:69px 48px;scroll-margin-top:20px}.start-grid{display:grid;grid-template-columns:1fr 1.12fr;gap:74px}.steps{list-style:none;margin:0;padding:0}.steps li{display:flex;gap:21px;padding:21px 0;border-bottom:1px solid var(--landing-line)}.steps li:first-child{padding-top:10px}.steps li:last-child{border-bottom:0}.step-number{font-family:Georgia,serif;font-style:italic;font-size:27px;font-weight:400;color:#9aab84;line-height:1.3}.steps h3{font-size:16px;line-height:1.7;font-weight:550;margin:0 0 8px;letter-spacing:-.04em}.steps p{font-size:12px;color:var(--landing-muted);margin:0;line-height:1.9}.steps a{display:inline-block;color:#4c7047;font-size:11px;font-weight:550;margin-top:10px}.step-aside{display:block;color:#829078;font-size:10px;margin-top:9px}
 .prompt-example{padding:25px 27px 13px;background:#f3f5ed;border:1px solid #dfe5d8;border-radius:8px;min-width:0}.prompt-heading{display:flex;justify-content:space-between;align-items:center}.prompt-heading .kicker{font-size:8px}.prompt-mark{font-size:19px;color:#9baa89}.prompt-example h3{font-size:18px;font-weight:500;margin:17px 0 10px}.prompt-destination{display:inline-block;font-size:9px;color:#6d7e61;background:#e5ecda;padding:5px 9px;border-radius:3px}.prompt-example pre{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit;line-height:1.95;font-size:12px;color:#586a4e;margin:21px 0 25px;user-select:text}.prompt-actions{display:flex;align-items:center;justify-content:space-between;gap:15px;padding-top:15px;border-top:1px solid #dce4d2}.prompt-actions>span{font-size:9px;color:#829075;line-height:1.8}.copy-button{display:flex;align-items:center;gap:12px;font-size:10px;font-weight:600;white-space:nowrap;background:#fffefa;border:1px solid #d9e1cf;border-radius:4px;padding:10px 13px}.copy-button:hover{background:#e9efdf}.copy-status{font-size:10px;color:#4b6b40;min-height:18px;margin:10px 0 0;line-height:1.8}
 .setup-details{margin-top:27px;border-block:1px solid var(--landing-line)}.setup-details summary{font-size:12px;color:#617258;cursor:pointer;padding:19px 0;list-style-position:inside}.setup-grid{display:grid;grid-template-columns:1fr 1fr;gap:50px;padding:12px 0 25px;min-width:0}.setup-grid>div{min-width:0}.setup-number{font-size:8px;letter-spacing:.1em;color:#7b8c6b}.setup-grid h3{font-size:15px;font-weight:550;margin:11px 0}.setup-grid p{font-size:11px;color:var(--landing-muted);line-height:1.9}.setup-grid pre{font:10px/1.8 ui-monospace,SFMono-Regular,monospace;overflow:auto;padding:14px;background:#edf1e7;border:1px solid #dce3d4;border-radius:4px}
 .browser-section{display:grid;grid-template-columns:1fr 1fr;gap:75px;align-items:center;padding-block:20px 65px}.browser-graphic{border:1px solid #d7e1d0;border-radius:8px;background:#edf3e6;overflow:hidden}.browser-chrome{display:flex;align-items:center;gap:4px;padding:12px 15px;border-bottom:1px solid #d6e0cd;background:#e5eddd}.browser-chrome i{width:5px;height:5px;border-radius:50%;background:#bac9aa}.browser-chrome>span{margin:auto;font-size:7px;letter-spacing:.15em;color:#7b8c6b;padding-right:24px}.browser-flow{display:flex;align-items:center;justify-content:center;gap:21px;padding:40px 18px 30px}.browser-flow>span:first-child,.browser-flow>span:last-child{font-size:11px;letter-spacing:.07em;color:#7a8d69}.browser-flow .flow-line{color:#a0b18a;font-size:20px}.browser-name{font-size:25px;font-weight:500;letter-spacing:-.055em;color:#3e5e3a;line-height:1.1}.browser-name>span{display:block;font-size:12px;letter-spacing:.005em;font-weight:400;margin-top:4px}.browser-bottom{text-align:center;font-size:10px;color:#7b8e6c;padding-bottom:26px;letter-spacing:-.015em}.browser-copy .kicker{font-size:8px}.browser-copy h2{font-size:30px;line-height:1.4;font-weight:500;margin:12px 0 16px}.browser-copy>p{font-size:12px;color:var(--landing-muted);line-height:1.95;margin-bottom:17px}.browser-links{display:flex;flex-wrap:wrap;gap:13px 23px;font-size:11px;color:#4c7046}.browser-links a{border-bottom:1px solid #b7c6a5;padding-bottom:4px}.browser-copy small{display:block;font-size:9px;color:#829276;margin-top:18px;line-height:1.8}
 .connection-section{display:grid;grid-template-columns:.8fr 1.2fr;gap:65px;background:#edf2e6;padding:40px 43px;border:1px solid #dee6d6;border-radius:9px;align-items:center;scroll-margin-top:30px}.connection-section .kicker{font-size:7px}.connection-section h2{font-size:28px;line-height:1.5;font-weight:500;letter-spacing:-.05em;margin:13px 0}.connection-section>div>p{font-size:11px;color:#7a8a6e;margin-bottom:0}.connection-content{min-width:0}.connection-content label{display:block;font-size:11px;color:#617451;margin-bottom:9px}.token-row{display:flex;gap:8px}.token-row input{min-width:0;flex:1;font-size:11px;padding:13px;border-color:#d5dfcb}.token-row input::placeholder{color:#9aa58f}.token-row button{font-size:11px;padding:12px 15px;gap:0}.connection-content small{display:block;font-size:9px;color:#7e8b72;margin-top:9px;line-height:1.9}.connection-error{color:#a34c37;background:#f8ebe4;border:1px solid #eddbcf;border-radius:4px;padding:10px 12px;font-size:11px;line-height:1.8;margin:12px 0 0}.scope-note{font-size:10px;line-height:1.9;color:#7b8970;border-top:1px solid #d8e1cf;margin:17px 0 0;padding-top:13px}.connected-label{display:flex;align-items:center;gap:8px;font-size:12px;color:#617451;margin-bottom:18px}
 .landing-footer{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-block:34px 30px}.footer-wordmark{font-size:15px;font-weight:500;letter-spacing:-.04em;white-space:nowrap}.footer-wordmark>span{color:#90a476}.landing-footer>p{font-size:9px;color:#829176;margin:0}.pricing-note{font-size:8px;line-height:1.8;color:#8a9680;text-align:right}
 .source-link{font-size:10px;color:#647d54;white-space:nowrap}
 @media(min-width:1441px){.hero h1{font-size:48px}}
 @media(max-width:1100px){.hero{gap:30px}.hero h1{font-size:36px}.hero-description{font-size:16px}.hero-detail{font-size:12px}.tool-tabs button{font-size:9px;gap:5px}.principles-inner{gap:60px}.start-grid{gap:38px}.browser-section{gap:40px}.connection-section{gap:35px;padding:32px}.destination+.destination{padding-left:20px}.destination{gap:12px}}
 @media(max-width:850px){.section-width{width:calc(100% - 56px)}.landing-header{padding:22px 28px}.landing-nav{gap:18px}.hero{grid-template-columns:1fr;gap:35px;padding-top:48px;padding-bottom:36px}.hero-copy{max-width:580px}.hero h1{font-size:46px}.hero-description{font-size:17px}.hero-detail{font-size:13px}.workflow-example{width:100%;max-width:530px;justify-self:center}.tool-tabs button{font-size:11px}.example-caption,.example-footer{font-size:9px}.destinations{padding-top:15px}.destination{padding:22px 10px 22px 0;gap:10px}.destination+.destination{padding-left:14px}.destination h3{font-size:13px}.destination p,.format-route{font-size:9px}.destination .tool-icon{width:22px;height:27px;font-size:13px}.principles-inner{gap:36px;padding-block:40px}.principles h2{font-size:26px}.principles p{font-size:11px}.principles dd{font-size:10px}.section-heading h2{font-size:30px}.start-grid{grid-template-columns:1fr;gap:28px}.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}.steps li{display:block;padding:0!important;border:0}.step-number{display:block;margin-bottom:12px}.steps h3{font-size:14px}.steps p{font-size:11px}.prompt-example{padding:25px}.prompt-example pre{font-size:13px}.browser-section{gap:28px}.browser-flow{gap:14px}.browser-copy h2{font-size:25px}.browser-copy>p{font-size:11px}.browser-links{font-size:10px}.connection-section{grid-template-columns:1fr;gap:25px;padding:30px}.connection-section h2 br{display:none}.connection-section h2{margin:12px 0}.landing-footer{flex-wrap:wrap;gap:13px}.landing-footer>p{margin-left:auto}.pricing-note{width:100%;text-align:left}.pricing-note br{display:none}}
 @media(max-width:580px){.section-width{width:calc(100% - 36px)}.landing-header{padding:18px;gap:15px;align-items:center}.wordmark{gap:7px;font-size:10px}.wordmark svg{width:23px;height:27px}.wordmark strong{font-size:19px}.landing-nav{gap:13px;font-size:10px}.nav-library{font-size:10px;padding:9px 10px;gap:8px}.hero{padding-top:36px;gap:28px;padding-bottom:28px}.hero .kicker{font-size:7px;letter-spacing:.08em}.hero h1{font-size:clamp(27px,7.3vw,42px);line-height:1.5;margin:20px 0}.hero-description{font-size:15px;line-height:1.85}.hero-detail{font-size:12px;line-height:1.9;margin-bottom:23px}.desktop-break{display:none}.hero-actions{gap:6px}.action{padding:12px 17px;font-size:12px}.action-text{padding-inline:12px;font-size:11px}.model-picker{padding-top:23px;gap:9px;flex-wrap:wrap}.model-picker>span{font-size:9px}.model-picker select{min-width:85px;font-size:10px}.tool-tabs{padding:7px 5px 0;gap:0}.tool-tabs button{font-size:9px;padding:10px 4px;gap:5px}.tool-tabs .tool-icon{width:14px;height:17px;font-size:9px}.example-caption{font-size:7px;margin-bottom:10px}.example-body{padding:14px 12px}.context-strip{padding:9px 11px}.context-strip strong{font-size:10px}.context-strip div>span{font-size:8px}.example-footer{font-size:7px;gap:4px}.example-disclosure{font-size:8px}.destinations{padding-bottom:32px}.section-heading{display:block;margin-bottom:24px}.section-heading>p{font-size:11px;margin-top:13px}.compact>p br{display:none}.section-heading h2{font-size:28px}.compact h2{font-size:23px}.destination-list{grid-template-columns:1fr}.destination,.destination+.destination{padding:20px 2px;border-left:0;gap:16px;align-items:center}.destination+.destination{border-top:1px solid var(--landing-line)}.destination>div{flex:1;display:grid;grid-template-columns:1fr auto;align-items:center;gap:0 12px;min-width:0}.destination h3{font-size:14px;margin:0 0 5px}.destination p{grid-column:1;font-size:9px;margin:0}.format-route{grid-column:2;grid-row:1/3;font-size:9px;max-width:96px;line-height:1.8;text-align:right}.destination .tool-icon{width:25px;height:30px;font-size:15px}.route-note{font-size:9px;margin-top:12px}.principles-inner{grid-template-columns:1fr;gap:26px;padding-block:34px}.principles h2{font-size:28px;margin-top:15px}.principles p{font-size:12px}.principles dt{font-size:15px}.principles dd{font-size:11px}.principles dl>div{padding-block:18px}.getting-started{padding-top:38px;padding-bottom:32px}.getting-started .section-heading>p br{display:none}.steps{display:block}.steps li,.steps li:first-child{display:flex;gap:17px;padding:18px 0!important;border-bottom:1px solid var(--landing-line)}.steps li:first-child{padding-top:0!important}.steps li:last-child{border:0;padding-bottom:0!important}.step-number{font-size:27px}.steps h3{font-size:15px}.steps p{font-size:12px}.prompt-example{padding:20px 18px 12px}.prompt-example h3{font-size:17px}.prompt-example pre{font-size:12px;margin-block:19px}.prompt-actions{gap:12px}.prompt-actions>span{font-size:8px}.copy-button{padding:9px 11px;font-size:10px;gap:8px}.copy-status{font-size:9px}.setup-grid{grid-template-columns:1fr;gap:20px}.setup-details summary{font-size:11px}.setup-grid pre{font-size:9px}.browser-section{grid-template-columns:1fr;gap:25px;padding-top:4px;padding-bottom:35px}.browser-flow{gap:24px;padding-block:36px 28px}.browser-copy h2{font-size:28px}.browser-copy>p{font-size:12px}.browser-links{font-size:11px;gap:15px}.connection-section{padding:25px 20px;gap:21px}.connection-section h2{font-size:26px}.connection-section h2 br{display:initial}.token-row{flex-direction:column;gap:9px}.token-row input{width:100%;padding:13px;font-size:12px}.token-row button{width:100%;font-size:12px;padding:12px}.connection-content small{font-size:9px}.scope-note{font-size:10px}.landing-footer{padding-block:26px;gap:10px}.footer-wordmark{font-size:14px}.landing-footer>p{font-size:8px;margin-left:0}.pricing-note{font-size:8px;margin-top:3px}}
 @media(min-width:851px) and (max-height:760px){.hero{padding-top:40px;padding-bottom:40px}}
 .use-cases{scroll-margin-top:24px}.use-cases .destination-list{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;border:0}.use-cases .destination{display:flex;align-items:flex-start;gap:14px;padding:25px 23px;background:#fffef9;border:1px solid var(--landing-line);border-radius:6px;min-width:0;height:100%}.use-cases .destination:hover{background:#f4f7ed;border-color:#bdcdb0}.use-cases .destination>div{display:block;min-width:0;flex:1}.use-cases .destination h3{font-size:16px;margin-bottom:6px}.use-cases .case-kind{font-size:10px;margin:0 0 17px;color:#7d8a73}.use-cases .case-request{font-size:13px;line-height:1.85;color:#3b533f;margin:0 0 16px;letter-spacing:-.025em}.use-cases .format-route{display:block;font-size:11px;line-height:1.85;color:#6a7d61;padding-top:13px;border-top:1px solid #e3e9db;max-width:none;text-align:left}.use-cases .format-route strong{display:block;font-size:9px;font-weight:550;color:#7a8d6d;margin-bottom:5px}.tool-icon.medium{background:#eeeede;color:#43513d;font-family:Georgia,serif}.tool-icon.naver{background:#e2ebd8;color:#52733c}.same-memory{padding:27px;background:#eaf0df;border:1px solid #dbe4d1;border-radius:6px}.same-memory .kicker{font-size:8px}.same-memory h3{font-size:24px;line-height:1.5;font-weight:500;letter-spacing:-.05em;margin:15px 0 13px}.same-memory p{font-size:12px;line-height:1.9;color:#617657;margin-bottom:18px}.same-memory small{display:block;font-size:10px;color:#748567;line-height:1.85}.use-cases .route-note{font-size:11px;line-height:1.9;margin-top:18px}
 @media(max-width:850px){.use-cases .destination-list{grid-template-columns:repeat(2,minmax(0,1fr))}.use-cases .destination{padding:24px 19px}.same-memory{padding:25px}}
 @media(max-width:580px){.use-cases .destination-list{grid-template-columns:1fr;gap:12px}.use-cases .destination{padding:23px 19px;gap:14px}.use-cases .destination h3{font-size:16px}.use-cases .case-kind{font-size:10px}.use-cases .case-request{font-size:13px}.use-cases .format-route{font-size:11px}.use-cases .route-note{font-size:10px}.same-memory h3{font-size:25px}}
 @media(prefers-reduced-motion:no-preference){.action,.nav-library,.copy-button{transition:background .15s}}
 .hero-resources{display:flex;flex-wrap:wrap;gap:12px 22px;margin-top:23px;align-items:center;font-size:11px;color:#617958}.hero-resources button{border:0;background:transparent;padding:0;font:inherit;color:#3b663c}.hero-resources>span{font-size:9px;color:#7d8e71}.how-section{padding-block:30px 55px;scroll-margin-top:24px}.how-steps{list-style:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));padding:0;margin:0;gap:28px}.how-steps li{padding:27px 24px;background:#fffef9;border:1px solid var(--landing-line);border-radius:6px;min-width:0}.how-number{font-size:9px;letter-spacing:.11em;color:#78916a}.how-steps h3{font-size:21px;letter-spacing:-.04em;font-weight:500;margin:18px 0 12px}.how-steps p{font-size:12px;line-height:1.9;color:var(--landing-muted);margin-bottom:20px}.how-example{display:block;border-top:1px solid #e1e8da;padding-top:15px;font-size:10px;line-height:1.8;color:#78906a}.browser-setup{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center;padding:28px 30px;background:#edf2e6;border:1px solid #dce5d3;border-radius:6px;margin-top:23px}.browser-setup h3{font-size:23px;font-weight:500;letter-spacing:-.04em;margin:11px 0}.browser-setup p{font-size:12px;line-height:1.9;color:var(--landing-muted);margin:0}.browser-downloads{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:10px}.browser-downloads .action{font-size:11px;padding:12px 15px}.chrome-download{background:#fffef9;border:1px solid #cedbc2;color:#37583e}.browser-setup-guide{width:100%;text-align:right;font-size:10px;color:#5a7849;margin-top:4px}
 @media(max-width:1100px){.landing-header{flex-wrap:wrap;gap:19px}.landing-nav{gap:18px}.how-steps{gap:16px}.how-steps li{padding:23px 18px}.browser-setup{gap:25px}}
 @media(max-width:850px){.landing-header{align-items:center}.landing-nav{flex-wrap:wrap;font-size:11px;gap:13px 19px}.hero{padding-top:40px}.how-section{padding-top:20px}.how-steps h3{font-size:18px}.how-steps p{font-size:11px}.browser-setup{grid-template-columns:1fr;gap:20px}.browser-downloads{justify-content:flex-start}.browser-setup-guide{width:auto;text-align:left;align-self:center;padding-inline:5px}}
 @media(max-width:580px){.landing-header{gap:20px}.landing-nav{width:100%;display:grid;grid-template-columns:1fr 1.3fr 1fr;gap:15px 10px;font-size:11px}.landing-nav .text-button{grid-column:1/3;justify-self:start;padding:0;font-size:11px}.landing-nav .nav-library{justify-content:center;padding:9px 10px;font-size:11px}.hero-resources{gap:14px 18px;font-size:11px}.hero-resources>span{width:100%}.how-section{padding-block:20px 34px}.how-steps{grid-template-columns:1fr;gap:12px}.how-steps li{padding:23px}.how-steps h3{font-size:22px;margin-top:13px}.how-steps p{font-size:13px;margin-bottom:18px}.how-example{font-size:11px}.browser-setup{padding:23px 20px}.browser-setup h3{font-size:23px}.browser-downloads{display:grid;grid-template-columns:1fr;width:100%}.browser-downloads .action{font-size:12px;padding:13px}.browser-setup-guide{text-align:center;margin-top:9px}}

 .hero-output{height:370px;overflow:hidden;margin:16px 0 13px;background:#edf1e7;border:1px solid #e0e6d8;border-radius:5px}
 .hero-output.worklog{background:#f0f0e7}
 .hero-output-title{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 16px}
 .hero-output-title strong{font-size:17px;font-weight:550;letter-spacing:-.025em}.hero-output-title>span{font-size:10px;color:var(--landing-muted)}
 .example-footer a{font-size:11px;font-weight:550;color:#446a42;text-decoration:underline;text-underline-offset:4px;white-space:nowrap}
 .about-section{padding-block:54px 66px;scroll-margin-top:24px;border-bottom:1px solid var(--landing-line)}
 .about-heading{margin-bottom:22px}.about-heading .kicker{font-size:9px}.about-heading h2{font-size:clamp(30px,3vw,42px)}
 .about-story{max-width:850px;font-size:14px;line-height:1.95;color:var(--landing-muted);margin:0 0 25px}
 .about-values{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
 .about-values article{min-width:0;padding:22px 23px;background:#fffef9;border:1px solid var(--landing-line);border-radius:6px}
 .about-index{font-size:8px;letter-spacing:.12em;color:#81916f}
 .about-values h3{font-size:17px;line-height:1.5;font-weight:550;letter-spacing:-.03em;margin:12px 0 8px}
 .about-values p{font-size:11px;line-height:1.9;color:var(--landing-muted);margin:0}
 .memory-savings{padding-block:42px 50px;scroll-margin-top:24px}
 .savings-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:0}
 .savings-metrics>div{min-width:0;padding:26px 28px;background:#edf2e6;border:1px solid #dce5d3;border-radius:6px}
 .savings-metrics dt{font-size:12px;color:#617657;line-height:1.7}
 .savings-metrics dd{margin:8px 0 0;font-size:clamp(36px,5vw,60px);line-height:1.15;font-weight:550;letter-spacing:-.05em;color:#365e3c}
 .savings-example{font-size:13px;line-height:1.85;color:#3b583e;margin:20px 0 10px}
 .savings-note{font-size:11px;line-height:1.9;color:var(--landing-muted);max-width:930px;margin:0}
 .savings-note a{color:#45653b;text-decoration:underline;text-underline-offset:3px}
 .savings-note a:focus-visible{outline:3px solid #527844;outline-offset:4px}
 @media(max-width:580px){.memory-savings{padding-block:28px 36px}.savings-metrics{grid-template-columns:1fr}.savings-metrics>div{padding:22px}.savings-example{font-size:12px}}
 .document-examples{padding-block:32px 76px;scroll-margin-top:28px}
 .document-examples .section-heading{margin-bottom:32px}.document-examples .section-heading h2{font-size:clamp(30px,3vw,43px);line-height:1.3}
 .document-examples .section-heading>p{font-size:15px;line-height:1.8}
 .example-gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;align-items:stretch}
 .document-example{display:flex;flex-direction:column;min-width:0;overflow:hidden;background:#fffef9;border:1px solid #dce3d8;border-radius:10px;text-decoration:none}
 .document-example.report{grid-row:span 2}
 .example-art{overflow:hidden;background:#edf1e7;flex:none}.document-example.report .example-art{flex:1;min-height:640px}.document-example.deck .example-art{aspect-ratio:4/3}.document-example.worklog .example-art{height:235px;background:#f0f0e7}
 .example-card-copy{padding:24px 28px 27px}.document-example.report .example-card-copy{margin-top:auto}
 .example-kind{display:flex;justify-content:space-between;gap:12px;font-size:11px;font-weight:550;letter-spacing:.08em;text-transform:uppercase;color:#75876a}
 .example-kind>span{font-size:19px;line-height:.9;letter-spacing:0;color:#6d875b}
 .example-card-copy h3{font-size:27px;line-height:1.3;letter-spacing:-.04em;font-weight:550;margin:14px 0 11px}
 .example-card-copy p{font-size:14px;line-height:1.8;color:var(--landing-muted);margin:0 0 17px;max-width:390px}
 .example-destination{font-size:11px;color:#7d8b72}.example-open{display:block;margin-top:20px;font-size:12px;font-weight:550;color:#365e3c}
 .document-example:hover{border-color:#a6bb93}.document-example:hover .example-open{text-decoration:underline;text-underline-offset:4px}
 .document-example:focus-visible,.example-footer a:focus-visible{outline:3px solid #527844;outline-offset:4px}
 .examples-note{font-size:11px;line-height:1.8;color:#7b8970;margin:18px 0 0}
 @media(min-width:851px) and (max-height:760px){.hero-output{height:260px;margin-block:12px}.hero-output-title{margin-bottom:10px}}
 @media(max-width:850px){.example-gallery{grid-template-columns:1fr}.document-example.report{grid-row:auto}.document-example.report .example-art{height:640px;min-height:0;flex:none}.document-example.deck .example-art{max-height:500px}.document-example.worklog .example-art{height:340px}.document-examples{padding-block:30px 50px}.document-examples .section-heading>p{font-size:14px}.hero-output{height:390px}}
 @media(max-width:720px){.about-values{grid-template-columns:1fr}}
 @media(max-width:580px){.landing-nav .examples-nav{display:none}.about-section{padding-block:38px 45px}.about-heading h2{font-size:29px}.about-story{font-size:12px}.about-values article{padding:19px}.about-values h3{font-size:16px}.about-values p{font-size:11px}.hero-output{height:330px;margin-block:13px}.hero-output-title{display:block;margin-bottom:13px}.hero-output-title strong{display:block;font-size:17px;margin-bottom:5px}.hero-output-title>span{font-size:10px}.example-footer{align-items:flex-start;gap:12px}.example-footer a{font-size:10px}.document-examples{padding-block:24px 40px}.document-examples .section-heading h2{font-size:32px}.document-examples .section-heading>p{font-size:14px}.example-gallery{gap:20px}.document-example.report .example-art{height:auto}.document-example.deck .example-art{max-height:none}.document-example.worklog .example-art{height:300px}.example-card-copy{padding:22px}.example-card-copy h3{font-size:25px}.example-card-copy p{font-size:14px}.example-open{margin-top:18px}}

 @media print{.landing{display:none}}

 .tool-icon.docs,.tool-icon.slides,.tool-icon.notion,.tool-icon.medium,.tool-icon.naver{background:transparent;border:0;padding:0}
 .tool-icon.medium{background:#222;border-radius:4px;padding:3px}
 .tool-icon :global(.service-logo){width:100%;height:100%}
 .ai-brands{display:inline-flex;align-items:center;gap:12px;flex-wrap:wrap}.ai-brands>span{display:inline-flex;align-items:center;gap:5px;font-size:10px;color:#75876a}.ai-brands :global(.service-logo){width:17px;height:17px}
 .browser-name :global(.service-logo){width:27px;height:27px;vertical-align:middle;margin-right:5px}
 @media(max-width:580px){.ai-brands{gap:9px}.ai-brands>span{font-size:9px}.ai-brands :global(.service-logo){width:15px;height:15px}.browser-flow{gap:14px}}
 .landing-nav{display:flex;align-items:center;justify-content:flex-end;gap:24px}
 .landing-links{display:flex;align-items:center;gap:22px;font-size:12px}
 .landing-links>a:not(.nav-library){color:#5d7062}
 .nav-actions{display:flex;align-items:center;gap:13px}
 .language-toggle{border:1px solid #dbe4d2;border-radius:5px;background:#fffef9;color:#37583e;padding:8px 11px;font:inherit;font-size:11px;font-weight:600;white-space:nowrap;cursor:pointer}
 .language-toggle:hover{background:#edf2e7}
 .language-toggle:focus-visible{outline:2px solid #5c7c4d;outline-offset:4px}
 @media(max-width:1100px){.landing-nav{gap:17px}.landing-links{gap:17px}}
 @media(max-width:850px){.landing-nav{width:100%;justify-content:space-between;gap:14px}.landing-links{flex-wrap:wrap;gap:13px 19px;font-size:11px}.nav-actions{gap:10px}}
 @media(max-width:580px){.landing-header{flex-wrap:wrap;align-items:center}.landing-nav{display:block;width:100%;font-size:11px}.landing-links{display:grid;grid-template-columns:1fr 1.3fr 1fr;gap:14px 10px;font-size:11px}.landing-links>a{min-width:0}.nav-actions{justify-content:space-between;width:100%;margin-top:14px;gap:8px}.language-toggle{font-size:10px;padding:8px}.landing-nav .nav-library{padding:9px 10px;font-size:10px;gap:8px}.landing-nav .text-button{font-size:11px;padding:0}}
</style>
