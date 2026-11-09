import {Api} from './api';
export type AdministratorSession={email:string;csrf_token:string;expires_in:number};
export class AdministratorApi extends Api {
 constructor(csrf=''){super('',csrf);}
 configuration(){return this.request<{enabled:boolean}>('/admin/auth/config');}
 sendLink(email:string){return this.request<{accepted:boolean;retry_after:number}>('/admin/auth/email/link',{method:'POST',body:JSON.stringify({email})});}
 consumeLink(token:string){return this.request<AdministratorSession>('/admin/auth/email/consume',{method:'POST',body:JSON.stringify({token})});}
 currentSession(){return this.request<AdministratorSession>('/admin/auth/session');}
 signOut(){return this.request('/admin/auth/logout',{method:'POST'});}
}
