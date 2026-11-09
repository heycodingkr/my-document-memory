import {test,expect} from '@playwright/test';

const token=process.env.DMEM_E2E_TOKEN||'automated-smoke-token-not-production';

test('public introduction explains the workflow before authentication',async({page})=>{
 const apiRequests:string[]=[];
 page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/v1/'))apiRequests.push(request.url());});
 await page.goto('/');
 await expect(page.getByRole('heading',{level:1})).toHaveText('The era of writing documents yourself is ending.');
 await expect(page.getByLabel('Example AI')).toBeVisible();
 await expect(page.getByRole('tablist',{name:'Document tool examples'}).getByRole('tab')).toHaveCount(3);
 await page.getByRole('link',{name:'Let AI write →',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Hand your next document to AI.'})).toBeInViewport();
 await expect(page.getByRole('link',{name:'Explore Arise Browser ↗',exact:true})).toHaveAttribute('href','https://arisebrowser.com/');
 await expect(page.getByRole('link',{name:'Browser connection guide ↗',exact:true})).toHaveAttribute('href','https://arisebrowser.com/blog/connect-ai-agent-to-browser-mcp/');
 expect(apiRequests.map(url=>new URL(url).pathname)).toEqual(['/v1/auth/session']);
});

test('tool and AI choices carry the same document criteria into the copied request',async({page})=>{
 await page.addInitScript(()=>{
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(text:string)=>{
   document.documentElement.dataset.copiedRequest=text;
  }}});
 });
 await page.goto('/');
 const docs=page.getByRole('tab',{name:'Google Docs',exact:true});
 await docs.focus();
 await docs.press('ArrowRight');
 await expect(page.getByRole('tab',{name:'Google Slides',exact:true})).toBeFocused();
 await expect(page.getByRole('tab',{name:'Google Slides',exact:true})).toHaveAttribute('aria-selected','true');
 await page.getByRole('tab',{name:'Google Slides',exact:true}).press('End');
 await expect(page.getByRole('tab',{name:'Notion',exact:true})).toBeFocused();
 await page.getByRole('tab',{name:'Notion',exact:true}).press('Home');
 await expect(docs).toBeFocused();
 await page.getByLabel('Example AI').selectOption('Claude');
 await page.getByRole('tab',{name:'Google Slides',exact:true}).click();
 await expect(page.getByRole('tab',{name:'Google Slides',exact:true})).toHaveAttribute('aria-selected','true');
 const slidesPanel=page.getByRole('tabpanel',{name:'Google Slides',exact:true});
 await expect(slidesPanel).toContainText('Project kickoff deck');
 await expect(slidesPanel.getByRole('link',{name:'Open presentation deck example',exact:true})).toHaveAttribute('href','/examples/document-examples.svg#deck');
 const prompt=page.getByLabel('Example request');
 await expect(prompt).toContainText('Google Slides');
 await expect(prompt).toContainText('outline first');
 await expect(page.getByText('Claude can start with this request.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Copy request',exact:true}).click();
 await expect(page.getByRole('status')).toHaveText('Request copied. Paste it into your connected AI.');
 expect(await page.locator('html').getAttribute('data-copied-request')).toBe(await prompt.textContent());
 await page.getByRole('tab',{name:'Notion',exact:true}).click();
 await expect(prompt).toContainText('Notion');
 await expect(prompt).toContainText('needs confirmation');
 await expect(page.getByRole('status')).toBeEmpty();
});

test('blocked clipboard offers a manual alternative without losing the request',async({page})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Clipboard denied');}}});
 });
 await page.goto('/');
 await page.getByRole('button',{name:'Copy request',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('copy it manually.');
 await expect(page.getByLabel('Example request')).toContainText('templates and references');
 expect(errors).toEqual([]);
});

test('connection errors recover and the guide preserves an unsaved document',async({page})=>{
 await page.goto('/');
 const input=page.getByLabel('Library connection token');
 await input.fill('incorrect-token-for-onboarding');
 await page.getByRole('button',{name:'Open library'}).click();
 await expect(page.getByRole('alert')).toBeVisible();
 await expect(input).toHaveValue('incorrect-token-for-onboarding');
 await input.fill(token);
 await page.getByRole('button',{name:'Open library'}).click();
 await expect(page.getByRole('heading',{name:'Template library.'})).toBeVisible();
 await page.locator('.template-card').filter({hasText:'Public template'}).getByRole('button',{name:'Meeting Notes and Action Items preview'}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Use this template'}).click();
 await page.getByLabel('Document title',{exact:true}).fill('Unsaved guide-return demo');
 await page.getByRole('button',{name:'Getting started',exact:true}).click();
 await expect(page.getByRole('heading',{level:1})).toBeVisible();
 await expect(page.getByLabel('Library connection token')).toHaveCount(0);
 await page.getByRole('button',{name:'My space',exact:true}).click();
 await expect(page.getByLabel('Document title',{exact:true})).toHaveValue('Unsaved guide-return demo');
 await expect(page.getByRole('button',{name:'Save',exact:true})).toBeEnabled();
});

test('introduction and connection remain usable at desktop and narrow widths',async({page})=>{
 await page.goto('/');
 await page.screenshot({path:'test-results/landing-desktop.png',fullPage:true});
 await page.setViewportSize({width:1440,height:614});
 await expect(page.getByRole('link',{name:'Let AI write →',exact:true})).toBeInViewport({ratio:1});
 await page.screenshot({path:'test-results/landing-laptop.png'});
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  for(const tool of ['Google Docs','Google Slides','Notion']){
   await page.getByRole('tab',{name:tool,exact:true}).click();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  }
  await page.getByText('Local setup and AI connection',{exact:true}).click();
  await expect(page.getByText('node scripts/dev.mjs',{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.getByText('Local setup and AI connection',{exact:true}).click();
  await page.getByRole('link',{name:'Connect my library →',exact:true}).click();
  await page.getByLabel('Library connection token').fill('mobile-layout-example-token');
  await expect(page.getByRole('button',{name:'Open library'})).toBeInViewport();
  await page.screenshot({path:`test-results/landing-mobile-${width}.png`,fullPage:true});
 }
});
