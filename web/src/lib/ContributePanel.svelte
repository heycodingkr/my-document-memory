<script lang="ts">
 import type {Template} from './types';
 let {template,author=$bindable(''),license=$bindable('CC-BY-4.0'),rights=$bindable(false),working,onsubmit}:{template:Template;author:string;license:string;rights:boolean;working:boolean;onsubmit:()=>Promise<void>}=$props();
</script>
<form class="custom-form" onsubmit={(e)=>{e.preventDefault();void onsubmit();}}>
 <span class="eyebrow">PUBLIC PREVIEW</span><h2>{template.title}</h2><p>{template.summary}</p><ol class="section-list">{#each template.sections as section}<li>{section}</li>{/each}</ol><p class="subtle-note">Only this template structure will be submitted. Your reference files and document content stay private. Check the title and outline for personal information before sharing.</p>
 <label for="public-author">Public author name</label><input id="public-author" bind:value={author} maxlength="80" required placeholder="A public name, not your email"/>
 <label for="public-license">Reuse license</label><select id="public-license" bind:value={license}><option value="CC-BY-4.0">CC BY 4.0 · reuse with attribution</option>{#if template.origin?.license!=='CC-BY-4.0'&&!(template.attributions??[]).some(a=>a.license==='CC-BY-4.0')}<option value="CC0-1.0">CC0 1.0 · public domain dedication</option>{/if}</select>
 {#if template.origin}<p class="muted">Original: {template.origin.author} · {template.origin.license}. Original attribution is preserved.</p>{/if}
 <label class="check-row"><input type="checkbox" bind:checked={rights} required/><span>I have the right to share this structure under the selected license. I have removed personal or confidential information.</span></label><p class="subtle-note">A reviewer checks your submission before it appears in public memories. You can withdraw it from My contributions.</p>
 <div class="modal-actions"><button class="primary" disabled={working||!rights||!author.trim()}>{working?'Submitting…':'Submit for review →'}</button></div>
</form>
