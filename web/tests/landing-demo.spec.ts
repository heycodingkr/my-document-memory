import {test,expect} from '@playwright/test';

async function seek(page:import('@playwright/test').Page,position:'Home'|'End'){
 const progress=page.getByRole('slider',{name:'Demo progress'});
 await progress.focus();await progress.press(position);
}

test('one brief makes three distinct complete drafts and every logo is served locally',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 const writes:string[]=[];page.on('request',r=>{if(!['GET','HEAD'].includes(r.method()))writes.push(r.url());});
 await page.goto('/');
 await page.getByLabel('Example AI',{exact:true}).selectOption('Claude');
 await expect(page.locator('.memory-agent')).toHaveText('Claude');
 await expect(page.locator('.memory-agent img')).toHaveAttribute('src','/brands/claude.ico');
 const demo=page.getByRole('region',{name:'Ask once. Watch it take shape.'});
 await demo.scrollIntoViewIfNeeded();
 const brief=page.getByLabel('Multi-output request',{exact:true});
 await expect(brief).toContainText('10-slide deck in Google Slides');
 await expect(brief).toContainText('one-page summary in Google Docs');
 await expect(brief).toContainText('promotional post about this project for Naver Blog');
 await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Ready for your review');
 const deck=page.getByRole('article',{name:'Google Slides demo: a ten-slide project deck'});
 await expect(deck.getByRole('button',{name:/Preview slide /})).toHaveCount(10);
 await expect(deck).toContainText('10/10 slides');
 await deck.getByRole('button',{name:'Preview slide 2: The blank page is only half the work.'}).click();
 await expect(deck.getByRole('heading',{level:3})).toHaveText('The blank page is only half the work.');
 await deck.getByRole('button',{name:'Preview slide 10: Your next great document starts here.'}).click();
 await expect(deck.getByRole('heading',{level:3})).toHaveText('Your next great document starts here.');
 await expect(page.getByRole('article',{name:'Google Docs demo: a one-page executive summary'})).toContainText('Confirm any missing facts before sharing.');
 await expect(page.getByRole('article',{name:'Naver Blog demo: an unpublished project promotional post'})).toContainText('unpublished draft');
 const sources=await page.locator('img.service-logo').evaluateAll(nodes=>[...new Set(nodes.map(n=>(n as HTMLImageElement).src))]);
 expect(sources.length).toBeGreaterThanOrEqual(8);
 for(const source of sources){
  expect(new URL(source).origin).toBe(new URL(page.url()).origin);
  const result=await page.request.get(source);expect(result.ok(),source).toBe(true);
  expect(result.headers()['content-type']).toMatch(/^image\//);
 }
 expect(writes).toEqual([]);
});

test('timeline has real writing states, pause and replay, and stops out of view',async({page})=>{
 await page.clock.install();await page.goto('/');
 const demo=page.locator('#workflow-demo');
 const progress=page.getByRole('slider',{name:'Demo progress'});
 await page.getByRole('button',{name:'Pause demo',exact:true}).click();
 await seek(page,'Home');
 await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Reading your brief');
 await page.getByRole('button',{name:'Play demo',exact:true}).click();
 await expect(demo).toHaveAttribute('data-playing','true');
 await page.clock.runFor(6500);
 await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Writing three drafts');
 await expect(page.getByRole('article',{name:'Google Slides demo: a ten-slide project deck'})).toContainText('2/10 slides');
 await page.getByRole('button',{name:'Pause demo',exact:true}).click();
 const stopped=await progress.inputValue();await page.clock.runFor(2000);
 await expect(progress).toHaveValue(stopped);
 await page.getByRole('button',{name:'Play demo',exact:true}).click();
 await page.clock.runFor(5000);
 await page.getByRole('button',{name:'Pause demo',exact:true}).click();
 await expect(page.locator('.blog-text')).toBeVisible();
 await expect(page.locator('.summary-text')).toBeVisible();
 await demo.screenshot({path:'test-results/multi-output-writing.png'});
 await page.getByRole('button',{name:'Play demo',exact:true}).click();
 await page.locator('.landing-footer').scrollIntoViewIfNeeded();
 await expect(demo).toHaveAttribute('data-playing','false');
 const offscreen=await progress.inputValue();await page.clock.runFor(1500);
 await expect(progress).toHaveValue(offscreen);
 await demo.scrollIntoViewIfNeeded();
 await expect(demo).toHaveAttribute('data-playing','true');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
 await expect(demo).toHaveAttribute('data-playing','false');
 const hidden=await progress.inputValue();await page.clock.runFor(1000);await expect(progress).toHaveValue(hidden);
 await page.evaluate(()=>{delete (document as Document&{hidden?:boolean}).hidden;document.dispatchEvent(new Event('visibilitychange'));});
 await seek(page,'End');await expect(progress).toHaveValue('22000');
 await page.getByRole('button',{name:'Replay demo',exact:true}).click();
 expect(Number(await progress.inputValue())).toBeLessThan(1000);
});

test('reduced motion opens a complete paused demo and the brief is copied exactly',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(text:string)=>{document.documentElement.dataset.multiOutputBrief=text;}}}));
 await page.goto('/');
 await expect(page.locator('#workflow-demo')).toHaveAttribute('data-reduced-motion','true');
 await expect(page.getByRole('slider',{name:'Demo progress'})).toHaveValue('22000');
 await expect(page.getByRole('button',{name:'Play demo',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Copy multi-output request',exact:true}).click();
 await expect(page.getByText('Brief copied. Paste it into your connected AI.',{exact:true})).toBeVisible();
 expect(await page.locator('html').getAttribute('data-multi-output-brief')).toBe(await page.getByLabel('Multi-output request',{exact:true}).textContent());
});

test('clipboard refusal selects the brief and preserves the complete demo',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied');}}}));
 await page.goto('/');await page.getByRole('button',{name:'Copy multi-output request',exact:true}).click();
 await expect(page.getByText('Select the brief and copy it manually.',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>window.getSelection()?.toString())).toBe(await page.getByLabel('Multi-output request',{exact:true}).textContent());
 await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Ready for your review');
 expect(errors).toEqual([]);
});

test('three writing surfaces and controls fit desktop, mobile and narrow screens',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
 const demo=page.locator('#workflow-demo');
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:1000});await demo.scrollIntoViewIfNeeded();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const boxes=await page.locator('.output-app').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width};}));
  expect(boxes).toHaveLength(3);
  if(width===1440){expect(new Set(boxes.map(b=>b.y)).size).toBe(1);}else{expect(boxes[0].y).toBeLessThan(boxes[1].y);expect(boxes[1].y).toBeLessThan(boxes[2].y);}
  for(const article of await page.locator('.output-app').all()){
   expect(await article.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
  }
  await seek(page,'Home');await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Reading your brief');
  await seek(page,'End');await expect(page.getByLabel('Demo stage',{exact:true})).toHaveText('Ready for your review');
  await demo.screenshot({path:`test-results/multi-output-demo-${width}.png`});
 }
});
