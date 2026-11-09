#!/usr/bin/env bash
# Deploy the production build to the existing Ubuntu host. DNS is managed separately.
set -euo pipefail
cd "$(dirname "$0")/.."
DMEM_DEPLOY_HOST="${1:?Usage: bash scripts/deploy-production.sh SSH_HOST}"
DMEM_RELEASE="$(date -u +%Y%m%dT%H%M%SZ)-$$"
DMEM_BASE=/srv/my-document-memory
mkdir -p .artifacts/deploy
DMEM_ARCHIVE=".artifacts/deploy/$DMEM_RELEASE.tar.gz"
test -s web/dist/index.html
COPYFILE_DISABLE=1 tar -czf "$DMEM_ARCHIVE" Cargo.toml Cargo.lock crates contracts web/dist deploy
ssh -o BatchMode=yes "$DMEM_DEPLOY_HOST" "sudo -n install -d -o jason -g jason $DMEM_BASE/releases/$DMEM_RELEASE"
scp -q "$DMEM_ARCHIVE" "$DMEM_DEPLOY_HOST:$DMEM_BASE/releases/$DMEM_RELEASE/source.tar.gz"
ssh -o BatchMode=yes "$DMEM_DEPLOY_HOST" "flock -E 75 -n /tmp/my-document-memory-deploy.lock bash -s -- $DMEM_RELEASE" <<'REMOTE'
set -euo pipefail
release="$1"
base=/srv/my-document-memory
cd "$base/releases/$release"
tar -xzf source.tar.gz
export PATH="$HOME/.cargo/bin:$PATH"
cargo +1.95.0 build --locked --release -p dmem-server
sudo -n bash -s -- "$base/releases/$release" <<'ROOT'
set -euo pipefail
release="$1"
getent passwd dmem >/dev/null || useradd --system --home /var/lib/my-document-memory --shell /usr/sbin/nologin dmem
install -d -m 0700 -o dmem -g dmem /var/lib/my-document-memory
install -d -m 0700 /etc/my-document-memory
if [ ! -f /etc/my-document-memory/server.env ]; then
  python3 - <<'PY'
from pathlib import Path
import secrets
p=Path("/etc/my-document-memory/server.env")
p.write_text("DMEM_TOKEN="+secrets.token_urlsafe(48)+"\nDMEM_ADDR=127.0.0.1:3848\nDMEM_DATABASE=/var/lib/my-document-memory/library.sqlite3\nDMEM_WEB_ORIGIN=https://mydocumentmemory.com\nDMEM_WEB_DIR=/srv/my-document-memory/current/web/dist\n")
p.chmod(0o600)
PY
fi
if [ -L /srv/my-document-memory/current ]; then
  readlink /srv/my-document-memory/current > /etc/my-document-memory/previous-release
fi
ln -sfn "$release" /srv/my-document-memory/current
install -m 0644 "$release/deploy/my-document-memory.service" /etc/systemd/system/my-document-memory.service
systemctl daemon-reload
systemctl enable my-document-memory.service
systemctl restart my-document-memory.service
ROOT
for attempt in $(seq 1 40); do
  if curl --fail --silent http://127.0.0.1:3848/healthz; then
    printf "\nRelease %s ready on loopback port 3848\n" "$release"
    exit 0
  fi
  sleep 1
done
exit 1
REMOTE
printf "Deployment release %s completed on %s\n" "$DMEM_RELEASE" "$DMEM_DEPLOY_HOST"
