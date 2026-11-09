<script lang="ts">
 import {Api} from './api';import type {WebOrigin} from './web-memory';
 let {id,api=null,isPublic=false}:{id:string;api?:Api|null;isPublic?:boolean}=$props();
 let origin=$state<WebOrigin|null>(null);
 $effect(()=>{let active=true;origin=null;const client=api??new Api();const request=isPublic?client.request<WebOrigin>('/public/templates/'+encodeURIComponent(id)+'/origin'):client.webOrigin(id);void request.then(value=>{if(active)origin=value;}).catch(()=>{});return()=>{active=false;};});
</script>
{#if origin}<aside class="web-source" aria-label="Original web source"><strong>Original web source</strong><p>{origin.canonical_url}</p><p>{origin.license} · {origin.copy_policy==='structure_only'?'Structure only':'Permitted reference copy'}</p><small>{origin.provenance==='captured'?'Captured from your browser':origin.provenance==='fetched'?'Imported from a public page':'Provided content'} · {new Date(origin.retrieved_at*1000).toLocaleDateString()}</small></aside>{/if}
<style>.web-source{margin:16px 0;padding:14px;border:1px solid #d4ddca;border-radius:8px;background:#f6f9f0}.web-source p{font-size:12px;overflow-wrap:anywhere;margin:8px 0}.web-source small{color:#69775e}</style>
