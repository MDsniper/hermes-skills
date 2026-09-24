"""Opt-in public-source integration tests. Not a general scraper.

Usage: pinned-python live_checks.py NEW_OUTPUT_DIRECTORY
Evidence is retained even when a platform refuses access. No credentials,
proxy, browser session, account actions, or media downloads are used.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

import feedparser

OUT = Path(sys.argv[1]).expanduser().resolve()
OUT.mkdir(parents=True, exist_ok=False)
ROWS = []
STAMP = dt.datetime.now(dt.timezone.utc).isoformat()
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def retain(row):
    ROWS.append(row)
    (OUT / 'results.json').write_text(json.dumps(ROWS, indent=2, ensure_ascii=False))
    print(json.dumps({k: row[k] for k in ('platform','status','detail')}, ensure_ascii=False), flush=True)

def get(name, platform, url, kind):
    row = dict(name=name, platform=platform, url=url, method='GET', credentials=False,
               retrieved_at=STAMP, status='failed', detail='', raw=str(OUT / (name + '.body')))
    req = urllib.request.Request(url, headers={'User-Agent': 'Hermes-Public-Source-Check/0.1', 'Accept': '*/*'})
    try:
        with OPENER.open(req, timeout=25) as response:
            body = response.read(5 * 1024 * 1024 + 1)
            row['http_status'] = response.status
            row['final_url'] = response.url
            row['content_type'] = response.headers.get('Content-Type', '')
        (OUT / (name + '.body')).write_bytes(body)
        row['sha256'] = hashlib.sha256(body).hexdigest()
        if len(body) > 5 * 1024 * 1024:
            row.update(status='failed', detail='Response exceeds 5 MiB limit; not parsed')
        elif kind == 'github':
            data = json.loads(body)
            assert data['full_name'] == 'kepano/defuddle' and data['private'] is False
            row.update(status='success', detail='Public repo full_name and private=false verified')
        elif kind == 'rss':
            data = feedparser.parse(body)
            entries = [{'title': e.get('title'), 'url': e.get('link')} for e in data.entries]
            assert entries and all(e['title'] and e['url'] for e in entries)
            (OUT / (name + '.parsed.json')).write_text(json.dumps({'title': data.feed.get('title'), 'bozo': bool(data.bozo), 'entries': entries}, indent=2))
            row.update(status='success', detail=f'{len(entries)} title/link entries verified; bozo={bool(data.bozo)}')
        elif kind == 'v2ex':
            data = json.loads(body)
            assert isinstance(data, list) and data and all(x.get('id') and x.get('title') and x.get('url') for x in data)
            row.update(status='success', detail=f'{len(data)} topic IDs/titles/URLs verified')
        elif kind == 'bilibili':
            data = json.loads(body)
            if data.get('code') == 0 and data.get('data', {}).get('title'):
                row.update(status='success', detail='Public video metadata only: ' + data['data']['title'])
            else:
                row.update(status='blocked', detail='API refused metadata: ' + str(data.get('code')) + ' ' + str(data.get('message')))
        elif kind == 'reddit':
            data = json.loads(body)
            children = data.get('data', {}).get('children', [])
            assert children and all(x.get('data', {}).get('title') for x in children)
            row.update(status='success', detail=f'{len(children)} public post titles verified; not full threads')
        elif kind == 'article':
            text = body.decode('utf8', errors='replace')
            assert 'Use the saw, fear the saw' in text and '<html' in text.lower(), 'Missing expected title or HTML document'
            row.update(status='success', detail='Live HTML and expected article title verified; extraction separately checked')
        else:
            text = body.decode('utf8', errors='replace')
            markers = [s for s in ('Just a moment', 'Something went wrong', 'JavaScript is not available', 'Sign in') if s in text]
            row.update(status='blocked' if markers else 'unverified', detail='No post-text semantic success; markers=' + ', '.join(markers))
    except urllib.error.HTTPError as exc:
        body = exc.read(5 * 1024 * 1024)
        (OUT / (name + '.body')).write_bytes(body)
        row.update(http_status=exc.code, sha256=hashlib.sha256(body).hexdigest(), status='needs_auth' if exc.code == 401 else 'blocked' if exc.code in (403,412,429,451) else 'failed', detail=f'HTTP {exc.code}; no auth/proxy/retry fallback')
        if exc.headers.get('Location'):
            row['redirect_location'] = exc.headers['Location']
            row['detail'] = 'Redirect not followed; public destination requires separate review'
    except Exception as exc:
        row.update(status='failed', detail=f'{type(exc).__name__}: {exc}')
    retain(row)

for args in [
    ('article', 'Web article', 'https://stephango.com/saw', 'article'),
    ('github', 'GitHub anonymous API', 'https://api.github.com/repos/kepano/defuddle', 'github'),
    ('rss', 'RSS', 'https://www.nasa.gov/feed/', 'rss'),
    ('v2ex', 'V2EX', 'https://www.v2ex.com/api/topics/hot.json', 'v2ex'),
    ('reddit', 'Reddit', 'https://www.reddit.com/r/Python/top.json?limit=3&t=day', 'reddit'),
    ('x', 'X public HTML', 'https://x.com/jack/status/20', 'x'),
    ('bilibili', 'Bilibili public API', 'https://api.bilibili.com/x/web-interface/view?bvid=BV17x411w7KC', 'bilibili'),
]:
    get(*args)

# Real pinned upstream CLI. Ignore all user config/plugin locations.
ytdlp = str(Path(sys.executable).parent / 'yt-dlp')
url = 'https://www.youtube.com/watch?v=UF8uR6Z6KLc'
argv = [ytdlp, '--ignore-config', '--no-plugin-dirs', '--no-cache-dir', '--no-playlist', '--skip-download', '--no-simulate', '--js-runtimes', 'node', '--socket-timeout', '15', '--retries', '0', '--extractor-retries', '0', '--write-subs', '--write-auto-subs', '--sub-langs', 'en', '--sub-format', 'vtt', '-o', str(OUT / '%(id)s.%(ext)s'), '--dump-single-json', '--', url]
env = {k: os.environ[k] for k in ('PATH','HOME','TMPDIR','LANG') if k in os.environ}
row = dict(name='youtube', platform='YouTube', url=url, command=argv, credentials=False, retrieved_at=STAMP, status='failed', detail='')
try:
    p = subprocess.run(argv, capture_output=True, text=True, timeout=90, env=env)
    (OUT / 'youtube.stdout').write_text(p.stdout)
    (OUT / 'youtube.stderr').write_text(p.stderr)
    row['exit_code'] = p.returncode
    if p.returncode == 0:
        data = json.loads(p.stdout)
        assert data.get('id') == 'UF8uR6Z6KLc' and data.get('title')
        tracks = [x for x in OUT.glob('*.vtt') if x.stat().st_size and '-->' in x.read_text()]
        row.update(status='success', detail=f'Metadata title/ID verified; caption files with timestamps={len(tracks)}', transcript_status='success' if tracks else 'unavailable')
    else:
        lower = p.stderr.lower()
        status = 'needs_auth' if 'sign in' in lower or 'login' in lower else 'blocked' if any(s in lower for s in ('403','429','bot','not available')) else 'failed'
        row.update(status=status, detail=p.stderr[-1600:], transcript_status='not_obtained')
except subprocess.TimeoutExpired as exc:
    (OUT / 'youtube.stderr').write_text('Bounded 90-second deadline exceeded')
    row.update(status='failed', detail='90-second deadline; no retry', transcript_status='not_obtained')
retain(row)

# Authenticated gh public read is explicitly distinct from anonymous API success.
if shutil.which('gh'):
    cmd = ['gh','repo','view','kepano/defuddle','--json','nameWithOwner,url,description,isPrivate']
    env = dict(os.environ, GH_TELEMETRY='false', DO_NOT_TRACK='true', GH_NO_UPDATE_NOTIFIER='1')
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        (OUT / 'github-cli.stdout').write_text(p.stdout)
        (OUT / 'github-cli.stderr').write_text(p.stderr)
        d = json.loads(p.stdout) if p.returncode == 0 else {}
        ok = d.get('nameWithOwner') == 'kepano/defuddle' and d.get('isPrivate') is False
        retain(dict(name='github-cli',platform='GitHub CLI',url='https://github.com/kepano/defuddle',command=cmd,retrieved_at=STAMP,credentials='existing gh auth may be used',status='success' if ok else 'failed',exit_code=p.returncode,detail='Public repo identity and visibility verified' if ok else p.stderr))
    except Exception as exc:
        retain(dict(name='github-cli',platform='GitHub CLI',url='https://github.com/kepano/defuddle',retrieved_at=STAMP,status='failed',detail=str(exc)))

for platform, detail in [
    ('Twitter CLI / X API','Needs cookie credentials or API setup; not installed or exercised'),
    ('Facebook','Session-backed upstream adapter; excluded from public-only testing'),
    ('Instagram','Session-backed upstream adapter; excluded from public-only testing'),
    ('XiaoHongShu','Session/cookie-backed adapters; excluded'),
    ('LinkedIn','Public profile route not tested; no login-backed integration installed'),
    ('Boss Zhipin','Browser session adapter excluded'),
    ('Xueqiu','Cookie/session route excluded'),
    ('Xiaoyuzhou','Transcription requires external provider key; excluded'),
    ('Exa / mcporter','No MCP or service configuration changes; not tested'),
    ('Jina Reader','Anonymous zero-key claim not assumed; no key or relay test performed'),
]:
    retain(dict(name=platform,platform=platform,status='not_tested',detail=detail,retrieved_at=STAMP))
(OUT / 'environment.json').write_text(json.dumps({'python':sys.version,'feedparser':feedparser.__version__,'yt_dlp':subprocess.run([ytdlp,'--ignore-config','--version'],capture_output=True,text=True).stdout.strip()},indent=2))
print('Harness complete; inspect every results.json status. Output:', OUT)
