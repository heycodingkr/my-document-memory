<script lang="ts">
 import {onMount} from 'svelte';
 import {Api,ApiFailure} from './api';
 import type {Session} from './types';
 let {linkToken='',mode='signin',onlogin,onswitch=()=>{}}:{linkToken?:string;mode?:'signin'|'signup';onlogin:(session:Session)=>Promise<void>;onswitch?:(mode:'signin'|'signup')=>void}=$props();
 let email=$state('');let sent=$state(false);let busy=$state(false);let error=$state('');let enabled=$state<boolean|null>(null);let retryAt=$state(0);let now=$state(Date.now());let useLink=$state(true);
 const retry=$derived(Math.max(0,Math.ceil((retryAt-now)/1000)));
 const confirming=$derived(Boolean(linkToken)&&useLink);
 $effect(()=>{void mode;sent=false;error='';});
 $effect(()=>{if(linkToken){useLink=true;sent=false;error='';}});
 onMount(()=>{void new Api().authConfig().then(v=>enabled=v.email_enabled).catch(()=>error='Cannot connect to the sign-in server. Try again shortly.');const timer=setInterval(()=>now=Date.now(),1000);return()=>clearInterval(timer);});
 async function send(){if(busy)return;busy=true;error='';try{const result=await new Api().startEmailLink(email);sent=true;now=Date.now();retryAt=now+result.retry_after*1000;}catch{error='We could not send your sign-in link. Please try again shortly.';}finally{busy=false;}}
 async function verify(){if(busy)return;busy=true;error='';try{await onlogin(await new Api().consumeEmailLink(linkToken));}catch(e){error=e instanceof ApiFailure&&e.code==='auth_required'?'This sign-in link has expired or has already been used. Request a new link below.':'We could not complete sign-in. Please try this link again shortly.';}finally{busy=false;}}
</script>
<section class="email-login" aria-label="Email sign-in">
 <span class="eyebrow">YOUR OWN SPACE</span><h2>{confirming?'Your space is one click away.':mode==='signup'?'Your own space starts here.':'Continue to your memories'}</h2>
 {#if error}<p class="login-error" role="alert">{error}</p>{/if}
 {#if confirming}
  <p>Continue to your private templates, references, and documents.</p>
  <button class="primary" onclick={verify} disabled={busy}>{busy?'Signing in…':'Continue to my space'}</button>
  <div class="login-links"><button type="button" class="text-button" disabled={busy} onclick={()=>{useLink=false;error='';}}>Send a new sign-in link</button></div>
 {:else}
  <p>{mode==='signup'?'Anyone can create a free account with a personal email address. No invitation or organization account is required.':'Sign in with the link sent to your email. Your saved library will be waiting.'}</p>
  <p>Public memories are open to everyone. Sign in to request a contribution and follow its review status.</p>
  {#if enabled===false}<p class="setup-note">Email sign-in is being set up. Please try again later.</p>{/if}
  {#if sent}
   <p class="sent" role="status"><strong>Check your inbox.</strong><br/>A sign-in link is on its way to <strong>{email}</strong>. Open it within 10 minutes. You can use the link once.</p>
   <div class="login-links"><button type="button" class="text-button" onclick={send} disabled={busy||retry>0}>{retry>0?`Resend in ${retry}s`:'Resend sign-in link'}</button><button type="button" class="text-button" disabled={busy} onclick={()=>{sent=false;error='';}}>Change email</button></div>
  {:else}
   <form onsubmit={(e)=>{e.preventDefault();void send();}}><label for="login-email">Email address</label><div class="login-row"><input id="login-email" type="email" autocomplete="email" maxlength="254" bind:value={email} required placeholder="you@example.com" disabled={busy}/><button class="primary" disabled={busy||enabled!==true}>{busy?'Sending…':mode==='signup'?'Send account link':'Send sign-in link'}</button></div></form>
  {/if}
 {/if}
 {#if !confirming}<div class="login-links"><span>{mode==='signup'?'Already have an account?':'New to Document Memory?'}</span><button type="button" class="text-button" disabled={busy} onclick={()=>onswitch(mode==='signup'?'signin':'signup')}>{mode==='signup'?'Sign in':'Create an account'}</button></div>{/if}
 <small>No password needed. Your references are private by default.</small>
</section>
<style>
 .email-login{max-width:540px;background:#fffef9;border:1px solid #dedfd5;border-radius:12px;padding:30px;margin:26px 0;text-align:left}.email-login h2{font-size:25px;margin:10px 0;letter-spacing:-.04em}.email-login p{font-size:14px;line-height:1.7;color:#65705e}.email-login label{display:block;font-size:13px;margin:18px 0 8px}.login-row{display:flex;gap:8px}.login-row input{min-width:0;flex:1}.login-row button{white-space:nowrap}.email-login small{display:block;color:#727a6b;font-size:11px;margin-top:18px;line-height:1.7}.login-links{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:18px}.login-error{color:#9b3627!important;background:#fff1ec;padding:12px;border-radius:8px}.sent strong{overflow-wrap:anywhere}.setup-note{background:#f8f4e8;padding:12px;border-radius:8px}@media(max-width:600px){.email-login{padding:20px}.login-row{flex-direction:column}.login-row button{width:100%}}
</style>
