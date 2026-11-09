import {test,expect} from '@playwright/test';
const screenshots=process.env.DMEM_E2E_OUTPUT_DIR||'test-results';
test.use({locale:'ko-KR'});

test('English landing exposes GitHub, browser downloads and all agent connection paths',async({page})=>{
 await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('lang','en');
 const nav=page.getByRole('navigation',{name:'Product guide'});
 await expect(nav.getByRole('link',{name:'GitHub',exact:true})).toBeVisible();
 await expect(nav.getByRole('link',{name:'GitHub',exact:true})).toHaveAttribute('href','https://github.com/heycodingkr/my-document-memory');
 await nav.getByRole('link',{name:'How it works',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Choose the context. Let your AI write.'})).toBeInViewport();
 await expect(page.getByRole('link',{name:'Download Arise Browser',exact:true})).toHaveAttribute('href','https://arisebrowser.com/#download');
 await expect(page.getByRole('link',{name:'Download Chrome',exact:true})).toHaveAttribute('href','https://www.google.com/chrome/');
 await nav.getByRole('link',{name:'Connect your agent',exact:true}).click();
 const tabs=page.getByRole('tablist',{name:'Connection methods'});
 for(const name of ['Web app','CLI','MCP']){
  await tabs.getByRole('tab',{name,exact:true}).click();
  await expect(tabs.getByRole('tab',{name,exact:true})).toHaveAttribute('aria-selected','true');
 }
 await expect(page.getByLabel('MCP configuration',{exact:true})).toContainText('dmem-mcp');
 await expect(page.getByLabel('MCP configuration',{exact:true})).not.toContainText('https://mydocumentmemory.com/mcp');
 await page.goto('/');
 // The language switch intentionally uses the destination language's name.
 expect((await page.locator('.landing main, .landing-footer').allInnerTexts()).join('\n')).not.toMatch(/[가-힣]/);
 await page.screenshot({path:screenshots+'/landing-english-desktop.png',fullPage:true});
 await page.screenshot({path:screenshots+'/landing-hero-desktop.png'});
 await page.locator('#how-it-works').screenshot({path:screenshots+'/landing-how-it-works.png'});
 await page.locator('#connect-agent').screenshot({path:screenshots+'/landing-connect-agent.png'});
});

test('About link explains the product and fits narrow screens',async({page})=>{
 await page.goto('/');
 const nav=page.getByRole('navigation',{name:'Product guide'});
 const aboutLink=nav.getByRole('link',{name:'About',exact:true});
 await expect(aboutLink).toHaveAttribute('href','#about');
 await aboutLink.click();
 await expect(page).toHaveURL(/#about$/);
 const about=page.locator('#about');
 await expect(about.getByRole('heading',{name:'Your work is done. Why are you still writing about it?'})).toBeInViewport();
 await expect(about).toContainText('templates, writing guidance, review criteria, and selected references');
 for(const heading of ['Keep your format across platforms and models.','Help lower-cost models write better.','Review and decide.']){
  await expect(about.getByRole('heading',{name:heading,exact:true})).toBeVisible();
 }
 await expect(about).toContainText('Your memories stay private unless you choose to share them.');
 await page.setViewportSize({width:320,height:844});
 await expect(aboutLink).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('connection examples copy exactly and remain usable on narrow screens',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(value:string)=>{document.documentElement.dataset.setupCopy=value;}}}));
 await page.goto('/');
 const tabs=page.getByRole('tablist',{name:'Connection methods'});
 for(const name of ['CLI','MCP']){
  await tabs.getByRole('tab',{name,exact:true}).click();
  const example=page.getByLabel(name==='MCP'?'MCP configuration':'CLI commands',{exact:true});
  await page.getByRole('button',{name:name==='MCP'?'Copy MCP configuration':'Copy setup commands',exact:true}).click();
  expect(await page.locator('html').getAttribute('data-setup-copy')).toBe(await example.textContent());
 }
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  await expect(page.getByRole('navigation',{name:'Product guide'}).getByRole('link',{name:'GitHub',exact:true})).toBeVisible();
  for(const name of ['Web app','CLI','MCP']){
   await tabs.getByRole('tab',{name,exact:true}).click();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.screenshot({path:screenshots+`/landing-english-mobile-${width}.png`,fullPage:true});
  await page.goto('/');await page.screenshot({path:screenshots+`/landing-hero-mobile-${width}.png`});
 }
});

test('email sign-in offers a link instead of requiring a verification code',async({page})=>{
 await page.route('**/v1/auth/config',route=>route.fulfill({json:{email_enabled:true}}));
 await page.goto('/#me');
 await expect(page.getByRole('button',{name:'Send sign-in link',exact:true})).toBeVisible();
 await expect(page.getByText('Sign in with the link sent to your email.',{exact:false})).toBeVisible();
});
