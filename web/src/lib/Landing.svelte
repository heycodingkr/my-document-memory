<script lang="ts">
 import {onDestroy,onMount} from 'svelte';
 import AgentSetup from './AgentSetup.svelte';
 import DocumentPreview from './DocumentPreview.svelte';
 import DemoVideo from './DemoVideo.svelte';
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
 let menuOpen=$state(false);
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
 function closeMenu(){menuOpen=false;}
 function menuKey(event:KeyboardEvent){
  if(event.key==='Escape'&&menuOpen){menuOpen=false;document.getElementById('landing-menu-toggle')?.focus();}
 }
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

<svelte:window onkeydown={menuKey}/>

<div class="landing" data-locale={locale}>
 <a class="skip-link" href="#intro">{page.skip}</a>
 <header class="landing-header">
  <a class="wordmark" href="#intro" aria-label={page.brandHome}>
   <svg width="29" height="33" viewBox="0 0 34 38" fill="none" aria-hidden="true"><path d="M7 2h15l8 8v25H7zM22 2v9h8M12 17h13M12 23h10M12 29h7M2 8v29h22" stroke="currentColor" stroke-width="1.7"/></svg>
   <span>my document <strong>memory<span>.</span></strong></span>
  </a>
  <div class="header-controls">
   <button class="language-toggle" aria-label={landingCopy[locale].languageButtonAria} onclick={toggleLanguage}>{landingCopy[locale].languageButton}</button>
   <button id="landing-menu-toggle" class="menu-toggle" aria-expanded={menuOpen} aria-controls="landing-navigation" onclick={()=>menuOpen=!menuOpen}>{locale==='ko'?'메뉴':'Menu'} <span aria-hidden="true">{menuOpen?'−':'+'}</span></button>
  </div>
  <nav id="landing-navigation" class="landing-nav" class:menu-open={menuOpen} aria-label={page.navLabel}>
   <div class="landing-links">
    <a href="#about" onclick={closeMenu}>{page.nav.about}</a>
    <a href="#how-it-works" onclick={closeMenu}>{page.nav.how}</a>
    <a class="examples-nav" href="#document-examples" onclick={closeMenu}>{page.nav.examples}</a>
    <a href="#connect-agent" onclick={closeMenu}>{page.nav.connect}</a>
    <a href="https://github.com/heycodingkr/my-document-memory" target="_blank" rel="noreferrer noopener" onclick={closeMenu}>{page.nav.github}</a>
   </div>
   <div class="nav-actions">
    <button class="text-button" onclick={()=>{closeMenu();onleaderboard();}}>{locale==='ko'?'리더보드':'Leaderboard'}</button>
    <button class="text-button" onclick={()=>{closeMenu();onpublic();}}>{page.nav.public}</button>
    {#if connected}<button class="nav-library" onclick={()=>{closeMenu();onreturn();}}>{page.nav.space}</button>{:else}<button class="nav-library" onclick={()=>{closeMenu();onlogin();}}>{page.nav.signIn} <span aria-hidden="true">↗</span></button><button class="nav-library nav-primary" onclick={()=>{closeMenu();onsignup();}}>{locale==='ko'?'가입하기':'Create account'}</button>{/if}
   </div>
  </nav>
 </header>

 <main id="intro" tabindex="-1">
  <section class="hero section-width" aria-labelledby="hero-title">
   <div class="hero-copy">
    <span class="kicker"><i aria-hidden="true"></i> {page.hero.kicker}</span>
    <h1 id="hero-title">{page.hero.title} <br/><span>{page.hero.subtitle}</span></h1>
    <p class="hero-description">{page.hero.description}<br class="desktop-break"/> {page.hero.descriptionNext}</p>
    <p class="hero-detail">{page.hero.detail}<br class="desktop-break"/> {page.hero.detailNext}</p>
    <div class="hero-actions"><a class="action action-primary" href="#get-started">{page.hero.getStarted} →</a><a class="action action-text" href="#product-demo">{page.hero.watchDemo} <span aria-hidden="true">↓</span></a></div>
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

  <div class="section-width"><DemoVideo {locale}/></div>

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
 .landing{--landing-muted:#526458;--landing-line:#dce3d8;background:#fafbf7;color:#263e32;font-size:16px;line-height:1.7;overflow-wrap:break-word}
 .section-width{width:min(1160px,calc(100% - 80px));margin-inline:auto}
 main:focus{outline:none}
 .kicker{display:block;font-size:12px;font-weight:650;letter-spacing:.09em;line-height:1.7;color:#526748}
 .skip-link{position:absolute;left:20px;top:-80px;background:#244e3c;color:#fff;padding:12px 18px;border-radius:6px;z-index:10}
 .skip-link:focus{top:12px}
 .landing-header{max-width:1440px;margin:auto;padding:20px 32px;display:flex;align-items:center;justify-content:space-between;gap:28px;border-bottom:1px solid var(--landing-line)}
 .wordmark{display:flex;align-items:center;gap:10px;line-height:1.1;letter-spacing:-.035em;font-size:13px;flex:none;min-height:44px}
 .wordmark strong{display:block;font-size:24px;font-weight:600}
 .wordmark strong span,.footer-wordmark>span{color:#78925f}
 .landing-nav{display:flex;align-items:center;justify-content:flex-end;gap:16px;min-width:0;order:1}
 .header-controls{display:flex;align-items:center;gap:8px;order:2}
 .header-controls>button{display:inline-flex;justify-content:center;align-items:center;min-width:44px;min-height:44px;padding:10px 12px;border-radius:7px;font-size:12px;line-height:1.4;white-space:nowrap}
 .header-controls>.menu-toggle{display:none;border:1px solid #ced9c5;background:#edf2e6;gap:12px;font-weight:600}
 .menu-toggle>span{font-size:18px;line-height:1}
 .landing-links{display:flex;align-items:center;gap:14px;font-size:13px}
 .landing-links>a{display:flex;align-items:center;min-height:44px;color:#455e4e;line-height:1.4}
 .landing-links>a:hover{text-decoration:underline;text-underline-offset:5px}
 .nav-actions{display:flex;align-items:center;gap:8px}
 .nav-actions>button{display:inline-flex;justify-content:center;align-items:center;min-height:44px;border-radius:7px;padding:10px 11px;font-size:12px;font-weight:550;line-height:1.4;white-space:nowrap}
 .nav-actions>.text-button{color:#455e4e}
 .language-toggle{border:1px solid #ced9c5;background:#fffef9;color:#37583e;font:inherit;cursor:pointer}
 .nav-library{gap:10px;border:1px solid #ced9c5;background:#fffef9}
 .nav-actions>.nav-primary{background:#284f3c;border-color:#284f3c;color:white}
 .nav-actions>button:hover{background:#eaf0e2}
 .nav-actions>.nav-primary:hover{background:#386347}
 .hero{display:grid;grid-template-columns:1.12fr 1fr;gap:54px;align-items:center;padding-block:64px 58px}
 .hero .kicker{display:flex;align-items:center;gap:9px;font-size:12px;letter-spacing:.07em}
 .hero-copy{min-width:0}
 .hero-copy .kicker i,.example-caption i{width:6px;height:6px;display:inline-block;background:#78925f;border-radius:50%;flex:none}
 .hero h1{font-size:clamp(36px,3.3vw,48px);font-weight:600;line-height:1.2;letter-spacing:-.045em;margin:22px 0}
 .hero h1>span{color:#557347}
 .hero-description{font-size:18px;line-height:1.75;letter-spacing:-.015em;margin-bottom:14px;max-width:46ch}
 .hero-detail{font-size:15px;color:var(--landing-muted);line-height:1.8;margin-bottom:24px;max-width:55ch}
 .hero-actions{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
 .action{display:inline-flex;align-items:center;justify-content:center;gap:14px;font-size:14px;font-weight:600;padding:13px 20px;min-height:48px;border-radius:7px;line-height:1.5}
 .action-primary{background:#284f3c;color:#fff;border:1px solid #284f3c}
 .action-primary:hover:enabled,.action-primary[href]:hover{background:#386347}
 .action-text{padding-inline:12px;color:#3e603c}
 .action-text:hover{background:#edf2e6}
 .action-text span{font-size:18px}
 .hero-resources{display:flex;flex-wrap:wrap;gap:0 22px;margin-top:14px;align-items:center;font-size:13px;color:#3e603c}
 .hero-resources button,.hero-resources>a{display:inline-flex;align-items:center;min-height:44px;padding:0;font:inherit;color:inherit}
 .hero-resources>span{font-size:12px;color:var(--landing-muted)}
 .model-picker{display:flex;align-items:center;gap:12px;padding-top:14px;font-size:12px;color:var(--landing-muted);flex-wrap:wrap}
 .model-picker select{font-size:16px;background:#f4f6ef;border-color:#ced9c5;padding:9px 24px 9px 10px;border-radius:6px;color:#3b563c;min-width:100px;min-height:44px}
 .ai-brands{display:inline-flex;align-items:center;gap:12px;flex-wrap:wrap}
 .ai-brands>span{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--landing-muted)}
 .ai-brands :global(.service-logo){width:18px;height:18px}
 .workflow-example{min-width:0;position:relative;padding-top:7px}
 .example-caption{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 12px;font-size:12px;line-height:1.7;color:var(--landing-muted);margin:0 2px 12px}
 .example-caption>span:first-child{display:flex;align-items:center;gap:7px}
 .tool-tabs{display:flex;background:#edf2e6;border:1px solid #d2dccb;border-bottom:0;border-radius:12px 12px 0 0;padding:8px 8px 0;gap:3px}
 .tool-tabs button{display:flex;align-items:center;justify-content:center;gap:7px;flex:1;min-width:0;min-height:48px;padding:10px 6px;border-radius:7px 7px 0 0;color:#526448;font-size:13px;line-height:1.4;border:1px solid transparent;border-bottom:0}
 .tool-tabs button.chosen{background:#fffef9;color:#263e32;border-color:#d2dccb;box-shadow:0 2px 0 #fffef9}
 .tool-icon{width:26px;height:30px;display:inline-grid;place-items:center;flex:none}
 .tool-tabs .tool-icon{width:18px;height:20px}
 .tool-icon.medium{background:#222;border-radius:4px;padding:3px}
 .tool-icon :global(.service-logo){width:100%;height:100%}
 .example-body{background:#fffef9;padding:19px;border:1px solid #d2dccb;border-top:0;border-radius:0 0 12px 12px;box-shadow:0 16px 40px #263e3209;min-width:0}
 .context-strip{display:flex;align-items:center;gap:10px;padding:12px 13px;background:#f0f4e9;border:1px solid #e2e8d9;border-radius:7px}
 .context-symbol{font-size:25px;color:#607c47}
 .context-strip strong{display:block;font-size:13px;font-weight:600;margin-bottom:3px;line-height:1.5}
 .context-strip div>span{font-size:12px;color:var(--landing-muted)}
 .context-check{margin-left:auto;background:#e0e8d1;width:24px;height:24px;display:grid;place-items:center;border-radius:50%;font-size:13px;color:#45623c;flex:none}
 .hero-output{height:370px;overflow:hidden;margin:16px 0 13px;background:#edf1e7;border:1px solid #e0e6d8;border-radius:7px}
 .hero-output.worklog{background:#f0f0e7}
 .hero-output-title{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:4px 12px;margin:0 0 12px}
 .hero-output-title strong{font-size:18px;font-weight:600;letter-spacing:-.025em}
 .hero-output-title>span{font-size:12px;color:var(--landing-muted)}
 .example-footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px 12px;font-size:12px;color:var(--landing-muted)}
 .example-footer>span:first-child{display:flex;align-items:center;gap:6px}
 .tiny-dot{display:inline-block;width:5px;height:5px;background:#65834d;border-radius:50%;flex:none}
 .example-footer a{display:inline-flex;align-items:center;min-height:44px;font-size:13px;font-weight:550;color:#365e3c;text-decoration:underline;text-underline-offset:4px}
 .example-disclosure{font-size:12px;color:var(--landing-muted);text-align:center;margin:12px 0 0;line-height:1.7}
 .section-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:32px;margin-bottom:30px}
 .section-heading>div{min-width:0;flex:1}
 .section-heading h2{font-size:34px;line-height:1.3;font-weight:600;margin:12px 0 0;letter-spacing:-.035em;text-wrap:balance}
 .section-heading>p{font-size:15px;color:var(--landing-muted);line-height:1.8;margin:0;max-width:38ch;flex:1}
 .about-section{padding-block:52px 60px;scroll-margin-top:24px;border-bottom:1px solid var(--landing-line)}
 .about-heading{margin-bottom:22px}
 .about-heading h2{font-size:clamp(30px,3vw,40px)}
 .about-story{max-width:80ch;font-size:16px;line-height:1.85;color:var(--landing-muted);margin:0 0 28px}
 .about-values{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
 .about-values article{min-width:0;padding:26px;background:#fffef9;border:1px solid var(--landing-line);border-radius:10px}
 .about-index{font-size:12px;letter-spacing:.07em;color:#526748}
 .about-values h3{font-size:20px;line-height:1.4;font-weight:550;letter-spacing:-.025em;margin:14px 0 12px}
 .about-values p{font-size:14px;line-height:1.85;color:var(--landing-muted);margin:0}
 .memory-savings{padding-block:48px;scroll-margin-top:24px}
 .savings-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:0}
 .savings-metrics>div{min-width:0;padding:28px;background:#edf2e6;border:1px solid #dce5d3;border-radius:10px}
 .savings-metrics dt{font-size:15px;color:#48603e;line-height:1.7}
 .savings-metrics dd{margin:8px 0 0;font-size:clamp(42px,5vw,60px);line-height:1.15;font-weight:550;letter-spacing:-.04em;color:#365e3c}
 .savings-example{font-size:15px;line-height:1.85;color:#3b583e;margin:22px 0 12px}
 .savings-note,.examples-note{font-size:13px;line-height:1.8;color:var(--landing-muted);margin:0;max-width:90ch}
 .savings-note a{color:#365e3c;text-decoration:underline;text-underline-offset:3px}
 .document-examples{padding-block:32px 64px;scroll-margin-top:28px}
 .document-examples .section-heading h2{font-size:clamp(30px,3vw,40px)}
 .example-gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;align-items:stretch}
 .document-example{display:flex;flex-direction:column;min-width:0;overflow:hidden;background:#fffef9;border:1px solid var(--landing-line);border-radius:12px}
 .document-example.report{grid-row:span 2}
 .example-art{overflow:hidden;background:#edf1e7;flex:none}
 .document-example.report .example-art{flex:1;min-height:640px}
 .document-example.deck .example-art{aspect-ratio:4/3}
 .document-example.worklog .example-art{height:235px;background:#f0f0e7}
 .example-card-copy{padding:26px 28px}
 .document-example.report .example-card-copy{margin-top:auto}
 .example-kind{display:flex;justify-content:space-between;gap:12px;font-size:12px;font-weight:550;letter-spacing:.05em;text-transform:uppercase;color:#526748}
 .example-kind>span{font-size:22px;line-height:1;letter-spacing:0}
 .example-card-copy h3{font-size:26px;line-height:1.3;letter-spacing:-.03em;font-weight:550;margin:14px 0 12px}
 .example-card-copy p{font-size:15px;line-height:1.8;color:var(--landing-muted);margin:0 0 18px;max-width:45ch}
 .example-destination{font-size:12px;color:var(--landing-muted)}
 .example-open{display:block;margin-top:20px;font-size:14px;font-weight:550;color:#365e3c}
 .document-example:hover{border-color:#90a87d;box-shadow:0 8px 24px #263e3208}
 .document-example:hover .example-open{text-decoration:underline;text-underline-offset:4px}
 .examples-note{margin-top:20px}
 .how-section{padding-block:30px 56px;scroll-margin-top:24px}
 .how-steps{list-style:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));padding:0;margin:0;gap:20px}
 .how-steps li{padding:26px;background:#fffef9;border:1px solid var(--landing-line);border-radius:10px;min-width:0}
 .how-number{font-size:12px;letter-spacing:.06em;color:#526748}
 .how-steps h3{font-size:22px;line-height:1.4;letter-spacing:-.03em;font-weight:550;margin:18px 0 12px}
 .how-steps p{font-size:14px;line-height:1.85;color:var(--landing-muted);margin-bottom:22px}
 .how-example{display:block;border-top:1px solid var(--landing-line);padding-top:16px;font-size:13px;line-height:1.8;color:#48603e}
 .browser-setup{display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:center;padding:30px;background:#edf2e6;border:1px solid #dce5d3;border-radius:10px;margin-top:24px}
 .browser-setup h3{font-size:24px;line-height:1.4;font-weight:550;letter-spacing:-.03em;margin:12px 0}
 .browser-setup p{font-size:14px;line-height:1.85;color:var(--landing-muted);margin:0}
 .browser-downloads{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:12px}
 .browser-downloads .action{font-size:14px;padding:12px 16px}
 .chrome-download{background:#fffef9;border:1px solid #b8c8aa;color:#37583e}
 .browser-setup-guide{display:flex;align-items:center;justify-content:flex-end;min-height:44px;width:100%;font-size:13px;color:#365e3c}
 .destinations{padding:24px 0 56px}
 .use-cases{scroll-margin-top:24px}
 .use-cases .destination-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
 .destination{display:flex;align-items:flex-start;gap:16px;padding:26px;background:#fffef9;border:1px solid var(--landing-line);border-radius:10px;min-width:0;height:100%}
 .destination:hover{background:#f1f5eb;border-color:#a6bb93}
 .destination>div{min-width:0;flex:1}
 .destination h3{font-size:18px;line-height:1.4;font-weight:550;margin:0 0 8px}
 .destination h3>span{font-size:15px;margin-left:6px}
 .case-kind{font-size:12px;margin:0 0 18px;color:var(--landing-muted)}
 .case-request{font-size:15px;line-height:1.8;color:#3b533f;margin:0 0 18px}
 .format-route{display:block;font-size:14px;line-height:1.85;color:var(--landing-muted);padding-top:16px;border-top:1px solid var(--landing-line)}
 .format-route strong{display:block;font-size:12px;font-weight:550;color:#48603e;margin-bottom:7px}
 .same-memory{padding:28px;background:#eaf0df;border:1px solid #dbe4d1;border-radius:10px}
 .same-memory h3{font-size:26px;line-height:1.4;font-weight:550;letter-spacing:-.035em;margin:16px 0}
 .same-memory p{font-size:15px;line-height:1.8;color:#48603e;margin-bottom:18px}
 .same-memory small{display:block;font-size:13px;color:#526448;line-height:1.8}
 .route-note{font-size:13px;line-height:1.8;margin:20px 0 0;color:var(--landing-muted)}
 .principles{background:#edf2e6;border-block:1px solid #e3e9db;scroll-margin-top:24px}
 .principles-inner{display:grid;grid-template-columns:1fr 1fr;gap:80px;padding-block:56px}
 .principles h2{font-size:34px;font-weight:550;line-height:1.35;letter-spacing:-.035em;margin:16px 0 20px}
 .principles p{font-size:15px;line-height:1.85;color:var(--landing-muted);margin:0}
 .principles dl{margin:0}
 .principles dl>div{padding:22px 0;border-bottom:1px solid #d3ddcb}
 .principles dl>div:first-child{padding-top:0}
 .principles dl>div:last-child{border-bottom:0;padding-bottom:0}
 .principles dt{font-size:18px;line-height:1.5;font-weight:550}
 .principles dt>span{display:block;font-size:12px;letter-spacing:.07em;color:#526748;font-weight:500;margin-bottom:8px}
 .principles dd{font-size:14px;line-height:1.85;color:var(--landing-muted);margin:10px 0 0}
 .getting-started{padding-block:60px 48px;scroll-margin-top:24px}
 .start-grid{display:grid;grid-template-columns:1fr 1.12fr;gap:54px}
 .steps{list-style:none;margin:0;padding:0}
 .steps li{display:flex;gap:20px;padding:24px 0;border-bottom:1px solid var(--landing-line)}
 .steps li:first-child{padding-top:10px}
 .steps li:last-child{border-bottom:0}
 .step-number{font-family:Georgia,serif;font-style:italic;font-size:30px;font-weight:400;color:#637e51;line-height:1.3}
 .steps h3{font-size:18px;line-height:1.5;font-weight:550;margin:0 0 10px;letter-spacing:-.025em}
 .steps p{font-size:14px;color:var(--landing-muted);margin:0;line-height:1.85}
 .steps a{display:inline-flex;align-items:center;min-height:44px;color:#365e3c;font-size:14px;font-weight:550;margin-top:4px}
 .step-aside{display:block;color:var(--landing-muted);font-size:13px;line-height:1.8;margin-top:12px}
 .prompt-example{padding:26px;background:#f3f5ed;border:1px solid #dfe5d8;border-radius:10px;min-width:0}
 .prompt-heading{display:flex;justify-content:space-between;align-items:center}
 .prompt-mark{font-size:22px;color:#607c47}
 .prompt-example h3{font-size:21px;font-weight:550;line-height:1.4;margin:18px 0 12px}
 .prompt-destination{display:inline-block;font-size:12px;color:#48603e;background:#e5ecda;padding:6px 10px;border-radius:5px}
 .prompt-example pre{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit;line-height:1.85;font-size:15px;color:#455a3e;margin:24px 0;user-select:text}
 .prompt-actions{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding-top:16px;border-top:1px solid #dce4d2}
 .prompt-actions>span{font-size:12px;color:var(--landing-muted);line-height:1.8}
 .copy-button{display:flex;align-items:center;gap:12px;font-size:13px;font-weight:600;white-space:nowrap;background:#fffefa;border:1px solid #c4d2b7;border-radius:6px;padding:10px 14px;min-height:44px}
 .copy-button:hover{background:#e9efdf}
 .copy-status{font-size:13px;color:#365e3c;min-height:22px;margin:12px 0 0;line-height:1.8}
 .setup-details{margin-top:28px;border-block:1px solid var(--landing-line)}
 .setup-details summary{font-size:14px;color:#3e603c;cursor:pointer;padding:20px 0;list-style-position:inside}
 .setup-grid{display:grid;grid-template-columns:1fr 1fr;gap:40px;padding:14px 0 28px;min-width:0}
 .setup-grid>div{min-width:0}
 .setup-number{font-size:12px;letter-spacing:.07em;color:#526748}
 .setup-grid h3{font-size:18px;font-weight:550;margin:12px 0}
 .setup-grid p{font-size:14px;color:var(--landing-muted);line-height:1.85}
 .setup-grid pre{font:13px/1.8 ui-monospace,SFMono-Regular,monospace;overflow:auto;padding:16px;background:#edf1e7;border:1px solid #dce3d4;border-radius:6px}
 .browser-section{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center;padding-block:20px 60px}
 .browser-graphic{border:1px solid #d7e1d0;border-radius:10px;background:#edf3e6;overflow:hidden}
 .browser-chrome{display:flex;align-items:center;gap:5px;padding:14px 16px;border-bottom:1px solid #d6e0cd;background:#e5eddd}
 .browser-chrome i{width:6px;height:6px;border-radius:50%;background:#a1b58a}
 .browser-chrome>span{margin:auto;font-size:12px;letter-spacing:.07em;color:#48603e;padding-right:24px}
 .browser-flow{display:flex;align-items:center;justify-content:center;gap:20px;padding:40px 18px 30px}
 .browser-flow>span:first-child,.browser-flow>span:last-child{font-size:14px;color:#48603e}
 .browser-flow .flow-line{color:#637e51;font-size:22px}
 .browser-name{font-size:27px;font-weight:550;letter-spacing:-.035em;color:#3e5e3a;line-height:1.1}
 .browser-name>span{display:block;font-size:14px;letter-spacing:0;font-weight:400;margin-top:6px}
 .browser-name :global(.service-logo){width:27px;height:27px;vertical-align:middle;margin-right:5px}
 .browser-bottom{text-align:center;font-size:13px;line-height:1.8;color:#48603e;padding:0 18px 28px}
 .browser-copy h2{font-size:32px;line-height:1.3;font-weight:550;margin:14px 0 18px}
 .browser-copy>p{font-size:15px;color:var(--landing-muted);line-height:1.85;margin-bottom:18px}
 .browser-links{display:flex;flex-wrap:wrap;gap:8px 24px;font-size:14px;color:#365e3c}
 .browser-links a{display:inline-flex;align-items:center;min-height:44px;text-decoration:underline;text-underline-offset:5px}
 .browser-copy small{display:block;font-size:13px;color:var(--landing-muted);margin-top:16px;line-height:1.8}
 .connection-section{display:grid;grid-template-columns:.8fr 1.2fr;gap:48px;background:#edf2e6;padding:40px;border:1px solid #dee6d6;border-radius:12px;align-items:center;scroll-margin-top:24px}
 .connection-section h2{font-size:30px;line-height:1.35;font-weight:550;letter-spacing:-.035em;margin:16px 0}
 .connection-section>div>p{font-size:14px;color:var(--landing-muted);line-height:1.85;margin-bottom:0}
 .connection-content{min-width:0}
 .connection-content label{display:block;font-size:14px;color:#48603e;margin-bottom:10px}
 .token-row{display:flex;gap:10px}
 .token-row input{min-width:0;flex:1;font-size:16px;min-height:48px;padding:12px;border-color:#bdcdb0}
 .token-row input::placeholder{color:#65755b}
 .token-row button{font-size:14px;padding:12px 16px;gap:0}
 .connection-content small{display:block;font-size:13px;color:var(--landing-muted);margin-top:12px;line-height:1.8}
 .connection-error{color:#8e3827;background:#f8ebe4;border:1px solid #eddbcf;border-radius:6px;padding:12px;font-size:14px;line-height:1.8;margin:14px 0 0}
 .scope-note{font-size:14px;line-height:1.85;color:var(--landing-muted);border-top:1px solid #d8e1cf;margin:20px 0 0;padding-top:16px}
 .connected-label{display:flex;align-items:center;gap:8px;font-size:14px;color:#48603e;margin-bottom:20px}
 .landing-footer{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px 24px;padding-block:36px}
 .footer-wordmark{font-size:18px;font-weight:550;letter-spacing:-.035em;white-space:nowrap}
 .landing-footer>p{font-size:13px;color:var(--landing-muted);margin:0}
 .source-link{display:inline-flex;align-items:center;min-height:44px;font-size:13px;color:#365e3c}
 .pricing-note{font-size:12px;line-height:1.8;color:var(--landing-muted);text-align:right}
 /* Keep narrative text readable in the embedded setup and template sections. */
 .landing :global(.agent-setup .setup-heading>p),.landing :global(.agent-setup .method-description p),.landing :global(.free-template-section article p),.landing :global(.free-template-section .section-heading>p){font-size:15px;line-height:1.85;color:var(--landing-muted)}
 .landing :global(.agent-setup .protocol-note),.landing :global(.agent-setup .method-note),.landing :global(.free-template-scope),.landing :global(.free-template-section .memory-evidence){font-size:13px;line-height:1.8;color:var(--landing-muted)}
 .landing :global(.agent-setup .connection-methods button),.landing :global(.agent-setup .code-heading button){min-height:44px}
 .landing :global(.agent-setup .method-code pre){font-size:13px;line-height:1.8}
 .landing :global(.agent-setup .kicker),.landing :global(.free-template-section .kicker){font-size:12px;color:#526748}
 .landing :global(.free-template-section .browse-templates){background:#284f3c;border-color:#284f3c;min-height:48px;border-radius:7px}
 @media(max-width:1240px){
  .landing-header{flex-wrap:wrap;gap:12px}
  .landing-nav{flex-basis:100%;justify-content:space-between;order:3}
  .header-controls{margin-left:auto}
 }
 @media(max-width:960px){
  .landing-nav{flex-direction:column;align-items:stretch;gap:8px}
  .landing-links{justify-content:space-between}
  .nav-actions{justify-content:flex-end}
  .section-heading{gap:24px}
 }
 @media(max-width:850px){
  .section-width{width:calc(100% - 56px)}
  .landing-header{padding:18px 28px}
  .hero{grid-template-columns:1fr;gap:32px;padding-block:40px}
  .hero-copy{max-width:640px}
  .hero h1{font-size:46px}
  .workflow-example{width:100%;max-width:560px;justify-self:center}
  .hero-output{height:390px}
  .about-values{grid-template-columns:1fr}
  .about-values article{padding:26px}
  .example-gallery{grid-template-columns:1fr}
  .document-example.report{grid-row:auto}
  .document-example.report .example-art{height:640px;min-height:0;flex:none}
  .document-example.deck .example-art{max-height:500px}
  .document-example.worklog .example-art{height:340px}
  .how-steps{grid-template-columns:1fr}
  .browser-setup{grid-template-columns:1fr;gap:22px}
  .browser-downloads{justify-content:flex-start}
  .browser-setup-guide{width:auto;justify-content:flex-start}
  .use-cases .destination-list{grid-template-columns:repeat(2,minmax(0,1fr))}
  .destination{padding:24px 20px}
  .principles-inner{gap:32px;padding-block:44px}
  .principles h2{font-size:28px}
  .start-grid{grid-template-columns:1fr;gap:28px}
  .browser-section{gap:28px}
  .browser-flow{gap:12px}
  .browser-copy h2{font-size:28px}
  .connection-section{grid-template-columns:1fr;gap:28px;padding:32px}
  .pricing-note{width:100%;text-align:left}
 }
 @media(max-width:600px){
  .section-width{width:calc(100% - 40px)}
  .landing-header{padding:16px 20px;gap:12px 8px}
  .header-controls>.menu-toggle{display:inline-flex}
  .landing-nav{display:none;gap:12px;padding-top:8px;border-top:1px solid var(--landing-line)}
  .landing-nav.menu-open{display:flex}
  .wordmark{font-size:12px}
  .wordmark strong{font-size:22px}
  .wordmark svg{width:25px;height:29px}
  .landing-links{display:grid;grid-template-columns:1fr 1fr 1.2fr;gap:0 10px;font-size:12px}
  .landing-links>a{padding-block:8px}
  .nav-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  .nav-actions>button{font-size:12px;padding:10px;white-space:normal}
  .hero{padding-block:28px 36px;gap:28px}
  .hero .kicker{font-size:11px;letter-spacing:.055em}
  .hero h1{font-size:clamp(30px,8.2vw,40px);line-height:1.2;margin:18px 0}
  .hero-description{font-size:17px;line-height:1.75}
  .hero-detail{font-size:14px;line-height:1.8;margin-bottom:22px}
  .desktop-break{display:none}
  .hero-actions{gap:6px}
  .action{font-size:14px;padding:12px 16px}
  .action-text{padding-inline:10px;font-size:13px}
  .hero-resources{gap:0 20px;font-size:13px}
  .hero-resources>span{width:100%}
  .model-picker{gap:10px;padding-top:18px}
  .ai-brands{gap:10px}
  .example-caption{font-size:12px}
  .tool-tabs{padding:7px 5px 0;gap:0}
  .tool-tabs button{font-size:12px;padding:10px 4px;gap:5px}
  .tool-tabs .tool-icon{width:16px;height:18px}
  .example-body{padding:14px 12px}
  .context-strip{padding:10px;gap:8px}
  .context-strip strong{font-size:12px}
  .hero-output{height:330px;margin-block:14px}
  .hero-output-title{display:block;margin-bottom:8px}
  .hero-output-title strong{display:block;font-size:18px;margin-bottom:4px}
  .example-footer{align-items:flex-start;gap:0}
  .example-footer>span:first-child{width:100%}
  .section-heading{display:block;margin-bottom:26px}
  .section-heading>p{font-size:14px;margin-top:16px;max-width:48ch}
  .section-heading h2,.about-heading h2,.document-examples .section-heading h2{font-size:30px}
  .about-section{padding-block:36px 44px}
  .about-story{font-size:15px}
  .about-values{gap:14px}
  .about-values article{padding:24px}
  .memory-savings{padding-block:36px}
  .savings-metrics{grid-template-columns:1fr;gap:14px}
  .savings-metrics>div{padding:24px}
  .document-examples{padding-block:24px 44px}
  .example-gallery{gap:20px}
  .document-example.report .example-art{height:auto}
  .document-example.deck .example-art{max-height:none}
  .document-example.worklog .example-art{height:300px}
  .example-card-copy{padding:24px}
  .example-card-copy h3{font-size:24px}
  .how-section{padding-block:24px 40px}
  .how-steps{gap:14px}
  .how-steps li{padding:24px}
  .how-steps h3{font-size:22px;margin-top:14px}
  .browser-setup{padding:24px}
  .browser-downloads{display:grid;grid-template-columns:1fr;width:100%}
  .browser-setup-guide{justify-content:center}
  .destinations{padding-bottom:40px}
  .use-cases .destination-list{grid-template-columns:1fr;gap:14px}
  .destination{padding:24px;gap:16px}
  .principles-inner{grid-template-columns:1fr;gap:32px;padding-block:40px}
  .principles h2{font-size:30px}
  .getting-started{padding-block:40px 36px}
  .start-grid{gap:24px}
  .steps li{gap:16px;padding:22px 0}
  .steps li:first-child{padding-top:0}
  .prompt-example{padding:24px 20px}
  .setup-grid{grid-template-columns:1fr;gap:24px}
  .browser-section{grid-template-columns:1fr;gap:28px;padding-block:12px 40px}
  .browser-flow{gap:14px}
  .browser-copy h2{font-size:30px}
  .connection-section{padding:26px 22px;gap:24px}
  .connection-section h2{font-size:28px}
  .token-row{flex-direction:column}
  .token-row input,.token-row button{width:100%}
  .landing-footer{padding-block:28px;gap:10px 20px}
  .footer-wordmark{font-size:17px}
 }
 @media(min-width:851px) and (max-height:760px){
  .hero{padding-block:28px}
  .hero h1{font-size:40px;margin-block:18px}
  .hero-description{font-size:17px}
  .hero-detail{margin-bottom:18px}
  .hero-output{height:260px;margin-block:12px}
 }
 @media(prefers-reduced-motion:no-preference){.action,.nav-actions>button,.document-example{transition:background .15s,border-color .15s,box-shadow .15s}}
 @media print{.landing{display:none}}
</style>
