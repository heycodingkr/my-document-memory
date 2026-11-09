import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';

const mailbox=process.env.DMEM_E2E_MAILBOX;
test.skip(!mailbox,'Requires isolated synthetic email fixture: python3 tests/smoke/accounts-v1.py');

async function signIn(page:Page){
 const email='sidebar-'+Date.now().toString(36)+'@example.test';
 await page.goto('/#me');
 await page.getByLabel('Email address',{exact:true}).fill(email);
 await page.getByRole('button',{name:'Send sign-in link',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('Check your inbox.');
 await expect.poll(()=>{try{return JSON.parse(readFileSync(mailbox!,'utf8')).email;}catch{return '';}}).toBe(email);
 await page.goto(JSON.parse(readFileSync(mailbox!,'utf8')).url);
 await page.getByRole('button',{name:'Continue to my space',exact:true}).click();
 await expect(page.getByRole('heading',{name:'My page.',exact:true})).toBeVisible();
}

for(const viewport of [{width:1416,height:614},{width:1024,height:500},{width:720,height:614},{width:701,height:500}]){
 test('BUG-398-DESKTOP: sidebar actions remain reachable at '+viewport.width+'×'+viewport.height,async({page},testInfo)=>{
  await page.setViewportSize(viewport);
  await signIn(page);
  const sidebar=page.locator('.sidebar');
  const guide=page.getByRole('button',{name:'Getting started',exact:true});
  await sidebar.hover({position:{x:80,y:180}});
  await page.mouse.wheel(0,2000);
  await expect(guide).toBeInViewport({ratio:1});
  expect(await sidebar.evaluate(el=>el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(viewport.height+1);
  await page.screenshot({path:testInfo.outputPath('sidebar-short-desktop.png')});
  await testInfo.attach('layout.json',{body:JSON.stringify(await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:Array.from(document.querySelectorAll('body *')).filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>({tag:el.tagName,class:el.className,right:el.getBoundingClientRect().right})).slice(0,20)}))),contentType:'application/json'});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const signOut=page.getByRole('button',{name:'Sign out',exact:true});
  await expect(signOut).toHaveCount(1);
  await expect(signOut).toBeInViewport({ratio:1});
  await guide.click();
  await expect(page.locator('.landing')).toBeVisible();
  await page.getByRole('button',{name:'My space',exact:true}).click();
  await expect(page.getByRole('heading',{name:'My page.',exact:true})).toBeVisible();
  await sidebar.hover({position:{x:80,y:180}});
  await page.mouse.wheel(0,2000);
  await expect(signOut).toBeInViewport({ratio:1});
  await signOut.click();
  await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
  expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 });
}

for(const viewport of [{width:700,height:844},{width:390,height:844}]){
 test('BUG-398-MOBILE: mobile sign out remains reachable at '+viewport.width+'×'+viewport.height,async({page},testInfo)=>{
  await page.setViewportSize(viewport);
  await signIn(page);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const signOut=page.getByRole('button',{name:'Sign out',exact:true});
  await expect(signOut).toHaveCount(1);
  await expect(signOut).toBeInViewport({ratio:1});
  await page.screenshot({path:testInfo.outputPath('sidebar-mobile.png')});
  await signOut.click();
  await expect(page.getByLabel('Email address',{exact:true})).toBeVisible();
  expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 });
}
