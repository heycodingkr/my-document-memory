<script lang="ts">
 import {onDestroy,onMount} from 'svelte';
 import {ApiFailure} from './api';
 import {AdministratorApi,type AdministratorSession} from './admin-api';
 import AdministratorSignIn from './AdministratorSignIn.svelte';
 import type {Contribution,ContributionQueueStatus,ReviewReport} from './types';
 import ReviewStages from './ReviewStages.svelte';
 let {linkToken='',onconsumed=()=>{}}:{linkToken?:string;onconsumed?:()=>void}=$props();
 let api=$state<AdministratorApi|null>(null);let queue=$state<Contribution[]>([]);let restoring=$state(true);
 let selected=$state<Contribution|null>(null);let report=$state<ReviewReport|null>(null);
 let working=$state(false);let loading=$state(false);let error=$state('');let notice=$state('');let confirmed=$state(false);
 let filter=$state<ContributionQueueStatus>('pending');let nextCursor=$state<string|null>(null);let epoch=0;
 function fail(e:unknown){error=e instanceof Error?e.message:'The review request failed.';}
 function clearQueue(){queue=[];nextCursor=null;selected=null;report=null;confirmed=false;notice='';}
 function clearLocal(){++epoch;api=null;clearQueue();filter='pending';error='';working=false;loading=false;restoring=false;}
 function handleError(e:unknown){if(e instanceof ApiFailure&&e.code==='auth_required')clearLocal();fail(e);}
 $effect(()=>{if(linkToken)clearLocal();});
 onDestroy(clearLocal);
 onMount(()=>{if(linkToken){restoring=false;return;}void restore();});
 async function restore(){const current=++epoch;try{const value=await new AdministratorApi().currentSession();if(current===epoch)await signedIn(value);}catch(e){if(current===epoch&&!(e instanceof ApiFailure&&e.code==='auth_required'))fail(e);}finally{if(current===epoch)restoring=false;}}
 async function signedIn(value:AdministratorSession){
  ++epoch;api=new AdministratorApi(value.csrf_token);restoring=false;filter='pending';onconsumed();await loadPage();
 }
 async function lock(){if(!api||working||loading)return;working=true;error='';try{await api.signOut();clearLocal();notice='Administrator signed out.';}catch(e){handleError(e);}finally{working=false;}}
 async function loadPage(append=false){
  if(!api||working||loading||(append&&!nextCursor))return;
  const current=epoch;const candidate=api;const cursor=append?nextCursor:undefined;
  loading=true;error='';if(!append)clearQueue();
  try{
   const result=await candidate.reviewQueue(filter,cursor??undefined);
   if(current===epoch){const known=new Set(queue.map(c=>c.id));queue=append?[...queue,...result.items.filter(c=>!known.has(c.id))]:result.items;nextCursor=result.next_cursor;}
  }catch(e){if(current===epoch)handleError(e);}
  finally{if(current===epoch)loading=false;}
 }
 function refresh(){return loadPage();}
 function changeFilter(value:ContributionQueueStatus){if(working||loading)return;filter=value;void loadPage();}
 async function open(c:Contribution){
  if(!api||working||loading)return;const current=epoch;loading=true;error='';notice='';confirmed=false;selected=null;report=null;
  try{const result=await api.review(c.id);if(current===epoch){selected=c;report=result;}}
  catch(e){if(current===epoch)handleError(e);}finally{if(current===epoch)loading=false;}
 }
 async function decide(decision:'approve'|'reject'){
  if(!api||!selected||!report||!confirmed||working||loading||selected.status!=='pending'||(decision==='approve'&&report.verdict==='blocked'))return;
  const current=epoch;const id=selected.id;working=true;error='';notice='';
  try{
   const result=await api.decide(id,decision);if(current!==epoch)return;
   selected=result;report=result.review??null;confirmed=false;queue=queue.map(c=>c.id===id?result:c).filter(c=>filter==='all'||c.status===filter);
   notice=decision==='approve'?'Contribution published. It is now available in public memories.':'Contribution rejected. The snapshot remains private to its owner and reviewers.';
  }catch(e){
   if(current===epoch){handleError(e);if(api)try{const fresh=await api.review(id);if(current===epoch){report=fresh;confirmed=false;}}catch{}}
  }finally{if(current===epoch)working=false;}
 }
</script>
<main class="review-page">
 <header class="review-heading"><div><span class="eyebrow">COMMUNITY / REVIEW</span><h1>Contribution review<span>.</span></h1><p>Check the shared structure, then make an explicit publishing decision.</p></div>{#if api}<button class="secondary" disabled={working||loading} onclick={lock}>Sign out and lock queue</button>{/if}</header>
 {#if error}<div class="alert" role="alert">{error}</div>{/if}
 {#if notice}<div class="notice" role="status">{notice}</div>{/if}
 {#if restoring}
 <p role="status">Checking administrator session…</p>
 {:else if !api}
 <AdministratorSignIn {linkToken} onsignedin={signedIn}/>
 {:else}
 <div class="review-grid">
  <section class="queue" aria-label="Contribution queue">
   <div class="queue-tools"><label for="queue-filter">Show submissions</label><select id="queue-filter" value={filter} disabled={working||loading} onchange={event=>changeFilter(event.currentTarget.value as ContributionQueueStatus)}><option value="pending">Awaiting review</option><option value="all">All statuses</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="withdrawn">Withdrawn</option></select><button class="text-button" disabled={working||loading} onclick={refresh}>Refresh queue</button></div>
   {#if loading}<p role="status">Loading review…</p>{/if}
   {#each queue as c (c.id)}
    <button class="queue-item" class:chosen={selected?.id===c.id} disabled={working||loading} aria-label={'Review '+c.snapshot.title} onclick={()=>open(c)}><strong>{c.snapshot.title}</strong><span>{c.snapshot.author} · v{c.snapshot.version}</span><small>{c.status==='pending'?'Awaiting review':c.status}</small></button>
   {:else}{#if !loading&&!nextCursor}<p class="empty-queue">No submissions in this view.</p>{/if}{/each}
   {#if queue.length}<p class="empty-queue">{queue.length} submissions loaded.</p>{/if}
   {#if nextCursor}<button class="secondary load-more" disabled={working||loading} onclick={()=>loadPage(true)}>Load more submissions</button>{/if}
  </section>
  <section class="review-detail" aria-label="Submission review">
   {#if selected&&report}
    <span class="eyebrow">SUBMITTED SNAPSHOT / {selected.status.toUpperCase()}</span><h2>{selected.snapshot.title}</h2><p class="summary">{selected.snapshot.summary}</p>
    <div class="attribution"><span>{selected.snapshot.author}</span><span>{selected.snapshot.license}</span><span>v{selected.snapshot.version} · {selected.snapshot.form.locale}</span></div>
    <ol class="section-list">{#each selected.snapshot.sections as section}<li>{section}</li>{/each}</ol>
    {#if selected.snapshot.tags.length}<p class="muted">Tags: {selected.snapshot.tags.join(', ')}</p>{/if}
    <ReviewStages {report}/>
    {#if selected.status==='pending'}
     <label class="check-row"><input type="checkbox" bind:checked={confirmed} disabled={working}/><span>I reviewed the snapshot and findings.</span></label>
     <div class="decision-actions"><button class="primary" disabled={working||!confirmed||report.verdict==='blocked'} onclick={()=>decide('approve')}>Approve and publish</button><button class="secondary" disabled={working||!confirmed} onclick={()=>decide('reject')}>Reject submission</button></div>
    {/if}
   {:else}<div class="empty-detail"><span class="eyebrow">REVIEW BEFORE SHARING</span><h2>Select a submission</h2><p>Review checks do not publish anything. Approval makes only the submitted structure public.</p></div>{/if}
  </section>
 </div>
 {/if}
</main>
<style>
 .review-page{padding:42px 46px;max-width:1500px;margin:auto}.review-heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:30px}.review-heading h1{font-size:38px;margin:12px 0}.review-heading h1 span{color:#dfa86b}.review-heading p{font-size:13px;color:var(--muted);margin-bottom:0}.review-grid{display:grid;grid-template-columns:minmax(220px, .75fr) minmax(0,1.8fr);gap:24px;align-items:start}.queue,.review-detail{min-width:0;background:white;border:1px solid var(--line);border-radius:14px;padding:22px}.queue-tools{display:grid;gap:10px;padding-bottom:18px;border-bottom:1px solid var(--line)}.load-more{width:100%;margin-top:16px;font-size:12px}.queue-tools label{font-size:11px}.queue-tools .text-button{text-align:left;font-size:11px}.queue-item{display:grid;gap:8px;width:100%;padding:20px 12px;text-align:left;border-bottom:1px solid var(--line);overflow-wrap:anywhere;border-radius:5px}.queue-item strong{font-size:13px}.queue-item span,.queue-item small{font-size:10px;color:var(--muted)}.queue-item.chosen{background:var(--soft)}.review-detail{padding:30px}.review-detail h2{margin:14px 0;font-size:26px;overflow-wrap:anywhere}.summary{font-size:12px;overflow-wrap:anywhere;white-space:pre-wrap}.decision-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}.decision-actions button{font-size:12px}.empty-detail{padding:50px 10px}.empty-detail p,.empty-queue{font-size:12px;color:var(--muted)}.review-page>.alert,.review-page>.notice{margin:0 0 24px;overflow-wrap:anywhere}@media(max-width:1000px){.review-page{padding:30px 24px}.review-grid{grid-template-columns:1fr}.queue{padding:18px}.queue-item{padding:15px 10px}}@media(max-width:700px){.review-page{padding:28px 18px}.review-heading{align-items:flex-start;flex-direction:column}.review-heading h1{font-size:29px}.review-detail{padding:22px 18px}.review-detail h2{font-size:24px}.decision-actions button{width:100%}.review-heading .secondary{font-size:11px}}
</style>
