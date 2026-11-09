import {test,expect} from '@playwright/test';
import {existsSync,readFileSync} from 'node:fs';
import {requestAdministratorLink} from './helpers/administrator';
const mailbox=process.env.DMEM_E2E_MAILBOX;
const screenshots=process.env.DMEM_E2E_OUTPUT_DIR||'test-results';
test.skip(!mailbox,'Requires the isolated email fixture');
test('ADMIN-UI-01: contribution review offers authorized email sign-in',async({page})=>{
 await page.goto('/#review');
 await expect(page.getByLabel('Administrator email',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Send administrator link',exact:true})).toBeEnabled();
 await expect(page.getByLabel('Administrator token',{exact:true})).toHaveCount(0);
 await page.screenshot({path:screenshots+'/administrator-email-login.png'});
});
test('ADMIN-UI-02: unauthorized email sees the generic response without receiving mail',async({page})=>{
 const before=existsSync(mailbox!)?readFileSync(mailbox!,'utf8'):'';
 await page.goto('/#review');await page.getByLabel('Administrator email',{exact:true}).fill('not-a-reviewer@example.test');
 await page.getByRole('button',{name:'Send administrator link',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('If this email is authorized');
 expect(existsSync(mailbox!)?readFileSync(mailbox!,'utf8'):'').toBe(before);
 expect((await page.request.get('/v1/admin/contributions')).status()).toBe(401);
});
test('ADMIN-UI-03: explicit cross-browser confirmation, persistent session, logout and replay rejection',async({page,browser,baseURL})=>{
 const url=await requestAdministratorLink(page,'reviewer-cross@example.test');
 const token=new URL(url).hash.slice('#admin-sign-in='.length);
 const other=await browser.newContext({baseURL});
 try{
  const target=await other.newPage();const errors:string[]=[];target.on('pageerror',error=>errors.push(error.message));
  await target.goto(url);await expect(target).toHaveURL(/\/#review$/);
  await expect(target.getByRole('button',{name:'Continue as administrator',exact:true})).toBeVisible();
  expect((await target.request.get('/v1/admin/auth/session')).status()).toBe(401);
  await target.getByRole('button',{name:'Continue as administrator',exact:true}).click();
  const lock=target.getByRole('button',{name:'Sign out and lock queue',exact:true});await expect(lock).toBeVisible();
  expect((await target.request.get('/v1/admin/contributions')).status()).toBe(200);
  expect((await target.request.get('/v1/auth/session')).status()).toBe(401);
  const storage=await target.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}));
  expect(storage).not.toContain(token);expect(storage).not.toContain('synthetic-e2e-admin-token');
  const cookies=await other.cookies();expect(cookies.find(cookie=>cookie.name==='dmem_admin_session')?.httpOnly).toBe(true);
  await target.reload();await expect(lock).toBeVisible();
  await target.screenshot({path:screenshots+'/administrator-session-review.png'});
  await lock.click();await expect(target.getByLabel('Administrator email',{exact:true})).toBeVisible();
  expect((await target.request.get('/v1/admin/contributions')).status()).toBe(401);
  await target.goto(url);await target.getByRole('button',{name:'Continue as administrator',exact:true}).click();
  await expect(target.getByRole('alert')).toContainText('already used');
  expect((await target.request.get('/v1/admin/auth/session')).status()).toBe(401);expect(errors).toEqual([]);
 }finally{await other.close();}
});
