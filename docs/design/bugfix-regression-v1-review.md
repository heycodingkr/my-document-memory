# Outstanding bug regression review v1

Date: 2026-11-09. Parent owns root-cause analysis, implementation review and verification.

## Baseline and design constraints

The checkout contains substantial pre-existing uncommitted account, web-memory, documentation and demo work. No reset, broad commit, production operation or overlapping feature rewrite is authorized by this regression pass. #406 remains with its existing owner.

#398 was reported when sidebar overflow was visible. Current CSS already has overflow-y:auto, so reproduce against the current build before selecting a fix. Inspect flex child sizing and mobile breakpoints only if the regression persists.

#411 was reported after contribution routes gained require_member. Current accounts_fixture already inserts local/bob account rows; preserve this provisioning and the server gate. Fresh builds and real product/browser smokes will determine whether the reported mismatch remains.

## Review and results

Pending focused reproduction and fresh validation.
