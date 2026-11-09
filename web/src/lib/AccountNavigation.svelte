<script lang="ts">
 let {active,connected,signedIn,onview,onlogout,busy=false}:{active:string;connected:boolean;signedIn:boolean;busy?:boolean;onlogout:()=>Promise<void>;onview:(view:'me'|'signin'|'public'|'contributions'|'review'|'leaderboard'|'signup')=>void}=$props();
</script>
<div class="account-navigation" aria-label="Account and community">
 <button class:active={active==='me'||active==='signin'} onclick={()=>onview(connected?'me':'signin')}><span aria-hidden="true">◈</span><span>{connected?'My page':'Sign in'}</span></button>
 {#if !signedIn}<button class:active={active==='signup'} onclick={()=>onview('signup')}><span aria-hidden="true">+</span><span>Create account</span></button>{/if}
 <button class:active={active==='leaderboard'} onclick={()=>onview('leaderboard')}><span aria-hidden="true">↗</span><span>Leaderboard</span></button>
 <button class:active={active==='public'} onclick={()=>onview('public')}><span aria-hidden="true">◎</span><span>Public memories</span></button>
 <button class:active={active==='contributions'} onclick={()=>onview('contributions')}><span aria-hidden="true">↗</span><span>My contributions</span></button>
 <button class:active={active==='review'} onclick={()=>onview('review')}><span aria-hidden="true">✓</span><span>Review contributions</span></button>
 {#if connected}<button class="mobile-signout" disabled={busy} onclick={onlogout}>Sign out</button>{/if}
</div>
<style>
 .mobile-signout{display:none!important}.account-navigation{display:flex;flex-direction:column;gap:7px;margin-bottom:12px}.account-navigation button{display:flex;align-items:center;gap:12px;border-radius:7px;padding:13px 12px;text-align:left;color:#7a8478;font-size:13px}.account-navigation button.active{background:#e2e9dc;color:#274d36;font-weight:650}.account-navigation button:hover:enabled{background:#e7ecdf}@media(max-width:700px){.account-navigation .mobile-signout{display:flex!important;flex:0 0 auto;}.account-navigation{grid-column:1/-1;flex-direction:row;flex-wrap:wrap;margin:14px 0 0;gap:4px}.account-navigation button{flex:1 1 30%;justify-content:center;padding:10px 4px;min-width:0;font-size:10px;gap:6px}}
</style>
