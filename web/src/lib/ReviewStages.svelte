<script lang="ts">
 import type {ReviewReport} from './types';
 let {report}:{report:ReviewReport}=$props();
 const verdicts={ready:'Ready for a decision',needs_review:'Human review required',blocked:'Changes required before approval'};
 const statuses:Record<string,string>={passed:'Passed',needs_review:'Needs review',blocked:'Blocked',pending:'Awaiting decision',approved:'Approved',rejected:'Rejected',withdrawn:'Withdrawn'};
 const findings:Record<string,string>={api_key_sk:'API key detected',aws_access_key:'Access key detected',github_token:'Access token detected',jwt:'Session token detected',bearer_token:'Bearer credential detected',private_key:'Private key detected',slack_token:'Access token detected',google_api_key:'API key detected',credential_assignment:'Credential value detected',email:'Email address detected',phone:'Phone number detected',national_id:'Personal identifier detected',card_number:'Card number detected',account_number:'Account number detected',prompt_override:'Instruction override detected',license_not_allowed:'License is not permitted',relicense_forbidden:'Original license must be preserved',exact_duplicate:'Same structure already public',near_duplicate:'Similar structure already public',limit_exceeded:'Structure exceeds a limit',empty_field:'Required field is empty',control_char:'Unexpected control character',markup:'Markup needs removal',invalid_form:'Document form is invalid',invalid_snapshot:'Snapshot is invalid'};
</script>
<section class="review-report">
 <h3 class:blocked={report.verdict==='blocked'}>{report.decision==='approve'?'Approved at review':report.decision==='reject'?'Submission rejected':verdicts[report.verdict]}</h3>
 <ol aria-label="Review stages" class="review-stages">
  {#each report.stages as stage}<li><span class="rule">{stage.rule}</span><span>{stage.label}</span><strong class:blocked={stage.status==='blocked'}>{statuses[stage.status]??stage.status}</strong></li>{/each}
 </ol>
 {#if report.findings.length}
 <ul class="findings" aria-label="Review findings">{#each report.findings as finding}<li><strong>{findings[finding.code]??'Review this field'}</strong><span>{finding.field.startsWith('public:')?'Compare with an existing public template':finding.field} · {finding.action==='block'?'Changes required':'Reviewer judgment'}</span></li>{/each}</ul>
 {:else}<p class="muted">The automatic checks found no blocking issues. A reviewer still decides whether to publish.</p>{/if}
 {#if report.decided_at}<p class="muted">Decision recorded {new Date(report.decided_at*1000).toLocaleString()} · snapshot v{report.snapshot_version}</p>{/if}
</section>
<style>
 .review-report h3{font-size:17px;margin:24px 0 15px}.blocked{color:#a14c39}.review-stages{list-style:none;padding:0;margin:0;border:1px solid var(--line);border-radius:10px;overflow:hidden}.review-stages li{display:grid;grid-template-columns:26px minmax(0,1fr) auto;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line);font-size:12px}.review-stages li:last-child{border-bottom:0}.rule{font-size:10px;color:var(--muted)}.review-stages strong{font-size:10px}.findings{list-style:none;padding:0;margin:18px 0}.findings li{display:grid;gap:6px;padding:12px 0;border-bottom:1px solid var(--line);overflow-wrap:anywhere}.findings strong{font-size:12px}.findings span{font-size:11px;color:var(--muted)}.muted{margin-top:16px}@media(max-width:700px){.review-stages li{padding:12px 10px;gap:6px;grid-template-columns:22px minmax(0,1fr) 83px}.review-stages strong{text-align:right;font-size:9px}}
</style>
