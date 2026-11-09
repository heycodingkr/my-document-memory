<script lang="ts">
 import {onMount} from 'svelte';
 import {Api,ApiFailure} from './lib/api';
 import type {Template,Source,Document,Block,Family,Session,Contribution,Dashboard} from './lib/types';
 import AuthPanel from './lib/AuthPanel.svelte';
 import AccountNavigation from './lib/AccountNavigation.svelte';
 import ContributePanel from './lib/ContributePanel.svelte';
 import MyPage from './lib/MyPage.svelte';
 import PublicLibrary from './lib/PublicLibrary.svelte';
 import Modal from './lib/Modal.svelte';
 import DocumentView from './lib/DocumentView.svelte';
 import AgentPrompt from './lib/AgentPrompt.svelte';
 import Landing from './lib/Landing.svelte';

 type View='templates'|'sources'|'documents'|'me'|'contributions'|'public';
 let session=$state<Session|null>(null);let summary=$state<Dashboard|null>(null);let contributions=$state<Contribution[]>([]);
 let contributionTemplate=$state<Template|null>(null);let publicAuthor=$state('');let publicLicense=$state('CC-BY-4.0');let rightsConfirmed=$state(false);let initialized=$state(false);
 let loginToken=$state('');let authEpoch=0;
 let token=$state('');let connected=$state(false);let working=$state(false);let loading=$state(false);let showGuide=$state(false);
 let view=$state<View>('templates');let query=$state('');let kind=$state('all');let scope=$state('all');let templateLocale=$state('en-US');
 let templates=$state<Template[]>([]);let sources=$state<Source[]>([]);let documents=$state<Document[]>([]);
 let error=$state('');let errorCode=$state('');let notice=$state('');
 let selectedTemplate=$state<Template|null>(null);let selectedSource=$state<Source|null>(null);
 let selectedSourceIds=$state<string[]>([]);let newTitle=$state('');let outlineApproved=$state(false);
 let doc=$state<Document|null>(null);let baseline=$state('');let editorSources=$state<Source[]>([]);let activeSlide=$state(0);
 let revisions=$state<Document[]|null>(null);let revisionPreview=$state<Document|null>(null);
 let customOpen=$state(false);let customTitle=$state('');let customType=$state('report');let customSections=$state('');
 let exportFormat=$state('md');let fileInput=$state<HTMLInputElement>();
 let api:Api|null=null;let refreshId=0;
 const dirty=$derived(doc!==null&&JSON.stringify({title:doc.title,content:doc.content})!==baseline);
 const featured=$derived(templates.find(t=>t.id==='meeting.minutes.en')??templates[0]);
 const labels:Record<Family,string>={document:'Document',deck:'Slides',sheet:'Spreadsheet'};
 const types=[['report','Log / Report'],['meeting_minutes','Meeting notes'],['proposal','Proposal'],['quote','Quote'],['resume','Resume'],['pitch_deck','Pitch deck'],['report_deck','Presentation report']];
 function fail(e:unknown){if(e instanceof ApiFailure&&e.code==='auth_required'&&connected&&!token){clearPrivate();view='me';}error=e instanceof Error?e.message:'The request could not be completed.';errorCode=e instanceof ApiFailure?e.code:'';}
 async function perform<T>(fn:()=>Promise<T>):Promise<T|undefined>{
  if(working)return;working=true;error='';errorCode='';
  try{return await fn();}catch(e){fail(e);}finally{working=false;}
 }
 async function refresh(){
  if(!api||view==='public')return;const n=++refreshId;loading=true;
  try{
   const [t,s,d]=await Promise.all([api.templates(view==='templates'?query:'',kind,view==='me'?'private':scope,view==='templates'?templateLocale:'all'),api.sources(view==='sources'?query:''),api.documents(view==='documents'?query:'')]);
   if(n===refreshId){templates=t.items;sources=s.items;documents=d.items;}
   if(view==='me'||view==='contributions'){const [stats,cs]=await Promise.all([api.dashboard(),api.contributions()]);if(n===refreshId){summary=stats;contributions=cs.items;}}
  }catch(e){if(n===refreshId)fail(e);}finally{if(n===refreshId)loading=false;}
 }
 async function connect(){
  await perform(async()=>{const candidate=new Api(token);await candidate.status();api=candidate;connected=true;sessionStorage.setItem('dmem.token',token);await refresh();});
 }
 function clearPrivate(){++refreshId;sessionStorage.removeItem('dmem.token');token='';api=null;connected=false;session=null;doc=null;templates=[];sources=[];documents=[];editorSources=[];selectedTemplate=null;selectedSource=null;contributionTemplate=null;customOpen=false;revisions=null;revisionPreview=null;summary=null;contributions=[];}
 async function disconnect(){
  if(working||loading)return;
  if(dirty&&!window.confirm('You have unsaved changes. Sign out?'))return;
  if(session&&api){try{await api.logout();}catch(e){fail(e);return;}}
  clearPrivate();view='me';history.replaceState(null,'','#me');notice='';error='';
 }
 async function signedIn(value:Session){loginToken='';session=value;token='';sessionStorage.removeItem('dmem.token');api=new Api('',value.csrf_token);connected=true;setView('me');}
 function openEmailLink(){
  const requested=location.hash.slice(1);if(!requested.startsWith('sign-in='))return false;
  const candidate=requested.slice(8);history.replaceState(null,'','#me');
  if(dirty&&!window.confirm('You have unsaved changes. Continue to sign in?')){history.replaceState(null,'','#'+view);return true;}
  ++authEpoch;clearPrivate();loginToken=/^[0-9a-f]{64}\.[0-9a-f]{64}$/i.test(candidate)?candidate:'invalid';view='me';showGuide=false;initialized=true;error='';notice='';return true;
 }
 onMount(()=>{void (async()=>{
  if(openEmailLink())return;const requested=location.hash.slice(1);const epoch=authEpoch;
  try{const value=await new Api().session();if(epoch!==authEpoch)return;session=value;api=new Api('',value.csrf_token);connected=true;view=['me','contributions','public','templates','sources','documents'].includes(requested)?requested as View:'me';await refresh();}
  catch(e){if(epoch!==authEpoch)return;token=sessionStorage.getItem('dmem.token')??'';view=requested==='public'?'public':requested==='me'?'me':'templates';if(token)await connect();else if(e instanceof ApiFailure&&e.code!=='auth_required')fail(e);}
  finally{if(epoch===authEpoch)initialized=true;}
 })();});
 function beforeUnload(e:BeforeUnloadEvent){if(dirty){e.preventDefault();e.returnValue='';}}
 function setView(next:View){
  if(doc&&!leaveEditor())return;showGuide=false;view=next;history.replaceState(null,'','#'+next);query='';kind='all';scope='all';error='';notice='';void refresh();
 }
 function leaveEditor(){
  if(dirty&&!window.confirm('You have unsaved changes. Return to the library?'))return false;
  doc=null;editorSources=[];return true;
 }
 function preview(t:Template){selectedTemplate=t;selectedSourceIds=[];newTitle=t.title;outlineApproved=false;error='';}
 async function copyTemplate(){
  const t=selectedTemplate;if(!t||!api)return;
  const copy=await perform(()=>api!.copy(t.id));if(copy){selectedTemplate=copy;notice='Template copied to your private library.';await refresh();}
 }
 async function createDocument(){
  if(!selectedTemplate||!api)return;
  const created=await perform(()=>api!.create(newTitle.trim(),selectedTemplate!.id,selectedSourceIds,outlineApproved));
  if(created){selectedTemplate=null;await enterDocument(created);notice='Your draft is ready with the selected references.';await refresh();}
 }
 async function enterDocument(d:Document){
  view='documents';history.replaceState(null,'','#documents');doc=structuredClone(d);baseline=JSON.stringify({title:d.title,content:d.content});activeSlide=0;exportFormat=d.family==='deck'?'pptx':'docx';editorSources=[];
  if(api)try{editorSources=await Promise.all(d.source_versions.map(r=>api!.source(r.source_id)));}catch(e){fail(e);}
 }
 async function openDocument(id:string){
  const d=await perform(()=>api!.document(id));if(d)await enterDocument(d);
 }
 async function save(){
  if(!doc||!api)return;
  const saved=await perform(()=>api!.save(doc!.id,doc!.version,doc!.title,doc!.content));
  if(saved){doc=saved;baseline=JSON.stringify({title:saved.title,content:saved.content});notice='Saved · v'+saved.version;await refresh();}
 }
 async function reloadDocument(){
  if(!doc||!api)return;
  if(dirty&&!window.confirm('Discard your edits and load the latest saved version?'))return;
  const latest=await perform(()=>api!.document(doc!.id));if(latest)await enterDocument(latest);
 }
 async function upload(event:Event){
  const input=event.currentTarget as HTMLInputElement;const file=input.files?.[0];if(!file||!api)return;
  if(file.size>10*1024*1024){fail(new ApiFailure('payload_too_large'));input.value='';return;}
  const source=await perform(()=>api!.upload(file));input.value='';
  if(source){notice='Reference saved. The original file is preserved.';query='';selectedSource=source;await refresh();}
 }
 async function sourceAsTemplate(){
  if(!selectedSource||!api)return;const t=await perform(()=>api!.fromSource(selectedSource!.id));
  if(t){selectedSource=null;preview(t);notice='Extracted structure saved as a private template.';await refresh();}
 }
 async function showSource(id:string){
  const source=editorSources.find(s=>s.id===id)??sources.find(s=>s.id===id);
  if(source){selectedSource=source;return;}if(!api)return;const loaded=await perform(()=>api!.source(id));if(loaded)selectedSource=loaded;
 }
 async function createCustom(){
  if(!api)return;const deck=['pitch_deck','report_deck'].includes(customType);
  const t=await perform(()=>api!.createTemplate({title:customTitle,summary:'My custom document structure',form:{provider:deck?'pptx':'docx',doc_type:customType,locale:'en-US'},sections:customSections.split('\n').map(s=>s.trim()).filter(Boolean),tags:[]}));
  if(t){customOpen=false;preview(t);await refresh();}
 }
 function moveBlock(i:number,delta:number){
  if(!doc)return;const blocks=doc.content.blocks;const next=i+delta;if(next<0||next>=blocks.length)return;
  const [item]=blocks.splice(i,1);blocks.splice(next,0,item);
 }
 function addBlock(type:'paragraph'|'heading'|'list'|'table'){
  if(!doc)return;const b:Block=type==='paragraph'?{type,text:''}:type==='heading'?{type,text:'New section',level:2}:type==='list'?{type,items:['']}:{type,rows:[['Item','Details'],['','']]};
  doc.content.blocks.push(b);
 }
 function moveSlide(delta:number){
  if(!doc)return;const slides=doc.content.slides;const n=activeSlide+delta;if(n<0||n>=slides.length)return;
  const [slide]=slides.splice(activeSlide,1);slides.splice(n,0,slide);activeSlide=n;
 }
 function removeSlide(){if(!doc||doc.content.slides.length===1)return;doc.content.slides.splice(activeSlide,1);activeSlide=Math.min(activeSlide,doc.content.slides.length-1);}
 async function showRevisions(){if(!doc||!api)return;const r=await perform(()=>api!.revisions(doc!.id));if(r){revisions=r.items;revisionPreview=null;}}
 function applyRevision(r:Document){if(!doc)return;doc.title=r.title;doc.content=structuredClone($state.snapshot(r.content));activeSlide=0;revisions=null;notice='Earlier version applied to your draft. Save to create a new version.';}
 async function download(){
  if(!doc||!api||dirty)return;
  if(exportFormat==='pdf'){window.print();return;}
  await perform(()=>api!.download('/documents/'+doc!.id+'/export/'+exportFormat,'document.'+exportFormat));
 }
 function prepareContribution(t:Template){selectedTemplate=null;contributionTemplate=t;publicLicense='CC-BY-4.0';rightsConfirmed=false;error='';}
 async function submitContribution(){if(!api||!contributionTemplate)return;const result=await perform(()=>api!.contribute(contributionTemplate!.id,publicAuthor,publicLicense,rightsConfirmed));if(result){contributionTemplate=null;setView('contributions');notice='Template submitted. It will become public after review.';}}
 async function withdrawContribution(id:string){if(!api||!window.confirm('Withdraw this contribution? New searches and copies will stop.'))return;const result=await perform(()=>api!.withdraw(id));if(result){notice='Contribution withdrawn. Existing copies keep their attribution.';await refresh();}}
 function date(ts:number){return new Date(ts*1000).toLocaleDateString('en-US',{month:'long',day:'numeric'});}
</script>

<svelte:window onbeforeunload={beforeUnload} onhashchange={openEmailLink}/>
{#if (!connected&&view!=='me'&&view!=='public')||showGuide}
 <Landing bind:token {connected} {working} {error} onconnect={connect} onreturn={()=>{showGuide=false;setView('me');}} onlogin={()=>setView('me')} onpublic={()=>setView('public')}/>
{:else}
<div class:editing={doc!==null} class="app-shell">
 <aside class="sidebar">
  <a class="brand" href="/" onclick={(e)=>{e.preventDefault();if(connected)setView('templates');}}>
   <svg width="34" height="38" viewBox="0 0 34 38" fill="none" aria-hidden="true"><path d="M7 2h15l8 8v25H7z" stroke="currentColor" stroke-width="1.8"/><path d="M22 2v9h8M12 17h13M12 23h10M12 29h7" stroke="currentColor" stroke-width="1.8"/><path d="M2 8v29h22" stroke="currentColor" stroke-width="1.8"/></svg>
   <span>my document<br/><strong>memory<span class="brand-dot">.</span></strong></span>
  </a>
  <div class="workspace-label"><span class="workspace-dot"></span> My workspace</div>
  <AccountNavigation active={doc?'':view} {connected} busy={working||loading} onview={setView} onlogout={disconnect}/>
  <nav aria-label="Library">
   <button class:active={view==='templates'&&!doc} disabled={!connected} onclick={()=>setView('templates')}><span aria-hidden="true">▤</span> Template library</button>
   <button class:active={view==='sources'&&!doc} disabled={!connected} onclick={()=>setView('sources')}><span aria-hidden="true">⌁</span> My references</button>
   <button class:active={view==='documents'||doc!==null} disabled={!connected} onclick={()=>setView('documents')}><span aria-hidden="true">▱</span> My documents</button>
  </nav>
  <div class="sidebar-note"><span class="eyebrow">A BETTER START</span><p>Reuse the structure.<br/>Make it your own.</p><span class="muted">Your templates and references<br/>start your next document.</span></div>
  <div class="sidebar-bottom"><span class="connection"><span class:online={connected}></span>{connected?'Library connected':'Ready to connect'}</span><button class="text-button" onclick={()=>{showGuide=true;window.scrollTo(0,0);}}>Getting started</button>{#if connected}<button class="text-button" disabled={working} onclick={disconnect}>{session?'Sign out':'Disconnect'}</button>{/if}<small>MY DOCUMENT MEMORY · LOCAL</small></div>
 </aside>

 <div class="main-shell">
  <header class="topbar"><span>{doc?'EDITOR':view==='me'?'MY SPACE / OVERVIEW':view==='contributions'?'MY SPACE / CONTRIBUTIONS':view==='public'?'COMMUNITY / PUBLIC':view==='templates'?'LIBRARY / TEMPLATES':view==='sources'?'LIBRARY / REFERENCES':'WORKSPACE / DOCUMENTS'}</span><div class="private-label"><span aria-hidden="true">◈</span> Private library <span class="avatar">ME</span></div></header>
  <input class="visually-hidden" type="file" accept=".txt,.md,.markdown,.docx,.pptx" bind:this={fileInput} onchange={upload} aria-label="Upload reference file"/>
  {#if error&&!selectedTemplate&&!selectedSource&&!customOpen&&!revisions&&!contributionTemplate}<div class="alert" role="alert"><span>{error}</span>{#if errorCode==='version_conflict'&&doc}<button onclick={reloadDocument} disabled={working}>Load latest saved version</button>{/if}<button class="icon-button" aria-label="Dismiss error" onclick={()=>{error='';errorCode='';}}>✕</button></div>{/if}
  {#if notice}<div class="notice" role="status">{notice}<button class="icon-button" aria-label="Dismiss notice" onclick={()=>notice=''}>✕</button></div>{/if}

  {#if !initialized}<main class="library-page"><p role="status">Opening your space…</p></main>
  {:else if !connected&&view!=='public'}<main class="library-page"><span class="eyebrow">WELCOME BACK</span><h1>Your next document starts here.</h1><AuthPanel linkToken={loginToken} onlogin={signedIn}/><button class="text-button" onclick={()=>setView('public')}>Browse public memories →</button></main>
  {:else if view==='public'}<PublicLibrary {connected} onpreview={preview} onlogin={()=>setView('me')}/>
  {:else if view==='me'||view==='contributions'}<MyPage email={session?.account.email??'Local workspace'} {summary} {contributions} {templates} {documents} loading={loading||working} onview={setView} onpreview={preview} onopen={openDocument} onwithdraw={withdrawContribution} contributionsOnly={view==='contributions'}/>
  {:else if doc}
   <main class="editor-shell">
    <div class="editor-toolbar"><button class="text-button back" onclick={leaveEditor}>← Library</button><span class="version-label">v{doc.version} · {dirty?'Unsaved changes':'All changes saved'}</span><div class="toolbar-actions"><button class="secondary" onclick={showRevisions} disabled={working}>Version history</button><button class="primary" onclick={save} disabled={working||!dirty}>{working?'Working…':'Save'}</button><select aria-label="Export format" bind:value={exportFormat}><option value="md">Markdown</option><option value="html">HTML</option>{#if doc.family==='document'}<option value="docx">DOCX</option>{:else}<option value="pptx">PPTX</option>{/if}<option value="pdf">PDF · Print</option></select><button class="secondary" onclick={download} disabled={working||dirty} title={dirty?'Save your changes before exporting':'Export the saved version'}>Export ↗</button></div></div>
    <div class="editor-grid">
     <aside class="outline-panel"><span class="eyebrow">{doc.family==='deck'?'SLIDES':'OUTLINE'}</span>
      {#if doc.family==='deck'}
       {#each doc.content.slides as slide,i}<button class:chosen={activeSlide===i} class="slide-thumb" onclick={()=>activeSlide=i}><small>{String(i+1).padStart(2,'0')}</small><strong>{slide.title}</strong><span>{slide.body.slice(0,50)}</span></button>{/each}
       <button class="secondary full" onclick={()=>{doc!.content.slides.push({title:'New slide',body:'',citations:[]});activeSlide=doc!.content.slides.length-1;}}>+ Add slide</button>
      {:else}
       {#each doc.content.blocks as b,i}{#if b.type==='heading'}<button class="outline-link" onclick={()=>window.document.getElementById('block-'+i)?.scrollIntoView({behavior:'smooth',block:'center'})}>{b.text||'Untitled'}</button>{/if}{/each}
      {/if}
     </aside>
     <div class="canvas-area">
      <label class="visually-hidden" for="document-title">Document title</label><input id="document-title" class="document-title" bind:value={doc.title} maxlength="120" placeholder="Document title"/>
      {#if doc.family==='deck'}
       {@const slide=doc.content.slides[activeSlide]}
       <div class="slide-controls"><span>{activeSlide+1} / {doc.content.slides.length}</span><div><button class="icon-button" aria-label="Move slide earlier" disabled={activeSlide===0} onclick={()=>moveSlide(-1)}>↑</button><button class="icon-button" aria-label="Move slide later" disabled={activeSlide===doc.content.slides.length-1} onclick={()=>moveSlide(1)}>↓</button><button class="text-button" disabled={doc.content.slides.length===1} onclick={removeSlide}>Delete</button></div></div>
       <section class="slide-canvas"><span class="slide-kicker">MY DOCUMENT MEMORY / {String(activeSlide+1).padStart(2,'0')}</span><textarea class="slide-title" aria-label="Slide title" bind:value={slide.title} maxlength="120" rows="2"></textarea><textarea class="slide-body" aria-label="Slide body" bind:value={slide.body} maxlength="10000" rows="8"></textarea><div class="slide-footer"><span>{doc.title}</span><span>{activeSlide+1}</span></div></section>
       <p class="canvas-hint">Keep one message per slide. Review long text after export.</p>
      {:else}
       <div class="document-canvas">
        {#each doc.content.blocks as block,i}
         <section class="editor-block" id={'block-'+i}>
          <div class="block-tools"><span>{block.type==='heading'?'Heading':block.type==='paragraph'?'Paragraph':block.type==='quote'?'Source excerpt':block.type==='list'?'List':'Table'}</span><button class="icon-button" aria-label={'Block '+(i+1)+' up'} disabled={i===0} onclick={()=>moveBlock(i,-1)}>↑</button><button class="icon-button" aria-label={'Block '+(i+1)+' down'} disabled={i===doc!.content.blocks.length-1} onclick={()=>moveBlock(i,1)}>↓</button><button class="icon-button" aria-label={'Block '+(i+1)+' delete'} disabled={doc!.content.blocks.length===1} onclick={()=>doc!.content.blocks.splice(i,1)}>×</button></div>
          {#if block.type==='heading'}<input class="block-heading" aria-label={'Section heading '+(i+1)} bind:value={block.text} placeholder="Section heading"/>
          {:else if block.type==='paragraph'}<textarea class="block-paragraph" aria-label={'Paragraph '+(i+1)} bind:value={block.text} rows="3" placeholder="Write your content"></textarea>
          {:else if block.type==='quote'}<blockquote><textarea aria-label={'Source excerpt '+(i+1)} readonly={Boolean(block.citation)} bind:value={block.text} rows="4"></textarea>{#if block.citation}<button class="text-button" onclick={()=>showSource(block.citation!.source_id)}>View source · {block.citation.span_id} ↗</button>{/if}</blockquote>
          {:else if block.type==='list'}<textarea class="block-paragraph" aria-label={'List '+(i+1)} value={block.items.join('\n')} oninput={(e)=>block.items=e.currentTarget.value.split('\n')} rows="4" placeholder="One item per line"></textarea>
          {:else if block.type==='table'}<textarea class="table-editor" aria-label={'Table '+(i+1)} value={block.rows.map(r=>r.join('\t')).join('\n')} oninput={(e)=>block.rows=e.currentTarget.value.split('\n').map(r=>r.split('\t'))} rows="5"></textarea><small class="muted">Separate columns with tabs and rows with new lines.</small>{/if}
         </section>
        {/each}
        <div class="add-block"><span>Add a block</span><button onclick={()=>addBlock('paragraph')}>+ Paragraph</button><button onclick={()=>addBlock('heading')}>+ Heading</button><button onclick={()=>addBlock('list')}>+ List</button><button onclick={()=>addBlock('table')}>+ Table</button></div>
       </div>
      {/if}
     </div>
     <aside class="evidence-panel"><span class="eyebrow">DOCUMENT CONTEXT</span><h3>Template and evidence</h3><div class="context-box"><small>Template used</small><strong>{templates.find(t=>t.id===doc!.template.template_id)?.title??doc.template.template_id}</strong><span>v{doc.template.version} · {doc.template.author}</span><span>{doc.template.license}</span></div>
      <h4>Selected references <span>{doc.source_versions.length}</span></h4>
      {#each doc.source_versions as source}<button class="evidence-link" onclick={()=>showSource(source.source_id)}><span>▱</span><strong>{source.title}</strong><small>v{source.version} · View original ↗</small></button>{:else}<p class="muted">No references selected. Review and confirm facts before writing.</p>{/each}
      <div class="context-note"><span aria-hidden="true">◎</span><p><strong>Review items that need confirmation.</strong>Missing facts remain open for review. Check the selected excerpts in the source panel.</p></div>
     </aside>
    </div>
   </main>
   <div class="print-only"><DocumentView title={doc.title} content={doc.content}/></div>
  {:else}
   <main class="library-page">
    <div class="page-heading"><div><span class="eyebrow">{view==='templates'?'MAKE IT YOUR OWN':view==='sources'?'YOUR SOURCES OF TRUTH':'WORK IN PROGRESS'}</span><h1>{view==='templates'?'Template library':view==='sources'?'My references':'My documents'}<span class="heading-dot">.</span></h1><p>{view==='templates'?'Find a useful structure for your next document.':view==='sources'?'Keep the facts and references for your work together.':'Reopen, refine, and keep your work moving.'}</p></div><button class="primary" disabled={working} onclick={()=>{if(view==='sources')fileInput?.click();else if(view==='documents')setView('templates');else{customOpen=true;customTitle='';customSections='';}}}>{view==='sources'?'+ Import reference':view==='documents'?'+ New document':'+ New template'}</button></div>
    {#if view==='templates'&&!query&&kind==='all'&&scope==='all'&&featured}
     <section class="featured"><div><span class="eyebrow">A SMALL STRUCTURE. A CLEARER DAY.</span><h2>Keep the notes clear.<br/>Make the next step count.</h2><p>{featured.summary}</p><button class="featured-link" disabled={loading} onclick={()=>preview(featured)}>{featured.title} Explore <span>↗</span></button></div><div class="featured-preview" aria-hidden="true"><span class="paper-label">TEMPLATE / {featured.form.locale}</span><h3>{featured.title}</h3>{#each featured.sections.slice(0,4) as section,i}<div><small>0{i+1}</small><span>{section}</span><i></i></div>{/each}<span class="paper-mark">mdm.</span></div><span class="featured-sticker">{labels[featured.form.family]} template<br/><strong>Make it yours.</strong></span></section>
    {/if}
    <div class="search-row"><form class="search-form" onsubmit={(e)=>{e.preventDefault();void refresh();}}><span aria-hidden="true">⌕</span><input aria-label="Library search" bind:value={query} maxlength="200" placeholder={view==='templates'?'What would you like to create?':view==='sources'?'Search reference titles or content':'Search documents by title'}/><button class="text-button" disabled={loading}>Search</button></form>{#if view==='templates'}<select aria-label="Template language" bind:value={templateLocale} onchange={()=>void refresh()}><option value="en-US">English</option><option value="all">All languages</option><option value="ko-KR">Korean</option></select><select aria-label="Visibility" bind:value={scope} onchange={()=>void refresh()}><option value="all">All templates</option><option value="private">My templates</option><option value="public">Public template</option></select>{/if}</div>
    {#if view==='templates'}<div class="filter-row" role="group" aria-label="Template type">{#each [['all','All'],['document','Document'],['deck','Slides'],['sheet','Spreadsheet']] as [value,label]}<button class:chosen={kind===value} onclick={()=>{kind=value;void refresh();}}>{label}</button>{/each}<span>{templates.length} templates{templates.length===20?' · showing up to 20':''}</span></div>{/if}
    {#if loading}<div class="loading" role="status">Loading your library…</div>{/if}
    {#if view==='templates'}
     <div class="template-grid" aria-busy={loading}>{#each templates as t (t.id)}<article class="template-card"><button class="card-preview" disabled={loading} class:deck-cover={t.form.family==='deck'} class:sheet-cover={t.form.family==='sheet'} aria-label={t.title+' preview'} onclick={()=>preview(t)}><div class="mini-page"><small>{t.form.locale} / {t.form.family==='deck'?'PRESENTATION':t.form.family==='sheet'?'SPREADSHEET':'DOCUMENT'}</small><strong>{t.title}</strong>{#each t.sections.slice(0,4) as s}<span>{s}</span>{/each}</div><span class="cover-arrow">↗</span></button><div class="card-body"><div class="card-meta"><span>{labels[t.form.family]}</span><span>{t.visibility==='private'?'My templates':'Public template'}</span></div><button class="card-title" disabled={loading} onclick={()=>preview(t)}><h3>{t.title}</h3></button><p>{t.summary}</p><div class="card-footer"><span>{t.tags[0]??t.form.doc_type}</span><span>{t.form.family==='sheet'?'Preview only':'v'+t.version+' · '+t.form.locale}</span></div></div></article>{:else}<div class="empty-state"><span>⌕</span><h3>No matching templates.</h3><p>Try another search or filter.</p><button class="secondary" onclick={()=>{query='';kind='all';scope='all';void refresh();}}>Show all templates</button></div>{/each}</div>
    {:else if view==='sources'}
     <div class="section-caption"><span>Saved references · {sources.length} items</span><small>TXT / Markdown / basic DOCX / PPTX · 10 MiB per file</small></div>
     <div class="source-list">{#each sources as source(source.id)}<button class="source-row" onclick={()=>selectedSource=source}><span class="file-badge">{source.format.toUpperCase()}</span><div><h3>{source.title}</h3><p>{source.spans[0]?.text.slice(0,160)}</p><small>{source.spans.length} source spans · v{source.version} · Original preserved</small></div><span class="row-arrow">↗</span></button>{:else}<div class="empty-state"><span>▱</span><h3>Add your first reference.</h3><p>Use policies, project records, and meeting notes as evidence.</p><button class="secondary" onclick={()=>fileInput?.click()}>Import reference</button></div>{/each}</div>
    {:else}
     <div class="section-caption"><span>Saved documents · {documents.length} items</span><small>Every saved version stays in your history.</small></div>
     <div class="documents-list">{#each documents as d(d.id)}<button class="document-row" disabled={working} onclick={()=>openDocument(d.id)}><span class="document-symbol">{d.family==='deck'?'▧':'▤'}</span><div><h3>{d.title}</h3><span>{labels[d.family]} · v{d.version} · {d.source_versions.length} references</span></div><time>{date(d.updated_at)}</time><span class="row-arrow">→</span></button>{:else}<div class="empty-state"><span>▤</span><h3>Your first document starts here.</h3><p>Choose a template to get started.</p><button class="secondary" onclick={()=>setView('templates')}>Browse templates</button></div>{/each}</div>
    {/if}
    <footer class="library-footer"><span>Fresh thinking. A structure worth keeping.</span><span>MY DOCUMENT MEMORY</span></footer>
   </main>
  {/if}
 </div>
</div>
{/if}

{#if selectedTemplate}
 <Modal {error} title="Template preview" onclose={()=>selectedTemplate=null}>
  <div class="template-detail"><span class="pill">{labels[selectedTemplate.form.family]} · {selectedTemplate.form.locale}</span><h2>{selectedTemplate.title}</h2><p>{selectedTemplate.summary}</p><ol class="section-list">{#each selectedTemplate.sections as section}<li>{section}</li>{/each}</ol><div class="attribution"><strong>{selectedTemplate.author}</strong><span>v{selectedTemplate.version} · {selectedTemplate.license}</span>{#if selectedTemplate.origin}<span>Original: {selectedTemplate.origin.author} · v{selectedTemplate.origin.version} · {selectedTemplate.origin.license}</span>{/if}{#each (selectedTemplate.attributions??[]).filter(a=>a.template_id!==selectedTemplate?.origin?.template_id) as attribution}<span>Also from: {attribution.author} · v{attribution.version} · {attribution.license}</span>{/each}</div>
   {#if connected&&selectedTemplate.visibility==='private'}<button class="secondary" onclick={()=>prepareContribution(selectedTemplate!)}>Contribute this template ↗</button>{/if}
   {#if !connected}<p class="subtle-note">Sign in to copy this template into your private space.</p><button class="primary" onclick={()=>{selectedTemplate=null;setView('me');}}>Sign in with email →</button>
   {:else if selectedTemplate.form.family==='sheet'}<p class="subtle-note">Spreadsheet templates offer a structure preview. Editing and formulas are planned.</p>
   {:else}<form onsubmit={(e)=>{e.preventDefault();void createDocument();}}><label class="field-label" for="new-title">New document title</label><input id="new-title" bind:value={newTitle} maxlength="120" required/><fieldset><legend>Select references <small>Optional</small></legend>{#each sources as source(source.id)}<label class="check-row"><input type="checkbox" bind:group={selectedSourceIds} value={source.id}/><span>{source.title}<small>v{source.version} · {source.spans.length} source spans</small></span></label>{:else}<p class="muted">Import a reference to include evidence in your draft.</p>{/each}</fieldset>
    {#if selectedTemplate.form.family==='deck'}<label class="check-row outline-approval"><input type="checkbox" bind:checked={outlineApproved}/><span>I approve this slide outline and order.</span></label>{/if}
    <p class="subtle-note">Drafts contain confirmation placeholders and selected source excerpts. Review and complete the missing details.</p>
    <AgentPrompt template={selectedTemplate} title={newTitle} sourceIds={selectedSourceIds} {sources} {outlineApproved} disabled={working}/>
    <div class="modal-actions"><button type="button" class="secondary" onclick={copyTemplate} disabled={working}>Copy to my templates</button><button class="primary" disabled={working||!newTitle.trim()||(selectedTemplate.form.family==='deck'&&!outlineApproved)}>{working?'Working…':'Use this template →'}</button></div>
   </form>{/if}
  </div>
 </Modal>
{/if}
{#if selectedSource}
 <Modal {error} title="Reference original" onclose={()=>selectedSource=null}><div class="source-detail"><span class="pill">{selectedSource.format.toUpperCase()} · v{selectedSource.version}</span><h2>{selectedSource.title}</h2><p class="muted">{selectedSource.filename} · Original file and extracted locations are preserved.</p>{#each selectedSource.spans as span}<section><small>{span.location} · {span.id}</small><p>{span.text}</p></section>{/each}<div class="modal-actions"><button class="secondary" disabled={working} onclick={()=>perform(()=>api!.download('/sources/'+selectedSource!.id+'/file',selectedSource!.filename))}>Download original ↧</button><button class="primary" disabled={working} onclick={sourceAsTemplate}>Save structure as a template</button></div></div></Modal>
{/if}
{#if customOpen}
 <Modal {error} title="New template" onclose={()=>customOpen=false}><form class="custom-form" onsubmit={(e)=>{e.preventDefault();void createCustom();}}><label for="custom-title">Template name</label><input id="custom-title" bind:value={customTitle} maxlength="120" required placeholder="e.g. Product review"/><label for="custom-type">Document type</label><select id="custom-type" bind:value={customType}>{#each types as [value,label]}<option {value}>{label}</option>{/each}</select><label for="custom-sections">Sections or slide outline</label><textarea id="custom-sections" rows="8" bind:value={customSections} required placeholder={'Background and Problem\nGoals\nProposal\nNext Steps'}></textarea><small class="muted">One section per line · up to 12 sections · 60 characters each. Your template stays private.</small><div class="modal-actions"><button class="primary" disabled={working||!customTitle.trim()||!customSections.trim()}>Save template →</button></div></form></Modal>
{/if}
<style>@media(max-width:760px){.search-row{flex-wrap:wrap}.search-form{flex-basis:100%;min-width:0}.search-row select{flex:1;min-width:0}}</style>
{#if contributionTemplate}<Modal {error} title="Contribute a template" onclose={()=>contributionTemplate=null}><ContributePanel template={contributionTemplate} bind:author={publicAuthor} bind:license={publicLicense} bind:rights={rightsConfirmed} {working} onsubmit={submitContribution}/></Modal>{/if}
{#if revisions}
 <Modal {error} title="Version history" onclose={()=>revisions=null}><div class="revision-list">{#each revisions as r}<button class:chosen={revisionPreview?.version===r.version} onclick={()=>revisionPreview=r}><strong>v{r.version} · {r.title}</strong><span>{date(r.updated_at)}</span></button>{/each}</div>{#if revisionPreview}<div class="revision-preview"><DocumentView title={revisionPreview.title} content={revisionPreview.content}/><button class="primary" onclick={()=>applyRevision(revisionPreview!)}>Apply this version to draft</button></div>{:else}<p class="muted">Choose a version to review its content.</p>{/if}</Modal>
{/if}
