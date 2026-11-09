import {test,expect} from '@playwright/test';
import {signInAdministrator} from './helpers/administrator';
const admin='synthetic-e2e-admin-token-at-least-32-characters';
const owner='automated-smoke-token-not-production';
test.skip(!process.env.DMEM_E2E_MAILBOX,'Requires isolated synthetic email fixture: python3 tests/smoke/accounts-v1.py');

async function submission(request: import('@playwright/test').APIRequestContext, baseURL:string, unsafe=false){
 const headers={Authorization:'Bearer '+owner,Origin:baseURL};
 const title='Review UI '+(unsafe?'blocked ':'clean ')+Date.now().toString(36);
 const t=await request.post('/v1/templates',{headers,data:{title,
  summary:unsafe?'synthetic-person@example.test':'Synthetic reusable structure only',
  form:{provider:'docx',doc_type:'report',locale:'en-US'},
  sections:unsafe?['Unique blocked structure','Review rationale']:['Novel planning context','Independent acceptance criteria','Decision rationale'],tags:[]}});
 expect(t.status()).toBe(200);
 const c=await request.post('/v1/me/contributions',{headers,data:{template_id:(await t.json()).id,
  author:'Synthetic reviewer fixture',license:'CC-BY-4.0',rights_confirmed:true}});
 expect(c.status()).toBe(200);return {title,...await c.json()};
}

test('MC-12: interactive admin review publishes only after explicit confirmation',async({page,request,baseURL})=>{
 const c=await submission(request,baseURL!);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/#review');
 await expect(page.getByRole('heading',{name:'Contribution review.'})).toBeVisible();
 expect((await request.get('/v1/admin/contributions',{headers:{Authorization:'Bearer '+owner}})).status()).toBe(401);
 await signInAdministrator(page,'reviewer@example.test');
 await page.getByRole('button',{name:'Review '+c.title,exact:true}).click();
 await expect(page.getByRole('heading',{name:c.title,exact:true})).toBeVisible();
 await expect(page.getByLabel('Review stages').locator('li')).toHaveCount(6);
 await expect(page.getByText('Ready for a decision',{exact:true})).toBeVisible();
 expect((await request.get('/v1/public/templates/'+c.snapshot.id)).status()).toBe(404);
 const approve=page.getByRole('button',{name:'Approve and publish',exact:true});
 await expect(approve).toBeDisabled();
 await page.getByLabel('I reviewed the snapshot and findings.').check();
 await approve.click();
 await expect(page.getByRole('status')).toContainText('Contribution published');
 expect((await request.get('/v1/public/templates/'+c.snapshot.id)).status()).toBe(200);
 const saved=await request.get('/v1/admin/contributions/'+c.id+'/review',{headers:{Authorization:'Bearer '+admin,Origin:baseURL!}});
 expect((await saved.json()).decision).toBe('approve');
 const storage=await page.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}));
 expect(storage).not.toContain(admin);
 await page.reload();
 await expect(page.getByRole('button',{name:'Sign out and lock queue',exact:true})).toBeVisible();
 await expect(page.getByLabel('Administrator token',{exact:true})).toHaveCount(0);
 expect(errors).toEqual([]);
});

test('MC-13: blocked review cannot approve, can reject, and fits narrow screens',async({page,request,baseURL})=>{
 const c=await submission(request,baseURL!,true);
 await page.goto('/#review');
 await signInAdministrator(page,'reviewer-blocked@example.test');
 await page.getByRole('button',{name:'Review '+c.title,exact:true}).click();
 await expect(page.getByText('Changes required before approval',{exact:true})).toBeVisible();
 await expect(page.getByText('Email address detected',{exact:true})).toBeVisible();
 await page.getByLabel('I reviewed the snapshot and findings.').check();
 await expect(page.getByRole('button',{name:'Approve and publish',exact:true})).toBeDisabled();
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('button',{name:'Reject submission',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('Contribution rejected');
 expect((await request.get('/v1/public/templates/'+c.snapshot.id)).status()).toBe(404);
 await page.screenshot({path:(process.env.DMEM_E2E_OUTPUT_DIR||'test-results')+'/administrator-review-mobile.png'});
 await page.getByRole('button',{name:'Sign out and lock queue',exact:true}).click();
 await expect(page.getByLabel('Administrator email',{exact:true})).toHaveValue('');
 await expect(page.getByRole('heading',{name:c.title,exact:true})).toHaveCount(0);
});
