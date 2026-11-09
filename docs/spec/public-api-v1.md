# Hosted API v1

Issue: #394. Requested on 2026-11-09.

## Behavior

The hosted web app is https://mydocumentmemory.com. The hosted HTTP API base is https://api.mydocumentmemory.com (without /v1); clients append versioned routes. Readers can open the hosted library without running a local server. CLI and stdio MCP may use the hosted API with a separately provisioned private library token. Email web sessions do not issue a CLI token, and this change does not add remote HTTP MCP.

The API hostname is a DNS-only CNAME to mydocumentmemory.com, inheriting the existing apex A record and its DDNS updates. Caddy terminates HTTPS and forwards only /healthz and /v1/* to the existing loopback listener 127.0.0.1:3848. Other API-host paths return 404. Apex/www behavior, configured browser Origin, authentication, database, binaries and active app release remain intact.

## Dependency order and ownership

All implementation and verification stays inline: the necessary source/configuration reads and decisions require direct inspection. No delegated claims are evidence.

1. Reproduce the missing API endpoint; inspect Git changes, live release, proxy, authentication and existing smoke. Output: focused failing external smoke and baseline. Independent check: apex HTTPS remains ready; identify the actual caddy-front.service listener.
2. Add the isolated Caddy API site to deploy/Caddyfile.fragment and create the DNS CNAME through the signed-in Arise Cloudflare UI. Output: reviewed config and saved DNS row. Independent check: public DNS resolves to the apex, proxy remains off.
3. Back up the live Caddyfile, replace only the delimited application block, preserve uid/gid/mode and validate the candidate as the caddy service account using the running proxy binary and service environment, then gracefully reload caddy-front. Guard against concurrent file changes. Output: live route and backup path. Independent check: external certificate-validating API smoke, existing apex smoke, CLI and stdio MCP status. Roll back the application block if verification fails.
4. Put hosted onboarding first in README and record operational details, root cause, verification and limitations. Output: accurate public URLs and explicitly separate local development steps. Independent check: focused diff review and commands exercised against the public API.

## Publication follow-up (2026-11-09)

The live API rollout and a working-tree README edit do not prove that GitHub readers receive the new onboarding. The follow-up first fetches the actual GitHub README and checks the hosted API URL; before publication this check fails while the nine-group live API smoke passes.

Dependency-ordered atomic goals, all inline:

1. Inspect the published README, local diff, existing verification and current live API. Output: remote README blob SHA and focused failure, plus a fresh passing API artifact. Independent check: the anonymous HTTPS health endpoint and hosted web readiness.
2. Prepare an isolated checkout from the current remote main. Apply only hosted Quick start/CLI/MCP/local-development README sections and the reviewed issue #394 ingress/specification/test/design files. Output: a reviewable commit that excludes parallel application, account and product-copy work. Independent check: inspect the complete commit diff and assert no loopback address appears before Development, both client examples use the API domain, and local development still documents loopback.
3. Publish the scoped commit with a normal fast-forward push. Output: a GitHub commit identifier. Independent check: fetch README from GitHub again and verify its API URL/client configuration; recheck public API health. No application restart, DNS change or database migration is required because the ingress is already live.

## Constraints

Never output or place production token values in documentation, arguments, browser storage or source archives. Preserve unrelated working-tree edits, other proxy sites and DNS records. Do not publish the private GitHub repository or invent per-account API-token provisioning. No application release or database migration is needed for this ingress change.
