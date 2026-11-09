# Production single owner deployment

Verified host: `jason-4090`, Ubuntu x86_64. Public origin: https://mydocumentmemory.com. This deploys runtime-v1 behind the existing Caddy HTTPS service. It remains a single owner application protected by a private connection token. Google provider synchronization and multiple user accounts are outside this release.

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

The zone has an unproxied apex A record pointing to the host public IPv4 and an unproxied `www` CNAME pointing to the apex, TTL 120. The host's existing Caddy dynamic DNS configuration includes `mydocumentmemory.com @`, so the apex follows a public IP change. Existing records and other sites were preserved.

`Caddyfile.fragment` is the application-specific block appended to `/etc/caddy/Caddyfile`. It uses the existing `direct_tls` and `rate_limit_per_ip` snippets; it is not a standalone Caddyfile. The host file was validated before reload and backed up as `/etc/caddy/Caddyfile.pre-dmem-20261109T012225Z`, with a separate backup before adding dynamic DNS. Caddy obtains public certificates using TLS-ALPN and redirects `www` to the apex.

## Verification and operations

```sh
python3 tests/smoke/deployed-v1.py --out .artifacts/deploy/smoke.json
# After seed upload, also pass the verified local manifest:
python3 tests/smoke/deployed-v1.py --manifest .artifacts/seed-library/manifest.json --out .artifacts/deploy/seeded-smoke.json
ssh jason-4090 systemctl status my-document-memory
ssh jason-4090 sudo journalctl -u my-document-memory --no-pager -n 30
```

The public smoke script is read-only. It validates HTTPS, credentials, browser Origin handling, built assets and optionally the uploaded original bytes, source checksums, private forms, immutable history and Office exports. See `docs/test/seed-deployment-v1.md` for the actual release, original Google file links and end-to-end evidence.

For rollback, inspect `/etc/my-document-memory/previous-release`, point `current` at that recorded release and restart only `my-document-memory`. The database and secret remain outside release directories. Do not copy the production database into a source archive.
