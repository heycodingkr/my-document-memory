import {expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
export async function requestAdministratorLink(page:Page,email:string){
 await page.goto('/#review');
 await page.getByLabel('Administrator email',{exact:true}).fill(email);
 await page.getByRole('button',{name:'Send administrator link',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('If this email is authorized');
 await expect.poll(()=>{try{return JSON.parse(readFileSync(process.env.DMEM_E2E_MAILBOX!,'utf8')).email;}catch{return '';}}).toBe(email);
 return JSON.parse(readFileSync(process.env.DMEM_E2E_MAILBOX!,'utf8')).url as string;
}
export async function signInAdministrator(page:Page,email:string){
 const url=await requestAdministratorLink(page,email);await page.goto(url);
 await expect(page).toHaveURL(/\/#review$/);
 await page.getByRole('button',{name:'Continue as administrator',exact:true}).click();
 await expect(page.getByRole('button',{name:'Sign out and lock queue',exact:true})).toBeVisible();
 return url;
}
