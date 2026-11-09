# Production deployment

Verified host: `jason-4090`, Ubuntu x86_64. The web app is https://mydocumentmemory.com; the HTTP API base is `https://api.mydocumentmemory.com`. Both use the existing Rust server behind `caddy-front.service`. Email-link browser accounts are enabled. CLI and stdio MCP access uses a separately provisioned private library token; email sessions do not issue that token. Provider synchronization and remote HTTP MCP are outside this release.

## Application release

After reviewing and testing the source snapshot:

```sh
cargo test --workspace
pnpm --dir web check
pnpm --dir web build
bash scripts/deploy-production.sh jason-4090
```

The installer uses the host's existing Rust 1.95.0 toolchain, creates an isolated release under `/srv/my-document-memory/releases`, keeps persistent data in `/var/lib/my-document-memory`, and starts the enabled `my-document-memory.service` as the dedicated `dmem` account. API binding stays `127.0.0.1:3848`. Application configuration is `/etc/my-document-memory/server.env`, mode 0600. A private local copy is `.env.production`, excluded from Git. Never paste its token into documentation, shell arguments or logs.

## Domain and HTTPS

The zone has an unproxied apex A record pointing to the host public IPv4 and DNS-only `www` and `api` CNAME records pointing to the apex. The apex and `www` TTL is 120; `api` uses Auto. The host's existing Caddy dynamic DNS configuration includes `mydocumentmemory.com @`, so both aliases follow an apex IP change without a separate DDNS entry. Existing records and other sites are preserved.

`Caddyfile.fragment` is the delimited application block in `/etc/caddy/Caddyfile`. It uses the existing `direct_tls` and `rate_limit_per_ip` snippets; it is not a standalone Caddyfile. Update only that block, preserve all other sites and global configuration, back up the active file, preserve owner/group and mode (currently root:caddy 0640), validate the complete candidate as the caddy service account, and gracefully reload `caddy-front.service`. The running binary is `/usr/local/bin/caddy-front`; validation needs the service environment file `/etc/web-agentic-memory/caddy.env` as well as the referenced DNS-token file. Never print those secrets. Caddy obtains public certificates using TLS-ALPN and redirects `www` to the apex.

The API hostname forwards `/healthz` and `/v1/*` to `127.0.0.1:3848`; all other paths return 404. The web hostname keeps serving the app and API. `DMEM_WEB_ORIGIN` stays `https://mydocumentmemory.com`, and CLI/MCP bearer requests omit browser Origin. App deployment does not install or reload the proxy fragment automatically. See [the API rollout specification](../docs/spec/public-api-v1.md) and [verification record](../docs/test/public-api-v1.md).

## Verification and operations

```sh
python3 tests/smoke/public-api-v1.py --out .artifacts/deploy/public-api-smoke.json
python3 tests/smoke/deployed-v1.py --out .artifacts/deploy/smoke.json
# After seed upload, also pass the verified local manifest:
python3 tests/smoke/deployed-v1.py --manifest .artifacts/seed-library/manifest.json --out .artifacts/deploy/seeded-smoke.json
ssh jason-4090 systemctl status my-document-memory
ssh jason-4090 sudo journalctl -u my-document-memory --no-pager -n 30
```

The public smoke script is read-only. It validates HTTPS, credentials, browser Origin handling, built assets and optionally the uploaded original bytes, source checksums, private forms, immutable history and Office exports. See `docs/test/public-api-v1.md` for the API rollout evidence and `docs/spec/seed-deployment-v1.md` for the seed-library contract. The [seed verification record](../docs/test/seed-deployment-v1.md) lists native Google originals and imported IDs; the [hero verification record](../docs/test/hero-examples-v1.md) records the public SVG examples, web-only release and data-preservation smoke.

For rollback, inspect `/etc/my-document-memory/previous-release`, point `current` at that recorded release and restart only `my-document-memory`. The database and secret remain outside release directories. Do not copy the production database into a source archive.
