# Hosted API v1 design and review

## Root cause

The app was already running on jason-4090 behind caddy-front.service at the apex domain, while README onboarding still led with the local development supervisor and loopback URLs. There was no api DNS record or API-host Caddy route. Rebuilding the app would not repair the missing ingress or onboarding.

The publication follow-up found a second gap: the live API and local README changes were complete, but GitHub main still served README blob b370c849d8ff79f1ae84e4ccac0d5c31ef3e593c with loopback onboarding and no hosted API URL. An actual GitHub contents fetch reproduced this failure; a fresh nine-group public API smoke passed. Publication therefore needs a scoped Git commit/push, rather than another application deployment.

## Design

Reuse the existing server and owner-scoped storage. A DNS-only api CNAME follows the DDNS-managed apex and avoids a second IP record that could drift. A separate Caddy site exposes only health and versioned API routes. Browser traffic continues to use the apex Origin and same-origin cookie sessions; token-authenticated CLI/MCP requests need no browser Origin. The API host does not serve another copy of the web app or relax origin validation.

MCP remains a local stdio adapter using the remote HTTPS API. No /mcp transport is implemented. Web email login and the separately provisioned operator/library bearer token are different credentials; documentation must not imply that email login supplies a token for any user.

## Review checkpoints

Read the actual running proxy service and binary rather than assuming caddy.service. Preserve the full active shared Caddyfile, modify only the existing BEGIN/END MY DOCUMENT MEMORY block, validate before reload, and keep a backup and concurrency guard. Compare app release and process before/after. Inspect the final diff and verify public HTTPS, authentication, exact CORS Origin, CLI and stdio MCP directly.

## Outcome

The final diff is limited to hosted onboarding, the isolated API proxy block, operational documentation and a read-only public smoke. No application binary, database, email credential or Origin configuration was changed by this rollout. The public API smoke passed on macOS and Linux; Arise and independent DNS/TLS checks confirmed the endpoint, and real CLI/MCP requests used the public URL successfully. Existing library identifiers/revisions and the apex web smoke matched their baseline. Full evidence is in ../test/public-api-v1.md.

The concurrency guard caught another session deploying release 20261109T024546Z-hero. Relevant server source files were compared directly before proceeding; their contents were unchanged. That newer release was retained.

The first file replacement lost the original service-readable group: mode 0640 with root:root could be validated by root but could not be read by the caddy ExecReload process. The previous file contents were restored immediately, the active file was made root:caddy 0640, and the final candidate/backup/rollback preserved uid, gid and mode explicitly. A runuser -u caddy read check and full validation then passed before successful graceful reload. shutil.copy2 preserves mode/timestamps, not ownership. Operational instructions now require service-account validation.

MCP continues to use a local stdio executable and a separately provisioned private token. The API hostname does not provide a remote MCP transport or self-service CLI credentials. Parallel MCP feature additions were left intact; the rollout verified required tool presence and status rather than assuming a permanently fixed tool count.
