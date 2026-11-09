export type CopyMode='structure_only'|'full';
export interface WebForm{provider:string;family:string;doc_type:string;locale:string;region?:string;variant?:string;page?:unknown}
export interface WebPreview{preview_id:string;canonical_url:string;title:string;provider:string;form:WebForm;outline:string[];table_headers:string[][];license:string;copy_policy_default:CopyMode;warnings:string[];expires_at:number;untrusted:true}
export interface WebOrigin{record_id:string;canonical_url:string;license:string;copy_policy:CopyMode;provenance:string;content_hash:string;retrieved_at:number}
export interface WebImportResult{id:string;kind:'template'|'reference';version:number;created:boolean;origin:WebOrigin;warnings:string[];body_chars_removed:number}
export interface WebImportRequest{preview_id:string;kind:'template'|'reference';title?:string;form?:{provider:string;doc_type:string;locale:string;region?:string;variant?:string};copy_mode?:CopyMode}
export interface WebSearchHit{title:string;url:string;snippet:string}
