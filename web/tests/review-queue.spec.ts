import {test,expect} from '@playwright/test';
import {execFileSync,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {signInAdministrator} from './helpers/administrator';

test.skip(!process.env.DMEM_E2E_DATABASE||!process.env.DMEM_E2E_MAILBOX,'Requires isolated accounts_fixture database and synthetic mailbox');
type Row={id:string;title:string;status:string};

test('QP-06/07: real CLI and browser reach older pending contributions across pages',async({page,baseURL})=>{
 test.setTimeout(60000);
 const fixture=JSON.parse(execFileSync('python3',[
  fileURLToPath(new URL('../../tests/smoke/review-queue-fixture.py',import.meta.url)),
  '--database',process.env.DMEM_E2E_DATABASE!,'--base',baseURL!
 ],{encoding:'utf8'})) as {pending:Row[];rejected:Row[];all:Row[]};
 const cli=fileURLToPath(new URL('../../target/debug/dmem',import.meta.url));
 const env={...process.env,DMEM_URL:baseURL!,DMEM_ORIGIN:baseURL!,DMEM_TOKEN:'',DMEM_ADMIN_TOKEN:'synthetic-e2e-admin-token-at-least-32-characters'};
 const invoke=(args:string[])=>JSON.parse(execFileSync(cli,['review-queue',...args],{env,encoding:'utf8'}));
 for(const flags of [['--status','unknown'],['--limit','0'],['--limit','101']]){
  const invalid=spawnSync(cli,['review-queue',...flags],{env,encoding:'utf8'});
  expect(invalid.status).toBe(2);expect(invalid.stdout).toBe('');
 }
 expect(invoke([]).items.map((r:Row)=>r.id)).toEqual(fixture.all.slice(0,100).map(r=>r.id));
 const cliIds:string[]=[];let cursor:string|null=null;let pages=0;
 do{
  const result=invoke(['--status','pending','--limit','37',...(cursor?['--cursor',cursor]:[])]);
  expect(result.items.length).toBeLessThanOrEqual(37);
  cliIds.push(...result.items.map((r:Row)=>r.id));cursor=result.next_cursor;
  expect(++pages).toBeLessThan(10);
 }while(cursor);
 expect(cliIds).toEqual(fixture.pending.map(r=>r.id));

 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await signInAdministrator(page,'reviewer-queue@example.test');
 const queue=page.getByRole('region',{name:'Contribution queue',exact:true});
 const items=queue.locator('.queue-item');
 const titles=()=>items.evaluateAll(nodes=>nodes.map(n=>n.getAttribute('aria-label')!.slice(7)));
 const expectPage=async(rows:Row[],count:number)=>{
  await expect(items).toHaveCount(count);
  expect(await titles()).toEqual(rows.slice(0,count).map(r=>r.title));
 };
 await expect(page.getByLabel('Show submissions')).toHaveValue('pending');
 await expectPage(fixture.pending,100);
 const oldest=fixture.pending.at(-1)!;
 await expect(page.getByRole('button',{name:'Review '+oldest.title,exact:true})).toHaveCount(0);
 await queue.getByRole('button',{name:'Load more submissions',exact:true}).click();
 await expectPage(fixture.pending,fixture.pending.length);
 await expect(queue.getByRole('button',{name:'Load more submissions',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Review '+oldest.title,exact:true}).click();
 await expect(page.getByRole('heading',{name:oldest.title,exact:true})).toBeVisible();
 await expect(page.getByLabel('Review stages').locator('li')).toHaveCount(6);
 await page.getByLabel('I reviewed the snapshot and findings.').check();

 await page.getByLabel('Show submissions').selectOption('rejected');
 await expectPage(fixture.rejected,100);
 await expect(page.getByRole('heading',{name:oldest.title,exact:true})).toHaveCount(0);
 await queue.getByRole('button',{name:'Load more submissions',exact:true}).click();
 await expectPage(fixture.rejected,fixture.rejected.length);
 await page.getByLabel('Show submissions').selectOption('all');
 await expectPage(fixture.all,100);
 await page.getByLabel('Show submissions').selectOption('pending');
 await expectPage(fixture.pending,100);
 await queue.getByRole('button',{name:'Load more submissions',exact:true}).click();
 await expectPage(fixture.pending,fixture.pending.length);
 await page.getByRole('button',{name:'Refresh queue',exact:true}).click();
 await expectPage(fixture.pending,100);
 await page.reload();
 await expect(page.getByRole('button',{name:'Sign out and lock queue',exact:true})).toBeVisible();
 await expectPage(fixture.pending,100);

 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:(process.env.DMEM_E2E_OUTPUT_DIR||'test-results')+'/review-queue-mobile.png'});
 await page.getByRole('button',{name:'Sign out and lock queue',exact:true}).click();
 await expect(page.getByLabel('Administrator email',{exact:true})).toHaveValue('');
 await expect(items).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Load more submissions',exact:true})).toHaveCount(0);
 expect(errors).toEqual([]);
});
