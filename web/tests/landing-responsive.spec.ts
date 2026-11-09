import {test,expect} from '@playwright/test';

test.use({reducedMotion:'reduce'});

test.beforeEach(async({page})=>{
 await page.route('**/v1/auth/session',route=>route.fulfill({status:401,json:{code:'auth_required',message:'Authentication required.'}}));
});

for(const locale of ['en','ko']){
 test(`responsive navigation is readable and reachable in ${locale}`,async({page})=>{
  await page.goto('/');
  if(locale==='ko')await page.getByRole('button',{name:'Switch to Korean'}).click();
  for(const width of [320,390,600,601,768,1024,1280,1440]){
   await page.setViewportSize({width,height:900});
   const menu=page.locator('#landing-menu-toggle');
   if(await menu.isVisible()&&await menu.getAttribute('aria-expanded')==='false')await menu.click();
   const actions=page.locator('.landing-links>a, .nav-actions>button, .header-controls>button:visible');
   for(const action of await actions.all()){
    await expect(action).toBeVisible();
    const box=await action.boundingBox();
    expect(box!.height,`${await action.innerText()} at ${width}px`).toBeGreaterThanOrEqual(44);
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x+box!.width).toBeLessThanOrEqual(width+1);
   }
   const boxes=await actions.evaluateAll(nodes=>nodes.map(el=>{
    const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,text:el.textContent};
   }));
   for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
    const a=boxes[i],b=boxes[j];
    const overlap=Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
    expect(overlap,`${a.text} overlaps ${b.text} at ${width}px`).toBe(false);
   }
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
 });

 test(`supporting prose and captions remain legible in ${locale}`,async({page})=>{
  await page.goto('/');
  if(locale==='ko')await page.getByRole('button',{name:'Switch to Korean'}).click();
  for(const width of [390,1440]){
   await page.setViewportSize({width,height:900});
   const metrics=await page.evaluate(()=>{
    const luminance=(rgb:number[])=>rgb.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
    const rgb=(color:string)=>(color.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
    return [...document.querySelectorAll('.hero-description,.hero-detail,.section-heading>p,.about-story,.about-values p,.how-steps p,.steps p,.browser-copy>p,.savings-note,.examples-note,.example-disclosure,.example-caption,.principles dd,.scope-note')].map(el=>{
     const style=getComputedStyle(el);let parent:Element|null=el,bg='';
     while(parent){bg=getComputedStyle(parent).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent')break;parent=parent.parentElement;}
     const foreground=luminance(rgb(style.color)),background=luminance(rgb(bg));
     return {className:el.className,font:parseFloat(style.fontSize),lineHeight:parseFloat(style.lineHeight)/parseFloat(style.fontSize),contrast:(Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05)};
    });
   });
   for(const metric of metrics){
    const caption=/note|disclosure|caption/.test(metric.className);
    expect(metric.font,`${metric.className} at ${width}px`).toBeGreaterThanOrEqual(metric.className.includes('hero-description')?16:caption?12:14);
    expect(metric.lineHeight,metric.className).toBeGreaterThanOrEqual(1.65);
    expect(metric.contrast,metric.className).toBeGreaterThanOrEqual(4.5);
   }
  }
 });

 test(`primary action stays in the first laptop and phone viewport in ${locale}`,async({page})=>{
  await page.goto('/');
  if(locale==='ko')await page.getByRole('button',{name:'Switch to Korean'}).click();
  for(const size of [{width:1440,height:614},{width:390,height:844}]){
   await page.setViewportSize(size);
   await page.evaluate(()=>scrollTo(0,0));
   await expect(page.locator('.hero-actions .action-primary')).toBeInViewport({ratio:1});
  }
 });
}

test('skip link moves keyboard focus into the page content',async({page})=>{
 await page.goto('/');
 await page.keyboard.press('Tab');
 await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
 await page.keyboard.press('Enter');
 await expect(page.locator('main#intro')).toBeFocused();
});

test('mobile menu opens with the keyboard, closes on Escape and follows section links',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 const menu=page.getByRole('button',{name:'Menu',exact:true});
 const guide=page.getByRole('navigation',{name:'Product guide'});
 await expect(menu).toHaveAttribute('aria-expanded','false');
 await expect(guide).toBeHidden();
 await expect(page.getByRole('button',{name:'Switch to Korean'})).toBeVisible();
 await menu.focus();await menu.press('Enter');
 await expect(guide).toBeVisible();
 await page.keyboard.press('Tab');
 await expect(guide.getByRole('link',{name:'About',exact:true})).toBeFocused();
 await page.keyboard.press('Escape');
 await expect(guide).toBeHidden();await expect(menu).toBeFocused();
 await menu.click();await guide.getByRole('link',{name:'Examples',exact:true}).click();
 await expect(page).toHaveURL(/#document-examples$/);
 await expect(guide).toBeHidden();
 await expect(page.locator('#document-examples-title')).toBeInViewport();
 await page.setViewportSize({width:1440,height:900});
 await expect(guide).toBeVisible();await expect(menu).toBeHidden();
});
