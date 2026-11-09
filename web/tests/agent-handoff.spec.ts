import {test,expect,type Page} from '@playwright/test';

test('public catalog defaults to English and preserves access to Korean originals',async({page})=>{
 await page.goto('/#public');
 await expect(page.getByRole('heading',{name:'Public memories.'})).toBeVisible();
 await expect(page.getByLabel('Public template language')).toHaveValue('en-US');
 await expect(page.getByRole('button',{name:'Meeting Notes and Action Items public preview',exact:true})).toBeVisible();
 expect(await page.locator('.public-grid').innerText()).not.toMatch(/[가-힣]/);
 await page.getByLabel('Public template language').selectOption('ko-KR');
 await expect(page.getByRole('button',{name:'회의록과 액션아이템 public preview',exact:true})).toBeVisible();
 await page.setViewportSize({width:320,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

const token=process.env.DMEM_E2E_TOKEN||'automated-smoke-token-not-production';
const headers={Authorization:'Bearer '+token};
async function connect(page:Page){
 await page.goto('/');
 await page.locator('#token').fill(token);
 await page.locator('form').filter({has:page.locator('#token')}).getByRole('button').click();
 await expect(page.locator('.template-grid')).toBeVisible();
}
async function setup(page:Page,deck=false){
 const title=(deck?'Outline demo ':'Prompt demo ')+Date.now();
 const t=await page.request.post('/v1/templates',{headers,data:{
  title,summary:'English handoff test',form:{provider:deck?'pptx':'docx',doc_type:deck?'report_deck':'report',locale:'en-US'},
  sections:['Purpose','Next Steps'],tags:[]
 }});expect(t.ok()).toBe(true);
 const template=await t.json();
 const s=await page.request.post('/v1/sources',{headers,multipart:{title:'Selected English Notes '+Date.now(),
  file:{name:'notes.md',mimeType:'text/markdown',buffer:Buffer.from('# Notes\nPRIVATE_BODY_SENTINEL: the pilot review is on 15 November 2026.')}
 }});expect(s.ok()).toBe(true);
 return {template,source:await s.json()};
}
async function preview(page:Page,title:string){
 await page.getByLabel('Library search').fill(title);
 await page.getByRole('button',{name:'Search',exact:true}).click();
 await page.locator('.template-card').filter({hasText:title}).locator('.card-preview').click();
 return page.getByRole('dialog');
}
function payload(prompt:string){const match=prompt.match(/```json\n([\s\S]*?)\n```/);expect(match).not.toBeNull();return JSON.parse(match![1]);}

test('copies the visible request with exact selections and no document side effect',async({page,context})=>{
 const {template,source}=await setup(page);
 await connect(page);
 // Stable selectors let this reproduce the missing prompt before UI translation.
 await page.locator('.search-form input').fill(template.title);
 await page.locator('.search-form button').click();
 await page.locator('.template-card').filter({hasText:template.title}).locator('.card-preview').click();
 const modal=page.getByRole('dialog');
 await modal.locator('#new-title').fill('Pilot Review Request');
 await modal.locator('input[type=checkbox][value="'+source.id+'"]').check();
 const promptBox=modal.getByLabel('Agent prompt');
 await expect(promptBox).toBeVisible({timeout:1500});
 const text=await promptBox.inputValue();const data=payload(text);
 expect(data.create_arguments).toEqual({title:'Pilot Review Request',template_id:template.id,source_ids:[source.id],outline_approved:false});
 expect(data.template.version).toBe(1);
 expect(data.template.sections).toEqual(['Purpose','Next Steps']);
 expect(data.references).toEqual([{id:source.id,version:1,title:source.title}]);
 expect(text.includes(token)||text.includes('PRIVATE_BODY_SENTINEL')).toBe(false);
 const creates:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname==='/v1/documents')creates.push(r.url());});
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 await modal.getByRole('button',{name:'Copy prompt',exact:true}).click();
 expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(text);
 await expect(modal.getByRole('status')).toContainText('Prompt copied');
 expect(creates).toEqual([]);
});

test('clipboard refusal keeps the request selectable and reports manual copying',async({page})=>{
 const {template}=await setup(page);await connect(page);
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}}));
 const modal=await preview(page,template.title);
 await modal.getByRole('button',{name:'Copy prompt',exact:true}).click();
 await expect(modal.getByRole('status')).toContainText('copy it manually');
 const selected=await modal.getByLabel('Agent prompt').evaluate((e:HTMLTextAreaElement)=>({start:e.selectionStart,end:e.selectionEnd,length:e.value.length}));
 expect(selected).toEqual({start:0,end:selected.length,length:selected.length});
});

test('deck requests require an approved outline and react to changed selections',async({page})=>{
 const {template}=await setup(page,true);await connect(page);
 const modal=await preview(page,template.title);const copy=modal.getByRole('button',{name:'Copy prompt',exact:true});
 await expect(copy).toBeDisabled();
 const approved=modal.getByRole('checkbox',{name:'I approve this slide outline and order.'});
 await approved.check();await expect(copy).toBeEnabled();
 expect(payload(await modal.getByLabel('Agent prompt').inputValue()).create_arguments.outline_approved).toBe(true);
 await approved.uncheck();await expect(copy).toBeDisabled();
 await approved.check();await modal.getByLabel('New document title').fill('   ');await expect(copy).toBeDisabled();
});

test('landing and default catalog are English and custom templates use en-US',async({page})=>{
 await page.goto('/');await expect(page.locator('html')).toHaveAttribute('lang','en');
 expect(await page.locator('body').innerText()).not.toMatch(/[가-힣]/);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.setViewportSize({width:1440,height:1100});
 await connect(page);
 await expect(page.getByLabel('Template language')).toHaveValue('en-US');
 await expect(page.locator('.template-card').filter({hasText:'Public template'}).getByRole('button',{name:'Meeting Notes and Action Items preview',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'+ New template',exact:true}).click();
 const modal=page.getByRole('dialog');
 await modal.getByLabel('Template name').fill('English custom '+Date.now());
 await modal.getByLabel('Sections or slide outline').fill('Purpose\nNext Steps');
 await modal.getByRole('button',{name:'Save template →',exact:true}).click();
 await expect(modal.locator('.pill')).toContainText('en-US');
});
