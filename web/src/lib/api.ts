import type {Template,Source,Document,List,Content,Session,Contribution,ContributionPage,ContributionQueueStatus,Dashboard,ReviewReport,MemberProfile,LeaderboardData,PublicMemberProfile} from './types';
import type {WebPreview,WebImportRequest,WebImportResult,WebOrigin,WebSearchHit} from './web-memory';
const messages:Record<string,string>={
 auth_required:'Your session expired or the credentials are invalid. Sign in again.',rate_limited:'Too many requests. Try again shortly.',not_found:'This item is unavailable or you do not have access.',
 handle_unavailable:'This handle is reserved or already taken. Choose another one.',
 search_unavailable:'Web search is not configured. Paste a public document URL below.',
 fetch_blocked:'This page cannot be imported. Try a public HTTPS URL, upload the file, or clip your owned browser tab.',
 fetch_failed:'The remote page could not be read. Check the URL and try again.',
 license_forbids:'The source license does not permit that copy or publication.',
 invalid_input:'Check the title, required fields, and input limits.',invalid_form:'Check that the document type matches the file format.',
 version_conflict:'A newer version was saved elsewhere. Your current edits are preserved.',
 payload_too_large:'Files must be at most 10 MiB and extracted text at most 1 MiB.',
 review_blocked:'This submission needs changes before it can be approved. Read the review findings.',
 unsupported_format:'This format is not supported yet.',extract_empty:'No text was found. Scanned files need text recognition.',
 request_timed_out:'The server took too long to respond. Please try again.',
 server_unavailable:'Cannot connect to the server. Check that it is running.',internal:'The library operation failed. Try again shortly.'
};
export class ApiFailure extends Error{
 constructor(public code:string){super(messages[code]??'The request could not be completed.');}
}
export class Api{
 constructor(private token='',private csrf=''){}
 private headers():Record<string,string>{return this.token?{Authorization:'Bearer '+this.token}:{'X-CSRF-Token':this.csrf};}
 async request<T>(path:string,options:RequestInit={}):Promise<T>{
 let response:Response;
 try{response=await fetch('/v1'+path,{...options,credentials:'same-origin',headers:{...this.headers(),...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...options.headers}});}catch{throw new ApiFailure('server_unavailable');}
 if(!response.ok){const error=await response.json().catch(()=>({code:'internal'}));throw new ApiFailure(typeof error.code==='string'?error.code:'internal');}
 return response.json();
 }
 private async readWithTimeout<T>(path:string):Promise<T>{
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),10_000);
  try{return await this.request<T>(path,{signal:controller.signal});}
  catch(e){if(controller.signal.aborted)throw new ApiFailure('request_timed_out');throw e;}
  finally{clearTimeout(timeout);}
 }
 status(){return this.request('/status');}
 webSearch(query:string,locale:string){return this.request<{items:WebSearchHit[];untrusted:true}>('/web/search',{method:'POST',body:JSON.stringify({query,locale,limit:5})});}
 webPreview(url:string){return this.request<WebPreview>('/web/preview',{method:'POST',body:JSON.stringify({url})});}
 webImport(input:WebImportRequest){return this.request<WebImportResult>('/web/import',{method:'POST',body:JSON.stringify(input)});}
 webOrigin(id:string){return this.request<WebOrigin>('/web/origins/'+encodeURIComponent(id));}
 authConfig(){return this.request<{email_enabled:boolean}>('/auth/config');}
 session(){return this.readWithTimeout<Session>('/auth/session');}
 startEmail(email:string){return this.request<{retry_after:number}>('/auth/email/start',{method:'POST',body:JSON.stringify({email})});}
 verifyEmail(code:string){return this.request<Session>('/auth/email/verify',{method:'POST',body:JSON.stringify({code})});}
 startEmailLink(email:string){return this.request<{retry_after:number}>('/auth/email/link',{method:'POST',body:JSON.stringify({email})});}
 consumeEmailLink(token:string){return this.request<Session>('/auth/email/consume',{method:'POST',body:JSON.stringify({token})});}
 logout(){return this.request('/auth/logout',{method:'POST'});}
 publicTemplates(q='',locale='en-US'){const params=new URLSearchParams({q});if(locale!=='all')params.set('locale',locale);return this.request<List<Template>>('/public/templates?'+params);}
 profile(){return this.request<MemberProfile>('/me/profile');}
 saveProfile(handle:string|null,public_profile:boolean){return this.request<MemberProfile>('/me/profile',{method:'PUT',body:JSON.stringify({handle,public_profile})});}
 leaderboard(offset=0){return this.readWithTimeout<LeaderboardData>('/leaderboard?offset='+offset);}
 publicProfile(handle:string){return this.request<PublicMemberProfile>('/profiles/'+encodeURIComponent(handle));}
 dashboard(){return this.request<Dashboard>('/me');}
 contributions(){return this.request<List<Contribution>>('/me/contributions');}
 contributionReview(id:string){return this.request<ReviewReport>('/me/contributions/'+encodeURIComponent(id)+'/review');}
 reviewQueue(status:ContributionQueueStatus='all',cursor?:string,limit=100){const query=new URLSearchParams({status,limit:String(limit)});if(cursor)query.set('cursor',cursor);return this.request<ContributionPage>('/admin/contributions?'+query);}
 review(id:string){return this.request<ReviewReport>('/admin/contributions/'+encodeURIComponent(id)+'/review');}
 decide(id:string,decision:'approve'|'reject'){return this.request<Contribution>('/admin/contributions/'+encodeURIComponent(id)+'/decision',{method:'POST',body:JSON.stringify({decision})});}
 contribute(template_id:string,author:string,license:string,rights_confirmed:boolean){return this.request<Contribution>('/me/contributions',{method:'POST',body:JSON.stringify({template_id,author,license,rights_confirmed})});}
 withdraw(id:string){return this.request<Contribution>('/me/contributions/'+encodeURIComponent(id)+'/withdraw',{method:'POST'});}
 templates(q='',family='all',visibility='all',locale='all'){const params=new URLSearchParams({q});if(family!=='all')params.set('family',family);if(visibility!=='all')params.set('visibility',visibility);if(locale!=='all')params.set('locale',locale);return this.request<List<Template>>('/templates?'+params);}
 sources(q=''){return this.request<List<Source>>('/sources?q='+encodeURIComponent(q));}
 documents(q=''){return this.request<List<Document>>('/documents?q='+encodeURIComponent(q));}
 source(id:string){return this.request<Source>('/sources/'+encodeURIComponent(id));}
 document(id:string){return this.request<Document>('/documents/'+encodeURIComponent(id));}
 copy(id:string){return this.request<Template>('/templates/'+encodeURIComponent(id)+'/copy',{method:'POST'});}
 fromSource(id:string){return this.request<Template>('/sources/'+encodeURIComponent(id)+'/template',{method:'POST'});}
 createTemplate(input:unknown){return this.request<Template>('/templates',{method:'POST',body:JSON.stringify(input)});}
 create(title:string,template_id:string,source_ids:string[],outline_approved:boolean){return this.request<Document>('/documents',{method:'POST',body:JSON.stringify({title,template_id,source_ids,outline_approved})});}
 save(id:string,base_version:number,title:string,content:Content){return this.request<Document>('/documents/'+encodeURIComponent(id),{method:'PUT',body:JSON.stringify({base_version,title,content})});}
 revisions(id:string){return this.request<List<Document>>('/documents/'+encodeURIComponent(id)+'/revisions');}
 upload(file:File){const form=new FormData();form.append('title',file.name.replace(/\.[^.]+$/,''));form.append('file',file);return this.request<Source>('/sources',{method:'POST',body:form});}
 async download(path:string,filename:string){
 let response:Response;
 try{response=await fetch('/v1'+path,{credentials:'same-origin',headers:this.headers()});}catch{throw new ApiFailure('server_unavailable');}
 if(!response.ok){const error=await response.json().catch(()=>({code:'internal'}));throw new ApiFailure(error.code??'internal');}
 const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
}
