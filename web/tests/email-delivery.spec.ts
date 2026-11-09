import {test,expect} from '@playwright/test';

// Opt-in provider simulation; never sends to a person's inbox.
test.skip(process.env.DMEM_LIVE_EMAIL_TEST!=='1','Requires explicit live Resend test opt-in.');
test('live Resend accepts a sign-in link through the public Svelte form',async({page})=>{
 await page.goto('/#me');
 expect(new URL(page.url()).origin).toBe('https://mydocumentmemory.com');
 const email=`delivered+dmem-${Date.now()}@resend.dev`;
 await page.getByLabel('Email address',{exact:true}).fill(email);
 const accepted=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/auth/email/link'&&response.request().method()==='POST');
 await page.getByRole('button',{name:'Send sign-in link',exact:true}).click();
 const result=await accepted;
 expect(result.status()).toBe(202);
 expect(await result.json()).toMatchObject({sent:true,expires_in:600,retry_after:60});
 await expect(page.getByRole('status')).toContainText('Check your inbox.');
 expect((await page.request.get('/v1/auth/session')).status()).toBe(401);
 await page.screenshot({path:(process.env.DMEM_E2E_OUTPUT_DIR||'test-results')+'/live-resend-link-request.png'});
});
