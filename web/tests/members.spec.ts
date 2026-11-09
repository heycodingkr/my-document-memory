import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
const mailbox=process.env.DMEM_E2E_MAILBOX;
const screenshots=process.env.DMEM_E2E_OUTPUT_DIR||'test-results';
test.skip(!mailbox,'Requires synthetic member fixture: python3 tests/smoke/accounts-v1.py');
async function signup(page:Page,label:string){
 const email=label+'-'+Date.now()+'@example.test';await page.goto('/#signup');
 await expect(page.getByRole('heading',{name:'Create your free account.'})).toBeVisible();
 await page.getByLabel('Email address',{exact:true}).fill(email);await page.getByRole('button',{name:'Send account link',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('Check your inbox.');
 await expect.poll(()=>{try{return JSON.parse(readFileSync(mailbox!,'utf8')).email;}catch{return '';}}).toBe(email);
 const url=JSON.parse(readFileSync(mailbox!,'utf8')).url;expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 await page.goto(url);await expect(page).toHaveURL(/\/#me$/);
 await page.getByRole('button',{name:'Continue to my space',exact:true}).click();await expect(page.getByRole('heading',{name:'My page.'})).toBeVisible();
 const session=await (await page.request.get('/v1/auth/session')).json();return {email,csrf:session.csrf_token,id:session.account.id};
}
async function profile(page:Page,handle:string,visible:boolean){
 const panel=page.getByRole('region',{name:'Membership and contribution points'});
 await expect(panel.getByLabel('Public handle',{exact:false})).toBeEnabled();
 await panel.getByLabel('Public handle',{exact:false}).fill(handle);await panel.getByRole('checkbox').setChecked(visible);
 await panel.getByRole('button',{name:'Save profile',exact:true}).click();
 await expect(panel.getByRole('status')).toHaveText(visible?'Your public profile is visible.':'Your profile is private.');return panel;
}
async function publish(page:Page,csrf:string,n:number){
 const origin=new URL(page.url()).origin;const headers={Origin:origin,'X-CSRF-Token':csrf};
 const t=await page.request.post('/v1/templates',{headers,data:{title:'Community research plan '+n,summary:'Original research structure '+n,form:{provider:'docx',doc_type:'report',locale:'en-US'},sections:['Research background '+n,'Experiment protocol '+n,'Review decisions '+n],tags:[]}});expect(t.status()).toBe(200);const template=await t.json();
 const c=await page.request.post('/v1/me/contributions',{headers,data:{template_id:template.id,author:'Synthetic researcher',license:'CC-BY-4.0',rights_confirmed:true}});expect(c.status()).toBe(200);const contribution=await c.json();
 const a=await page.request.post('/v1/admin/contributions/'+contribution.id+'/decision',{headers:{Origin:origin,Authorization:'Bearer synthetic-e2e-admin-token-at-least-32-characters'},data:{decision:'approve'}});expect(a.status()).toBe(200);return {template,contribution};
}
test('LB-01/18: distinct signup, private member defaults, opt-in profile and direct public navigation',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');const header=page.locator('.landing-header');await expect(header.getByRole('button',{name:'Sign in',exact:false})).toBeVisible();await expect(header.getByRole('button',{name:'Leaderboard',exact:true})).toBeVisible();await header.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Create your free account.'})).toBeVisible();
 const auth=page.getByRole('region',{name:'Email sign-in'});await auth.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Sign in.',exact:true})).toBeVisible();
 const user=await signup(page,'signup');let panel=page.getByRole('region',{name:'Membership and contribution points'});await expect(panel.getByTestId('member-points')).toHaveText('0');await expect(panel.getByRole('checkbox')).not.toBeChecked();
 const handle='new-member-'+Date.now();panel=await profile(page,handle,true);await panel.getByRole('button',{name:'View my public profile ↗'}).click();
 await expect(page.getByRole('heading',{name:'@'+handle,exact:true})).toBeVisible();await expect(page.locator('main')).not.toContainText(user.email);await page.reload();await expect(page.getByRole('heading',{name:'@'+handle,exact:true})).toBeVisible();
 await page.getByRole('button',{name:'My page',exact:true}).click();panel=page.getByRole('region',{name:'Membership and contribution points'});await expect(panel.getByLabel('Public handle',{exact:false})).toHaveValue(handle);
 await profile(page,handle,false);expect((await page.request.get('/v1/profiles/'+handle)).status()).toBe(404);
 expect(errors).toEqual([]);
});
test('LB-18/20: approved contributions drive real points, opt-in ranking, public profile and withdrawal',async({page,browser,request})=>{
 const alice=await signup(page,'rank-alice');const ah='alpha-'+Date.now();await profile(page,ah,true);const first=await publish(page,alice.csrf,201);await publish(page,alice.csrf,202);
 await page.getByRole('button',{name:'My page',exact:true}).click();let panel=page.getByRole('region',{name:'Membership and contribution points'});await expect(panel.getByTestId('member-points')).toHaveText('40');await expect(panel.getByTestId('overall-rank')).toHaveText('#1');
 const other=await browser.newContext();const bobPage=await other.newPage();
 try{
  const bob=await signup(bobPage,'rank-bob');const bh='beta-'+Date.now();await publish(bobPage,bob.csrf,203);await bobPage.getByRole('button',{name:'My page',exact:true}).click();
  const bp=bobPage.getByRole('region',{name:'Membership and contribution points'});await expect(bp.getByTestId('member-points')).toHaveText('20');await expect(bp.getByTestId('overall-rank')).toHaveText('#2');await expect(bp.getByTestId('public-rank')).toHaveText('Not ranked');
  await profile(bobPage,bh,true);await page.getByRole('button',{name:'Leaderboard',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Leaderboard.'})).toBeVisible();await expect(page.getByRole('table').getByRole('row')).toHaveCount(3);
  await page.getByRole('button',{name:'@'+bh,exact:true}).click();await expect(page.getByRole('heading',{name:'@'+bh,exact:true})).toBeVisible();await expect(page.locator('main')).toContainText('Community research plan 203');await expect(page.locator('main')).not.toContainText(bob.email);
  await page.getByRole('button',{name:'← Leaderboard',exact:true}).click();
  for(const width of [1440,390,320]){await page.setViewportSize({width,height:1000});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:screenshots+'/leaderboard-'+width+'.png',fullPage:true});}
  await profile(bobPage,bh,false);await page.reload();await expect(page.getByRole('table').getByText('@'+bh,{exact:true})).toHaveCount(0);expect((await request.get('/v1/profiles/'+bh)).status()).toBe(404);
  const origin=new URL(page.url()).origin;const withdrawal=await page.request.post('/v1/me/contributions/'+first.contribution.id+'/withdraw',{headers:{Origin:origin,'X-CSRF-Token':alice.csrf}});expect(withdrawal.status()).toBe(200);await page.getByRole('button',{name:'My page',exact:true}).click();panel=page.getByRole('region',{name:'Membership and contribution points'});await expect(panel.getByTestId('member-points')).toHaveText('20');
  const result=await (await request.get('/v1/leaderboard')).json();const raw=JSON.stringify(result);for(const sentinel of [alice.email,bob.email,alice.id,bob.id,first.template.id])expect(raw).not.toContain(sentinel);
  await page.screenshot({path:screenshots+'/member-mypage.png',fullPage:true});
 }finally{await other.close();}
});
test('LB-19: anonymous direct routes, empty/error recovery and unavailable profile',async({page})=>{
 await page.route('**/v1/leaderboard*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({code:'server_unavailable'})}));
 await page.goto('/#leaderboard');await expect(page.getByRole('alert')).toBeVisible();await page.unroute('**/v1/leaderboard*');await page.getByRole('button',{name:'Retry leaderboard'}).click();await expect(page.getByRole('alert')).toHaveCount(0);await expect(page.getByRole('heading',{name:'Leaderboard.'})).toBeVisible();
 await page.goto('/#profile/not-a-published-member');await expect(page.getByRole('heading',{name:'Profile unavailable.'})).toBeVisible();await page.getByRole('button',{name:'← Leaderboard',exact:true}).click();await expect(page.getByRole('heading',{name:'Leaderboard.'})).toBeVisible();
});
