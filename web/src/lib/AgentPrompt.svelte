<script lang="ts">
 import type {Template,Source} from './types';
 import {buildAgentPrompt} from './prompt';
 let {template,title,sourceIds,sources,outlineApproved,disabled=false}:{
  template:Template;title:string;sourceIds:string[];sources:Source[];outlineApproved:boolean;disabled?:boolean;
 }=$props();
 let status=$state('');
 let area=$state<HTMLTextAreaElement>();
 const prompt=$derived(buildAgentPrompt(template,title,sourceIds,sources,outlineApproved));
 const ready=$derived(!disabled&&Boolean(title.trim())&&template.form.family!=='sheet'&&(template.form.family!=='deck'||outlineApproved));
 $effect(()=>{prompt;status='';});
 async function copy(){
  if(!ready)return;
  const request=prompt;
  try{
   if(!navigator.clipboard?.writeText)throw new Error('clipboard_unavailable');
   await navigator.clipboard.writeText(request);
   if(prompt===request)status='Prompt copied. Paste it into your connected agent.';
  }catch{
   area?.focus();area?.select();
   status='Clipboard access was blocked. The prompt is selected; copy it manually.';
  }
 }
</script>

<section class="agent-handoff" aria-labelledby="agent-handoff-title">
 <h3 id="agent-handoff-title">Take this to your agent</h3>
 <p id="agent-prompt-help">Use this request with an agent connected to the same library. It updates with your title and selected references.</p>
 <label for="agent-prompt">Agent prompt</label>
 <textarea id="agent-prompt" bind:this={area} value={prompt} readonly spellcheck="false" rows="10" aria-describedby="agent-prompt-help"></textarea>
 <div class="prompt-actions">
  <small>{template.form.family==='deck'&&!outlineApproved?'Approve the slide outline above before copying the request.':'Review the request, then paste it into your agent.'}</small>
  <button type="button" class="secondary" disabled={!ready} onclick={copy}>Copy prompt</button>
 </div>
 <p class="prompt-status" role="status" aria-live="polite">{status}</p>
</section>

<style>
 .agent-handoff{border-top:1px solid #dce3d8;margin-top:24px;padding-top:22px}
 h3{font-size:17px;margin:0 0 8px;font-weight:600}
 p{font-size:12px;line-height:1.7;color:#64756b}
 label{display:block;font-size:12px;font-weight:600;margin:15px 0 8px}
 textarea{box-sizing:border-box;width:100%;min-height:180px;max-height:360px;resize:vertical;padding:13px;border:1px solid #dce3d8;border-radius:6px;background:#f6f8f2;color:#314c3b;font:11px/1.7 ui-monospace,SFMono-Regular,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
 .prompt-actions{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-top:12px;flex-wrap:wrap}
 small{font-size:11px;line-height:1.7;color:#64756b;flex:1;min-width:170px}
 .prompt-status{min-height:1.7em;margin:9px 0 0;color:#345c40}
</style>
