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
export type ContributionStatus = 'pending'|'approved'|'rejected'|'withdrawn';
export type ContributionQueueStatus = ContributionStatus|'all';
export type ContributionPage = List<Contribution>&{next_cursor:string|null};
export type Session = {account:{id:string;email:string};csrf_token:string};
export type MemberProfile = {handle:string|null;public_profile:boolean;total_points:number;approved_contributions:number;overall_rank:number|null;public_rank:number|null;points_per_approval:number};
export type RankedMember = {handle:string;total_points:number;approved_contributions:number;rank:number};
export type LeaderboardData = {items:RankedMember[];total:number;next_offset:number|null;points_per_approval:number};
export type PublicMemberProfile = {handle:string;total_points:number;approved_contributions:number;rank:number|null;templates:Template[]};
export type Dashboard = {templates:number;sources:number;documents:number;contributions:number};
export type ReviewFinding = {rule:string;field:string;code:string;reason:string;action:'block'|'review'};
export type ReviewReport = {schema_version:number;policy:string;contribution_id:string;snapshot_version:number;snapshot_hash:string;verdict:'ready'|'needs_review'|'blocked';reasons:string[];findings:ReviewFinding[];stages:{rule:string;label:string;status:string}[];decision:'approve'|'reject'|null;decided_at:number|null};
export type Contribution = {id:string;template_id:string;status:ContributionStatus;snapshot:Template;public_id:string|null;created_at:number;updated_at:number;review?:ReviewReport};
