import {test,expect} from '@playwright/test';

const examples=[
 {kind:'report',name:'Open report example',art:'report-art'},
 {kind:'deck',name:'Open presentation deck example',art:'deck-art'},
 {kind:'worklog',name:'Open worklog example',art:'worklog-art'}
];

test.beforeEach(async({page})=>{
 await page.route('**/v1/**',route=>route.fulfill({status:401,json:{code:'auth_required',message:'Authentication required.'}}));
});

test('public examples load real SVG art and open the matching standalone view',async({page})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/');
 const gallery=page.locator('#document-examples');
 await expect(gallery.getByRole('link')).toHaveCount(3);
 for(const item of examples){
  const link=gallery.getByRole('link',{name:item.name,exact:true});
  await expect(link).toHaveAttribute('href','/examples/document-examples.svg#'+item.kind);
  await expect(link).toHaveAttribute('target','_blank');
  await expect(link).toHaveAttribute('rel',/noopener/);
  const art=link.getByRole('img');
  await expect.poll(()=>art.evaluate(el=>(el as SVGGraphicsElement).getBBox().width)).toBeGreaterThan(500);
  const popupPromise=page.waitForEvent('popup');await link.click();const popup=await popupPromise;
  await popup.waitForLoadState('load');
  expect(new URL(popup.url()).hash).toBe('#'+item.kind);
  await expect(popup.locator('view[id="'+item.kind+'"]')).toHaveCount(1);
  await expect(popup.locator('symbol[id="'+item.art+'"]')).toHaveCount(1);
  await popup.screenshot({path:'test-results/hero-examples/'+item.kind+'-full.svg.png'});
  await popup.close();
 }
 const response=await page.request.get('/examples/document-examples.svg');
 expect(response.status()).toBe(200);expect(response.headers()['content-type']).toContain('image/svg+xml');
 const xml=await response.text();expect(xml).not.toMatch(/<script|<image|https:\/\//i);
 expect(errors).toEqual([]);
 await gallery.screenshot({path:'test-results/hero-examples/gallery-desktop.png'});
});

test('hero keyboard tabs keep the visual, example link and request in sync',async({page})=>{
 let requests=0;page.on('request',request=>{if(request.url().includes('/v1/'))requests++;});
 await page.goto('/');
 const tabs=page.getByRole('tablist',{name:'Document tool examples'});
 const panel=page.getByRole('tabpanel');
 await tabs.getByRole('tab',{name:'Google Docs',exact:true}).focus();
 await tabs.getByRole('tab',{name:'Google Docs',exact:true}).press('ArrowRight');
 await expect(tabs.getByRole('tab',{name:'Google Slides',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(panel.getByRole('link')).toHaveAttribute('href','/examples/document-examples.svg#deck');
 await expect(page.getByLabel('Example request')).toContainText('outline');
 await tabs.getByRole('tab',{name:'Google Slides',exact:true}).press('ArrowRight');
 await expect(tabs.getByRole('tab',{name:'Notion',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(panel.getByRole('link')).toHaveAttribute('href','/examples/document-examples.svg#worklog');
 await expect(page.getByLabel('Example request')).toContainText('Markdown');
 const baseline=requests;
 await tabs.getByRole('tab',{name:'Notion',exact:true}).press('Home');
 await expect(panel.getByRole('link')).toHaveAttribute('href','/examples/document-examples.svg#report');
 expect(requests).toBe(baseline);
 await page.locator('.hero').screenshot({path:'test-results/hero-examples/hero-desktop.png'});
});

test('large previews and actions remain usable across laptop, tablet and mobile sizes',async({page})=>{
 for(const size of [{width:1440,height:614},{width:768,height:1024},{width:390,height:844},{width:320,height:844}]){
  await page.setViewportSize(size);await page.goto('/');
  const primary=page.locator('.hero').getByRole('link',{name:'Let AI write',exact:false});
  await expect(primary).toBeVisible();
  if(size.width===1440)await expect(primary).toBeInViewport();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const gallery=page.locator('#document-examples');
  for(const item of examples){
   const link=gallery.getByRole('link',{name:item.name,exact:true});await link.scrollIntoViewIfNeeded();
   await expect(link).toBeInViewport();
   const box=await link.boundingBox();expect(box!.width).toBeGreaterThan(Math.min(250,size.width-40));
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(size.width===390||size.width===320)await gallery.screenshot({path:'test-results/hero-examples/gallery-'+size.width+'.png'});
  if(size.width===1440)await page.locator('.hero').screenshot({path:'test-results/hero-examples/hero-laptop.png'});
 }
});
