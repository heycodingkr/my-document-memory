#!/usr/bin/env python3
"""Real browser login/community against isolated Rust API + synthetic mail capture."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='dmem-accounts-') as d:
    tmp=Path(d)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    env={**os.environ,'DMEM_E2E_ADDR':f'127.0.0.1:{port}','DMEM_E2E_URL':base,
         'DMEM_E2E_MAILBOX':str(tmp/'mail.json'),'DMEM_E2E_DATABASE':str(tmp/'library.sqlite3'),
         'DMEM_E2E_WEB_DIR':str(ROOT/'web/dist'),
         'DMEM_E2E_OUTPUT_DIR':str(ROOT/'target/e2e-logs'/('accounts-'+str(time.time_ns())))}
    with (tmp/'server.log').open('w') as log:
        process=subprocess.Popen([str(ROOT/'target/debug/examples/accounts_fixture')],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            for _ in range(100):
                if process.poll() is not None: raise RuntimeError('fixture exited')
                try:
                    if urllib.request.urlopen(base+'/healthz',timeout=1).status==200:break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('fixture readiness timeout')
            subprocess.run(['pnpm','exec','playwright','test',*env.get('DMEM_E2E_TESTS','accounts.spec.ts public-access.spec.ts review.spec.ts review-queue.spec.ts members.spec.ts admin-email.spec.ts sidebar.spec.ts').split()],cwd=ROOT/'web',env=env,check=True)
        finally:
            process.terminate();process.wait(timeout=5)
