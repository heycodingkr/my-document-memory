# Hosted API v1 verification

Issue: #394. Specification: ../spec/public-api-v1.md.

## Inputs and expected results

| Input | Expected |
|---|---|
| DNS api.mydocumentmemory.com | DNS-only CNAME to mydocumentmemory.com; current apex IPv4 resolves |
| HTTPS API /healthz | Valid public certificate, HTTP 200, {"ready":true} |
| HTTP API /healthz | Redirect to the identical HTTPS hostname/path |
| GET API /v1/public/templates, no credentials | 200, public templates only |
| GET API /v1/auth/config | Same configuration as hosted web; email stays enabled |
| GET API /v1/templates, absent/wrong token | 401 auth_required |
| GET API /v1/status, private token, no Origin | 200, service=my-document-memory |
| GET API /v1/status, private token, web Origin | 200 and exact CORS allow-origin |
| OPTIONS API /v1/templates, web Origin, POST + Authorization/Content-Type | Successful CORS preflight |
| GET API /v1/status, private token, unrelated Origin | 401 auth_required; no permissive CORS |
| API / and /assets/probe.js | 404; web assets remain on the web hostname |
| dmem status with DMEM_URL=HTTPS API | JSON service=my-document-memory |
| MCP initialize/tools/list/document_memory_status using HTTPS API | Valid JSON-RPC handshake, required core tools advertised, successful status tool |
| Existing deployed-v1 smoke on web hostname | HTTPS, assets, auth, Origin and existing library reads still pass |
| Live release and application process after ingress change | Same release and application PID; only graceful proxy reload |
| GitHub main README Quick start and CLI/MCP examples | Hosted web/API URLs; no loopback URL before Development |
| GitHub main README Local development | Explicit loopback instructions retained for local use |
| Isolated publication commit | Only README and reviewed issue #394 ingress/docs/smoke files; shared index and parallel edits preserved |

## Reproduction

2026-11-09: apex resolves and /healthz returns 200 ready=true. api.mydocumentmemory.com has no DNS address (gaierror); its HTTPS request fails with URLError. README Quick start and stdio MCP configuration point to local servers.

Focused automated reproduction: python3 tests/smoke/public-api-v1.py. Run before ingress changes, then repeat after deployment. Public probes are read-only; credentials are read only from the excluded .env.production file. DNS UI save is checked by observing the saved row and by independent resolver queries.

## Publication follow-up

Verified 2026-11-09 at 03:03 UTC. The API was already deployed, but the GitHub main README was still blob b370c849d8ff79f1ae84e4ccac0d5c31ef3e593c and lacked the hosted API URL. The failing GitHub contents assertion reproduced that gap.

- The fresh nine-group public API smoke passed; real CLI status and MCP initialize/tools-list/status also passed against https://api.mydocumentmemory.com. Artifacts: .artifacts/deploy/public-api-followup-smoke.json and .artifacts/deploy/public-api-followup-clients.json.
- Commit 1b65192b6be2efe2a5a562eda1f04fa6b42cd4e5 published only the reviewed seven README/ingress/specification/test/design files from an isolated checkout. Parallel account, runtime and product-copy edits were excluded.
- A new GitHub contents fetch from main matched the reviewed README blob daa1e3a2ebd9699f1993d7555ea9f3ec161d2d69 exactly. Assertions confirmed that hosted Quick start and CLI/MCP use the API domain, and loopback instructions appear only in Development. HTTPS /healthz again returned 200 with ready=true.
- The shared checkout HEAD and staged index were preserved; the index digest was unchanged. No application restart, DNS edit or database change was needed. Publication artifact: .artifacts/deploy/public-api-followup-publication.json.

## Results

Verified 2026-11-09 (UTC).

- Before the fix, the focused smoke failed at its first HTTPS request with gaierror/URLError because the API name did not exist.
- Arise Cloudflare UI saved and, after navigation/reload, displayed CNAME api.mydocumentmemory.com → mydocumentmemory.com, DNS only, Auto TTL. Independent Google public DNS returned the CNAME (TTL 300) and apex A 121.167.167.102 (TTL 120).
- The complete proxy candidate passed validation as the caddy service account using the service environment. The final graceful reload succeeded without changing proxy PID 3469454 or app PID 5701. The active app remained /srv/my-document-memory/releases/20261109T024546Z-hero.
- The successful config backup is /etc/caddy/Caddyfile.pre-dmem-api-20261109T025032Z. The full-file hash changed from a5557782b3cca6a33856823a71de8df01996e95cb1627b20b0ceeee7290425b9 to d23f1edcf699f44cd96dd46b35f72df7af4d56e38fe02b81214bf1bc45dbed31; the content outside the application marker block was identical. Artifact: .artifacts/deploy/public-api-rollout.json.
- The exact public-api-v1.py smoke passed all nine check groups on Linux and macOS. Artifacts: .artifacts/deploy/public-api-smoke-linux.json and .artifacts/deploy/public-api-smoke.json. Linux used /etc/my-document-memory/server.env; macOS used the excluded .env.production. Neither printed credentials.
- Arise opened https://api.mydocumentmemory.com/healthz and read {"ready":true}. A Mac curl request using independent DNS-over-HTTPS also verified the public certificate and response. The Mac initially retained a negative DNS cache entry; refreshing mDNSResponder restored normal system resolution, after which the complete Mac smoke passed without a resolver override.
- Actual Rust CLI status and template search plus stdio MCP initialize/tools-list/status passed on Linux and macOS. The deployed source client advertises seven tools; a concurrently updated Mac working-tree client advertises sixteen. Both advertised the required core tools and returned successful hosted API status. Artifacts: .artifacts/deploy/public-api-clients.json and .artifacts/deploy/public-api-clients-macos.json. This does not certify every newly added concurrent MCP tool.
- Existing deployed-v1.py smoke passed before and after: valid HTTPS, rejected invalid credentials, exact Origin checks, HTML/assets and library reads. The six source IDs, twenty template IDs and two document revision entries matched the pre-change baseline. Artifacts: .artifacts/deploy/pre-public-api-web.json and .artifacts/deploy/post-public-api-web.json.
- Local CLI/MCP build and Python smoke syntax checks passed. Whitespace checks were scoped to the touched files; a whole-tree check reported a pre-existing/concurrent trailing blank line in tests/smoke/cases/fmt.py, which this task did not alter.

An initial apply attempt correctly refused a concurrent app release change. The replacement release was inspected: main.rs, http.rs, http/account.rs and identity.rs were byte-identical for the relevant server behavior, and readiness/email configuration remained enabled. A subsequent reload was rejected because the candidate did not retain service-readable group ownership; the disk configuration was restored, root:caddy 0640 access was established and tested, and the final candidate was validated as caddy before the successful reload. Existing web health stayed ready throughout.
