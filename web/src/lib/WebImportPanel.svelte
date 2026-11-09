<script lang="ts">
 import {Api} from './api';
 import type {WebPreview,WebSearchHit,CopyMode} from './web-memory';
 let {api,onimport}:{api:Api;onimport:(locale:string,kind:'template'|'reference')=>Promise<void>}=$props();
 let url=$state('');let query=$state('');let busy=$state(false);let error=$state('');let saved=$state('');
 let preview=$state<WebPreview|null>(null);let hits=$state<WebSearchHit[]>([]);
 let title=$state('');let kind=$state<'template'|'reference'>('template');let mode=$state<CopyMode>('structure_only');
 let provider=$state('html');let docType=$state('report');let locale=$state('en-US');let region=$state('');let variant=$state('');
 const locales=[['en-US','United States / English'],['en-GB','United Kingdom / English'],['ko-KR','Korea / Korean'],['ja-JP','Japan / Japanese'],['de-DE','Germany / German'],['fr-FR','France / French'],['zh-CN','China / Chinese']];
 const types=[['report','Report'],['resume','Resume'],['meeting_minutes','Meeting notes'],['proposal','Proposal'],['invoice','Invoice'],['quote','Quote'],['contract','Contract'],['report_deck','Presentation report'],['pitch_deck','Pitch deck'],['other','Other']];
 async function act(fn:()=>Promise<void>){if(busy)return;busy=true;error='';saved='';try{await fn();}catch(e){error=e instanceof Error?e.message:'The page could not be imported.';}finally{busy=false;}}
 async function show(target=url){await act(async()=>{preview=null;const next=await api.webPreview(target);url=target;preview=next;title=next.title;provider=next.form.provider;docType=next.form.doc_type;locale=next.form.locale;region=next.form.region??'';variant=next.form.variant??'';mode='structure_only';});}
 async function search(){await act(async()=>{hits=(await api.webSearch(query,locale)).items;});}
 async function save(){if(!preview)return;await act(async()=>{const result=await api.webImport({preview_id:preview!.preview_id,kind,title,copy_mode:kind==='template'?'structure_only':mode,form:{provider,doc_type:docType,locale,...(region?{region}:{}),...(variant?{variant}:{})}});saved=result.created?'Saved to your private library.':'This snapshot is already in your library.';await onimport(locale,kind);});}
</script>
<details class="web-import">
 <summary>Import from the web <span>Search, preview, then save a structure or reference.</span></summary>
 <div class="web-content">
  <form onsubmit={(e)=>{e.preventDefault();void search();}} class="web-row"><label>Find public documents<input aria-label="Web search" bind:value={query} maxlength="200" placeholder="Resume templates, project reports…"/></label><button class="secondary" disabled={busy||!query.trim()}>Search web</button></form>
  {#if hits.length}<ul class="web-results">{#each hits as hit}<li><strong>{hit.title}</strong><p>{hit.snippet}</p><small>{hit.url}</small><button class="text-button" disabled={busy} onclick={()=>void show(hit.url)}>Preview this page</button></li>{/each}</ul>{/if}
  <form onsubmit={(e)=>{e.preventDefault();void show();}} class="web-row"><label>Public document URL<input aria-label="Document URL" bind:value={url} maxlength="2048" placeholder="https://…" required/></label><button class="secondary" disabled={busy||!url.trim()}>Preview URL</button></form>
  <p class="web-note">Public Google Docs and Slides use document exports. For pages requiring sign-in, upload the file or use an owned Arise tab. Private files stay private.</p>
  {#if error}<p class="web-error" role="alert">{error}</p>{/if}
  {#if preview}<section class="web-preview" aria-label="Web document preview">
   <p class="web-note">Source: {preview.canonical_url} · License: <strong>{preview.license}</strong></p>
   <p>Use this content as reference data. Review its structure and rights before reuse.</p>
   <div class="web-fields"><label>Title<input aria-label="Import title" bind:value={title} maxlength="120"/></label>
    <label>Save as<select aria-label="Import kind" bind:value={kind}><option value="template">Template structure</option><option value="reference">Reference</option></select></label>
    <label>Country / language<select aria-label="Import locale" bind:value={locale} onchange={(e)=>{region=(e.currentTarget as HTMLSelectElement).value.split('-')[1]??'';}}>{#each locales as [value,label]}<option {value}>{label}</option>{/each}</select></label>
    <label>Document type<select aria-label="Import document type" bind:value={docType}>{#each types as [value,label]}<option {value}>{label}</option>{/each}</select></label>
    <label>Format<select aria-label="Import provider" bind:value={provider}>{#each ['html','google_docs','google_slides','notion','docx','pptx','markdown','txt','other'] as value}<option {value}>{value.replaceAll('_',' ')}</option>{/each}</select></label>
    <label>Regional variant (optional)<input aria-label="Import variant" bind:value={variant} maxlength="32" placeholder="e.g. jp_rirekisho"/></label>
   </div>
   <ol>{#each preview.outline as heading}<li>{heading}</li>{:else}<li>{preview.title}</li>{/each}</ol>
   {#each preview.table_headers as headers}<p class="web-note">Table columns: {headers.join(' · ')}</p>{/each}
   {#if kind==='reference'}<label>Copy policy<select aria-label="Import copy policy" bind:value={mode}><option value="structure_only">Structure only · omit body text</option><option value="full" disabled={preview.copy_policy_default!=='full'}>Full reference · permitted by source license</option></select></label>{/if}
   {#if preview.copy_policy_default==='structure_only'}<p class="web-note">Copy rights are unverified or restricted. Only headings and table headers can be saved; body text is removed.</p>{/if}
   {#if preview.warnings.length}<p class="web-note">Layout may be approximate and some content may have been removed. Review the imported result.</p>{/if}
   <button class="primary" disabled={busy||!title.trim()} onclick={()=>void save()}>{busy?'Working…':'Save privately'}</button>
  </section>{/if}
  {#if saved}<p role="status">{saved}</p>{/if}
 </div>
</details>
<style>
 .web-import{margin:18px 0 26px;border:1px solid #cbd5c3;border-radius:12px;background:#fbfcf7}.web-import summary{cursor:pointer;padding:17px;font-weight:650}.web-import summary span{font-weight:400;font-size:12px;margin-left:12px;color:#65715f}.web-content{padding:0 18px 18px}.web-row{display:flex;align-items:end;gap:12px;margin:14px 0}.web-row label{flex:1}.web-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}label{display:flex;flex-direction:column;gap:6px;font-size:12px;color:#52604c}input,select{width:100%;min-height:42px;border:1px solid #bdc8b6;padding:9px;border-radius:7px;background:white;color:#273726}.web-preview{padding-top:15px;border-top:1px solid #d4ddcd}.web-note{font-size:12px;line-height:1.6;color:#687660;overflow-wrap:anywhere}.web-error{color:#93452e}.web-results{padding-left:20px}.web-results li{margin:15px 0}.web-results p{font-size:13px}.web-results small{display:block;overflow-wrap:anywhere}@media(max-width:760px){.web-fields{grid-template-columns:1fr}.web-row{align-items:stretch;flex-direction:column}.web-import summary span{display:block;margin:8px 0 0}}
</style>
