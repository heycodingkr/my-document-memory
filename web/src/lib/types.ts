export type Family = 'document' | 'deck' | 'sheet';
export type Citation = {source_id:string;source_version:number;span_id:string};
export type Block =
 | {type:'heading';text:string;level:number}
 | {type:'paragraph';text:string}
 | {type:'quote';text:string;citation:Citation|null}
 | {type:'list';items:string[]}
 | {type:'table';rows:string[][]};
export type Slide = {title:string;body:string;citations:Citation[]};
export type Content = {blocks:Block[];slides:Slide[]};
export type Origin = {template_id:string;version:number;author:string;license:string};
export type Template = {id:string;version:number;title:string;summary:string;form:{family:Family;provider:string;doc_type:string;locale:string};tags:string[];sections:string[];author:string;license:string;visibility:'private'|'public';origin:Origin|null;attributions?:Origin[]};
export type Source = {id:string;version:number;title:string;filename:string;format:string;checksum:string;spans:{id:string;location:string;text:string}[]};
export type Document = {id:string;version:number;title:string;family:Family;template:Origin;source_versions:{source_id:string;version:number;title:string}[];content:Content;created_at:number;updated_at:number};
export type List<T> = {items:T[]};
export type Session = {account:{id:string;email:string};csrf_token:string};
export type Dashboard = {templates:number;sources:number;documents:number;contributions:number};
export type Contribution = {id:string;template_id:string;status:'pending'|'approved'|'rejected'|'withdrawn';snapshot:Template;public_id:string|null;created_at:number;updated_at:number};
