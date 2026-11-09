#!/usr/bin/env python3
"""Seed a synthetic scale fixture in the isolated accounts_fixture database."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
import urllib.parse
import urllib.request
import uuid

parser = argparse.ArgumentParser()
parser.add_argument('--database', required=True, type=Path)
parser.add_argument('--base', required=True)
args = parser.parse_args()
base = args.base.rstrip('/')
assert urllib.parse.urlsplit(base).hostname in ('127.0.0.1', 'localhost', '::1')
assert args.database.is_file(), 'Start the isolated accounts_fixture server first'
headers = {'Authorization': 'Bearer automated-smoke-token-not-production',
           'Origin': base, 'Content-Type': 'application/json'}
request = urllib.request.Request(base + '/v1/templates', headers=headers, data=json.dumps({
    'title': 'Synthetic queue scale seed',
    'summary': 'Reusable synthetic review structure',
    'form': {'provider': 'docx', 'doc_type': 'report', 'locale': 'en-US'},
    'sections': ['Queue assumptions', 'Independent verification', 'Decision rationale'],
    'tags': [],
}).encode())
with urllib.request.urlopen(request, timeout=10) as response:
    template = json.load(response)
run = uuid.uuid4().hex[:8]
now = int(time.time())
with sqlite3.connect(args.database, timeout=10) as db:
    for status, count, created in [('pending', 121, now - 10000), ('rejected', 120, now + 10000)]:
        for i in range(count):
            suffix = uuid.uuid4().hex
            private = {**template, 'id': 'tpl_' + suffix,
                       'title': f'Queue 407 {run} {status} {i:04}'}
            stamp = created + i // 7
            db.execute("INSERT INTO records(id,owner,kind,version,payload,updated_at) VALUES(?,'local','template',1,?,?)",
                       (private['id'], json.dumps(private), stamp))
            snapshot = {**private, 'id': 'public_' + suffix, 'visibility': 'public',
                        'author': 'Synthetic queue author', 'license': 'CC-BY-4.0'}
            db.execute("INSERT INTO contributions(id,owner,template_id,status,snapshot,created_at,updated_at) VALUES(?,'local',?,?,?,?,?)",
                       ('contrib_' + suffix, private['id'], status, json.dumps(snapshot), stamp, stamp))
    # Expected results use an independent unbounded SQL query, not the paginated API.
    rows = [{'id': r[0], 'title': json.loads(r[2])['title'], 'status': r[1]}
            for r in db.execute('SELECT id,status,snapshot FROM contributions ORDER BY created_at DESC,id ASC')]
print(json.dumps({'run': run, 'all': rows,
                  'pending': [r for r in rows if r['status'] == 'pending'],
                  'rejected': [r for r in rows if r['status'] == 'rejected']}))
