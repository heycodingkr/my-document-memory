# Outstanding bug regression inputs and results v1

Specification: [bugfix-regression-v1](../spec/bugfix-regression-v1.md). Date: 2026-11-09.

| Case | Input | Expected result |
|---|---|---|
| BUG-398-DESKTOP | Synthetic email-member login at 1416×614, 1024×500 and 720×614; scroll sidebar with pointer, click Getting started, return, sign out | Sidebar is viewport-bounded; footer controls can be revealed and clicked, guide opens, return works, session becomes anonymous |
| BUG-398-MOBILE | Same signed-in workspace at 390×844 | Navigation fits width; visible Sign out works; no horizontal document overflow |
| BUG-411-MEMBER | Fresh accounts_fixture DB with local/bob account rows and existing synthetic bearer credentials; CLI/MCP contribute/list/check/withdraw | Member contributions succeed; explicit consent required; private data isolation and operator-only approval retained |
| BUG-411-NONMEMBER | Registered bearer owner without accounts row; anonymous requests; list, submit, review, withdraw routes | auth_required/401 before contribution access; no mutation |
| BUG-411-REVIEW | Member fixture submits clean and unsafe templates via HTTP; administrator confirms decisions in browser | Explicit clean approval publishes; unsafe approval remains blocked |

## Evidence

Pending fresh parent-run results. Existing #411 fixture provisioning and sidebar overflow changes are present in the shared working tree; these are baseline source, not changes attributed to this pass.
