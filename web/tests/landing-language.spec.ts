import {test,expect} from '@playwright/test';

test.use({locale:'ko-KR',reducedMotion:'reduce'});

test.beforeEach(async({page})=>{
 await page.goto('/');
});

test('LANG-01: English is the initial language even for Korean browser locales',async({page})=>{
 await expect(page.locator('html')).toHaveAttribute('lang','en');
 await expect(page).toHaveTitle('My Document Memory — Let AI do the writing.');
 await expect(page.getByRole('heading',{name:'The era of writing documents yourself is ending.'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Switch to Korean'})).toBeVisible();
});

test('LANG-02: Korean selection translates the landing and nested examples',async({page})=>{
 await page.getByRole('button',{name:'Switch to Korean'}).click();
 await expect(page.locator('html')).toHaveAttribute('lang','ko');
 await expect(page).toHaveTitle('My Document Memory — 문서 작성은 AI에게.');
 await expect(page.locator('meta[name="description"]')).toHaveAttribute('content',/문서를 사람이 쓰던 시대는 끝나갑니다/);
 await expect(page.getByRole('button',{name:'영어로 변경'})).toBeVisible();
 await expect(page.getByRole('navigation',{name:'제품 안내'}).getByRole('link',{name:'소개',exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'문서를 사람이 쓰던 시대는 끝나갑니다.'})).toBeVisible();
 await expect(page.locator('.hero-output-title')).toContainText('주간 제품 보고서');
 await expect(page.getByRole('heading',{name:'한 번 요청하고, 세 곳에서 결과를 확인하세요.'})).toBeVisible();
 await expect(page.getByLabel('여러 결과물 요청',{exact:true})).toContainText('Google Slides');
 await expect(page.locator('#connect-agent').getByRole('heading',{name:'에이전트를 연결하고 문서 메모리를 이어 쓰세요.'})).toBeVisible();
 await expect(page.getByRole('tablist',{name:'연결 방법'}).getByRole('tab',{name:'웹 앱'})).toBeVisible();
});

test('LANG-03: the language choice survives reload and can be changed back',async({page})=>{
 await page.getByRole('button',{name:'Switch to Korean'}).click();
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('lang','ko');
 expect(await page.evaluate(()=>localStorage.getItem('dmem.landing-locale'))).toBe('ko');
 await page.getByRole('button',{name:'영어로 변경'}).click();
 await expect(page.locator('html')).toHaveAttribute('lang','en');
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('lang','en');
 expect(await page.evaluate(()=>localStorage.getItem('dmem.landing-locale'))).toBe('en');
 await expect(page.getByRole('heading',{name:'The era of writing documents yourself is ending.'})).toBeVisible();
});

test('LANG-04: the language switch stays usable at 320px in both languages',async({page})=>{
 await page.setViewportSize({width:320,height:844});
 const languageButton=page.getByRole('button',{name:'Switch to Korean'});
 await expect(languageButton).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await languageButton.click();
 await expect(page.getByRole('button',{name:'영어로 변경'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('LANG-05: Korean setup controls copy CLI commands with real line breaks',async({page})=>{
 await page.context().grantPermissions(['clipboard-read','clipboard-write'],{origin:new URL(page.url()).origin});
 await page.getByRole('button',{name:'Switch to Korean'}).click();
 await page.getByRole('tab',{name:'CLI'}).click();
 await page.getByRole('button',{name:'설정 명령 복사'}).click();
 await expect(page.locator('.setup-copy-status')).toHaveText('명령을 복사했습니다.');
 const copied=await page.evaluate(()=>navigator.clipboard.readText());
 expect(copied.split('\n')).toEqual([
  'cargo install --path crates/dmem-cli --locked --debug',
  'set -a',
  '. ./.env',
  'set +a',
  'export DMEM_URL=http://127.0.0.1:3847',
  'dmem status',
  'dmem templates Meeting'
 ]);
});
