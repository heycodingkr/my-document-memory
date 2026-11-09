import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

const mailbox=process.env.DMEM_E2E_MAILBOX;
test.skip(!mailbox,'Requires isolated accounts_fixture and synthetic mailbox');

test('a library connection still offers personal signup and requests email sign-in for web contributions',async({page})=>{
 await page.goto('/');
 await page.getByLabel('Library connection token').fill('automated-smoke-token-not-production');
 await page.getByRole('button',{name:'Open library'}).click();
 await expect(page.getByRole('heading',{name:'Template library.'})).toBeVisible();
 expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 await page.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Create your free account.'})).toBeVisible();
 await page.getByRole('button',{name:'My contributions',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Sign in.',exact:true})).toBeVisible();
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
});

test('public memories support anonymous search and full previews with optional personal signup',async({page})=>{
 await page.goto('/#public');
 await expect(page.getByRole('heading',{name:'Public memories.'})).toBeVisible();
 await expect(page.getByText('Open to everyone',{exact:false})).toBeVisible();
 await expect(page.getByText('Browse, search, and preview memories without signing in.')).toBeVisible();
 const catalog=await page.request.get('/v1/public/templates?locale=en-US');
 expect(catalog.status()).toBe(200);
 const template=(await catalog.json()).items[0];
 await page.getByLabel('Search public templates',{exact:true}).fill(template.title);
 await page.getByRole('button',{name:'Search',exact:true}).click();
 await page.getByRole('button',{name:template.title+' public preview',exact:true}).click();
 const modal=page.getByRole('dialog');
 await expect(modal.getByRole('heading',{name:template.title,exact:true})).toBeVisible();
 await expect(modal.locator('.section-list li')).toHaveText(template.sections);
 expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 expect((await page.request.post('/v1/me/contributions',{data:{template_id:template.id}})).status()).toBe(401);
 await modal.getByRole('button',{name:'Close',exact:true}).click();
 await page.locator('.public-actions').getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Create your free account.'})).toBeVisible();
 await expect(page.getByRole('region',{name:'Email sign-in'})).toContainText('No invitation or organization account is required.');
 await page.getByRole('button',{name:'Browse public memories →',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Public memories.'})).toBeVisible();
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:1000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:(process.env.DMEM_E2E_OUTPUT_DIR||'test-results')+'/anonymous-public-memories-'+width+'.png',fullPage:true});
 }
 await page.locator('.public-actions').getByRole('button',{name:'Sign in to contribute →',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Sign in.',exact:true})).toBeVisible();
 await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
});

test('contribution sign-in returns a new individual member to requests and all four statuses persist',async({page,request})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/#contributions');
 await expect(page.getByRole('heading',{name:'Sign in.',exact:true})).toBeVisible();
 await page.getByRole('region',{name:'Email sign-in'}).getByRole('button',{name:'Create an account',exact:true}).click();
 const email='individual-access-'+Date.now()+'@example.test';
 await page.getByLabel('Email address',{exact:true}).fill(email);
 await page.getByRole('button',{name:'Send account link',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('Check your inbox.');
 await expect.poll(()=>{try{return JSON.parse(readFileSync(mailbox!,'utf8')).email;}catch{return '';}}).toBe(email);
 await page.goto(JSON.parse(readFileSync(mailbox!,'utf8')).url);
 await page.getByRole('button',{name:'Continue to my space',exact:true}).click();
 await expect(page.getByRole('heading',{name:'My contributions.'})).toBeVisible();
 await expect(page.getByText(email,{exact:true})).toBeVisible();
 const session=await (await page.request.get('/v1/auth/session')).json();
 const origin=new URL(page.url()).origin;
 const headers={Origin:origin,'X-CSRF-Token':session.csrf_token};
 const admin={Origin:origin,Authorization:'Bearer synthetic-e2e-admin-token-at-least-32-characters'};
 const submissions:Record<string,{id:string;snapshot:{title:string;id:string}}>={};
 for(const status of ['pending','approved','rejected','withdrawn']){
  const title='Individual '+status+' '+Date.now().toString(36);
  const template=await page.request.post('/v1/templates',{headers,data:{title,summary:'Personal contribution status verification',form:{provider:'docx',doc_type:'report',locale:'en-US'},sections:[status+' assumptions',status+' evidence',status+' decisions'],tags:[]}});
  expect(template.status()).toBe(200);
  const submitted=await page.request.post('/v1/me/contributions',{headers,data:{template_id:(await template.json()).id,author:'Individual contributor',license:'CC-BY-4.0',rights_confirmed:true}});
  expect(submitted.status()).toBe(200);const contribution=await submitted.json();
  expect(contribution.status).toBe('pending');submissions[status]=contribution;
  if(status==='approved'||status==='rejected'){
   const result=await request.post('/v1/admin/contributions/'+contribution.id+'/decision',{headers:admin,data:{decision:status==='approved'?'approve':'reject'}});
   expect(result.status()).toBe(200);
  }else if(status==='withdrawn'){
   expect((await page.request.post('/v1/me/contributions/'+contribution.id+'/withdraw',{headers})).status()).toBe(200);
  }
  expect((await request.get('/v1/public/templates/'+contribution.snapshot.id)).status()).toBe(status==='approved'?200:404);
 }
 await page.getByRole('button',{name:'Refresh status',exact:true}).click();
 const filters=page.getByRole('group',{name:'Filter contributions by status'});
 await expect(filters.getByRole('button',{name:'All (4)',exact:true})).toBeVisible();
 for(const [status,label] of Object.entries({pending:'Awaiting review',approved:'Approved · Public',rejected:'Rejected',withdrawn:'Withdrawn'})){
  const row=page.getByRole('article',{name:submissions[status].snapshot.title+' contribution',exact:true});
  await expect(row.getByText(label,{exact:true})).toBeVisible();
  await expect(row.locator('time')).toHaveCount(2);
  await filters.getByRole('button',{name:label+' (1)',exact:true}).click();
  await expect(page.locator('article.contribution')).toHaveCount(1);
  await expect(row).toBeVisible();
  await filters.getByRole('button',{name:'All (4)',exact:true}).click();
 }
 await page.reload();await expect(page.locator('article.contribution')).toHaveCount(4);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:(process.env.DMEM_E2E_OUTPUT_DIR||'test-results')+'/personal-contribution-statuses-mobile.png',fullPage:true});
 await page.getByRole('button',{name:'Sign out',exact:true}).click();
 expect((await page.request.get('/v1/me/contributions')).status()).toBe(401);
 await page.getByRole('button',{name:'Public memories',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Public memories.'})).toBeVisible();
 expect(errors).toEqual([]);
});
