#!/usr/bin/env python3
"""Read-only HTTPS smoke. Credentials stay in a private env file, never in output."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='https://mydocumentmemory.com')
parser.add_argument('--env', type=Path, default=Path('.env.production'))
parser.add_argument('--manifest', type=Path)
parser.add_argument('--out', type=Path)
args = parser.parse_args()
base = args.base.rstrip('/')
assert urllib.parse.urlsplit(base).scheme == 'https', 'Public smoke requires HTTPS'
config = dict(line.split('=', 1) for line in args.env.read_text().splitlines()
              if '=' in line and not line.startswith('#'))
token = config['DMEM_TOKEN'].strip().strip('\"\'')
passed = []


def request(path, *, auth=True, origin=None, override_token=None):
    headers = {}
    if auth:
        headers['Authorization'] = 'Bearer ' + (token if override_token is None else override_token)
    if origin:
        headers['Origin'] = origin
    req = urllib.request.Request(base + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def read(path, **kwargs):
    code, raw, headers = request(path, **kwargs)
    assert code == 200, f'{path}: HTTP {code}'
    assert token.encode() not in raw, 'Response unexpectedly contains connection secret'
    return json.loads(raw)


assert read('/healthz', auth=False) == {'ready': True}
passed.append('public HTTPS health and certificate validation')
for params in ({'auth': False}, {'override_token': 'wrong-connection-token'}):
    code, raw, _ = request('/v1/templates', **params)
    assert code == 401 and json.loads(raw)['code'] == 'auth_required'
passed.append('missing and invalid credentials return 401')
status = read('/v1/status', origin=base)
assert status['service'] == 'my-document-memory'
code, raw, _ = request('/v1/status', origin='https://untrusted.invalid')
assert code == 401 and json.loads(raw)['code'] == 'auth_required'
passed.append('configured public Origin accepted, unrelated Origin rejected')
code, html, headers = request('/', auth=False)
assert code == 200 and b'My Document Memory' in html
assets = re.findall(rb'(?:src|href)="(/assets/[^\"]+)"', html)
assert assets, 'Production asset links missing'
for asset in assets:
    code, raw, _ = request(asset.decode(), auth=False)
    assert code == 200 and len(raw) > 100 and token.encode() not in raw
passed.append('production HTML and all linked assets load')

sources = read('/v1/sources')['items']
templates = read('/v1/templates')['items']
documents = read('/v1/documents')['items']
if args.manifest:
    manifest = json.loads(args.manifest.read_text())
    for item in manifest['files']:
        source = read('/v1/sources/' + item['source_id'])
        assert source['title'] == item['title']
        assert source['spans'], 'Extracted source spans missing'
        original = Path(item['path']).read_bytes()
        code, raw, _ = request('/v1/sources/' + item['source_id'] + '/file')
        assert code == 200 and raw == original, 'Original bytes changed'
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
        assert source['checksum'] == item['sha256']
        template = read('/v1/templates/' + item['template_id'])
        assert template['visibility'] == 'private'
        assert template['form']['family'] == item['family']
        assert template['sections'] == item['sections']
        query = urllib.parse.quote(item['title'])
        assert any(s['id'] == source['id'] for s in read('/v1/sources?q=' + query)['items'])
        assert any(t['id'] == template['id'] for t in read('/v1/templates?q=' + query)['items'])
    passed.append(f"{len(manifest['files'])} private original memories and forms match bytes, SHA-256, family, sections and search")
    for item in manifest.get('documents', []):
        document = read('/v1/documents/' + item['id'])
        assert document['version'] == item['version']
        assert document['template']['template_id'] == item['template_id']
        assert [(s['source_id'], s['version']) for s in document['source_versions']] == [(item['source_id'], 1)]
        assert item['expected_text'] in json.dumps(document['content'], ensure_ascii=False)
        if 'slide_count' in item:
            assert len(document['content']['slides']) == item['slide_count']
        history = read('/v1/documents/' + item['id'] + '/revisions')['items']
        assert [revision['version'] for revision in history] == [2, 1]
        extension = 'pptx' if document['family'] == 'deck' else 'docx'
        code, raw, _ = request('/v1/documents/' + item['id'] + '/export/' + extension)
        assert code == 200
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                if name.endswith(('.xml', '.rels')):
                    ET.fromstring(archive.read(name))
    passed.append(f"{len(manifest.get('documents', []))} saved documents preserve pinned versions, history and valid Office exports")

result = {'base': base, 'passed': passed, 'source_ids': [s['id'] for s in sources],
          'template_ids': [t['id'] for t in templates],
          'document_versions': {d['id']: d['version'] for d in documents}}
if args.out:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
for item in passed:
    print('PASS:', item)
print(f'Library: {len(sources)} sources, {len(templates)} forms, {len(documents)} documents')
