<script lang="ts">
 import {onMount} from 'svelte';
 import {AdministratorApi,type AdministratorSession} from './admin-api';
 let {linkToken='',onsignedin}:{linkToken?:string;onsignedin:(value:AdministratorSession)=>Promise<void>}=$props();
 let email=$state('');let sent=$state(false);let busy=$state(false);let enabled=$state<boolean|null>(null);let error=$state('');
 let useLink=$state(true);let retryAt=$state(0);let now=$state(Date.now());
 const confirming=$derived(Boolean(linkToken)&&useLink);
 const retry=$derived(Math.max(0,Math.ceil((retryAt-now)/1000)));
 $effect(()=>{if(linkToken){useLink=true;sent=false;error='';}});
 onMount(()=>{void new AdministratorApi().configuration().then(value=>enabled=value.enabled).catch(()=>error='Administrator sign-in is temporarily unavailable. Try again shortly.');const timer=setInterval(()=>now=Date.now(),1000);return()=>clearInterval(timer);});
 async function send(){if(busy)return;busy=true;error='';try{const result=await new AdministratorApi().sendLink(email);sent=true;now=Date.now();retryAt=now+result.retry_after*1000;}catch{error='We could not request your administrator link. Try again shortly.';}finally{busy=false;}}
 async function confirm(){if(busy)return;busy=true;error='';try{await onsignedin(await new AdministratorApi().consumeLink(linkToken));}catch{error='This administrator link is invalid, expired, already used, or no longer authorized. Request a new link.';}finally{busy=false;}}
</script>
<section class="administrator-login" aria-label="Administrator sign-in">
 <span class="eyebrow">AUTHORIZED REVIEWERS</span><h2>{confirming?'Confirm administrator sign-in':'Administrator sign-in'}</h2>
 {#if error}<p role="alert" class="login-error">{error}</p>{/if}
 {#if confirming}
  <p>Continue to the contribution queue. Review findings before approving or rejecting a memory.</p>
  <button class="primary" disabled={busy} onclick={confirm}>{busy?'Signing in…':'Continue as administrator'}</button>
  <button class="text-button" disabled={busy} onclick={()=>{useLink=false;error='';}}>Request a new administrator link</button>
 {:else}
  <p>Only authorized reviewer email addresses can receive an administrator sign-in link.</p>
  {#if enabled===false}<p class="setup-note">Administrator sign-in is unavailable. Contact the site operator.</p>{/if}
  {#if sent}
   <p role="status" class="sent"><strong>Check your inbox.</strong><br/>If this email is authorized, a sign-in link will arrive shortly. Open it within 10 minutes. It can be used once.</p>
   <div class="login-actions"><button class="text-button" disabled={busy||retry>0} onclick={send}>{retry>0?`Resend in ${retry}s`:'Resend administrator link'}</button><button class="text-button" disabled={busy} onclick={()=>{sent=false;error='';}}>Change email</button></div>
  {:else}
   <form onsubmit={(event)=>{event.preventDefault();void send();}}><label for="administrator-email">Administrator email</label><input id="administrator-email" type="email" autocomplete="email" maxlength="254" bind:value={email} required disabled={busy} placeholder="reviewer@example.com"/><button class="primary" disabled={busy||enabled!==true}>{busy?'Requesting…':'Send administrator link'}</button></form>
  {/if}
 {/if}
 <small>No password or administrator token to enter. Sign out to lock the review queue.</small>
</section>
<style>
 .administrator-login{max-width:550px;background:white;border:1px solid var(--line);border-radius:14px;padding:30px;display:grid;gap:16px}.administrator-login h2{font-size:24px;margin:0}.administrator-login p{font-size:13px;line-height:1.7;color:var(--muted);margin:0}.administrator-login form{display:grid;gap:12px}.administrator-login label{font-size:12px}.administrator-login input{min-width:0;width:100%}.administrator-login .primary{justify-self:start}.administrator-login small{font-size:11px;color:var(--muted);line-height:1.7}.administrator-login .text-button{font-size:12px;text-align:left}.login-actions{display:flex;flex-wrap:wrap;gap:18px}.login-error{color:#9b3627!important;background:#fff1ec;padding:12px;border-radius:6px}.setup-note{background:#f8f4e8;padding:12px;border-radius:6px}@media(max-width:700px){.administrator-login{padding:22px}.administrator-login .primary{width:100%}}
</style>
