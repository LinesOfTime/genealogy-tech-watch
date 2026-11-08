#!/usr/bin/env python3
"""Read-only GitHub metadata audit for every repository card in catalog.json.

Metadata is a screening signal, not independent verification of software quality.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def repository_name(url):
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.hostname not in ('github.com', 'www.github.com'):
        return None
    parts = [p for p in parsed.path.strip('/').split('/') if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[:2]
    if repo.endswith('.git'):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return owner + '/' + repo


def inspect(cards, fetch, pause=0):
    items = []
    cache = {}
    for card in cards:
        name = card.get('name')
        url = card.get('url')
        repo = repository_name(url)
        row = {'name': name, 'url': url, 'repository': repo}
        if not repo:
            row['status'] = 'not_github_repository'
        else:
            if repo not in cache:
                try:
                    cache[repo] = fetch(repo)
                except Exception as exc:
                    cache[repo] = {'_error': str(exc)}
                if pause:
                    time.sleep(pause)
            data = cache[repo]
            if '_error' in data:
                row.update(status='request_failed', error=data['_error'])
            elif not isinstance(data, dict):
                row.update(status='invalid_response')
            else:
                license_info = data.get('license')
                row.update(
                    status='ok',
                    archived=data.get('archived'),
                    disabled=data.get('disabled'),
                    pushed_at=data.get('pushed_at'),
                    updated_at=data.get('updated_at'),
                    default_branch=data.get('default_branch'),
                    open_issues_count=data.get('open_issues_count'),
                    license_spdx=(license_info.get('spdx_id') if isinstance(license_info, dict) else None),
                    github_url=data.get('html_url'),
                )
        items.append(row)
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, default=ROOT / 'catalog.json')
    parser.add_argument('--output', type=Path, default=Path('github-metadata-audit.json'))
    parser.add_argument('--pause', type=float, default=0.1)
    args = parser.parse_args()
    cards = json.loads(args.catalog.read_text(encoding='utf-8'))
    token = os.environ.get('GITHUB_TOKEN', '')
    def fetch(repo):
        request = Request(
            'https://api.github.com/repos/' + quote(repo, safe='/'),
            headers={'Accept': 'application/vnd.github+json',
                     'User-Agent': 'genealogy-tech-watch-audit',
                     **({'Authorization': 'Bearer ' + token} if token else {})})
        try:
            with urlopen(request, timeout=12) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError('HTTP ' + str(exc.code)) from exc
        except URLError as exc:
            raise RuntimeError('network error: ' + str(exc.reason)) from exc
    items = inspect(cards, fetch, args.pause)
    summary = dict(Counter(item['status'] for item in items))
    report = {'checked_at': datetime.now(timezone.utc).isoformat(),
              'catalog_count': len(cards), 'status_counts': summary,
              'items': items,
              'limitations': 'GitHub repository metadata only; no releases, README, license text, quality or compatibility verified.'}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'catalog_count': len(cards), 'status_counts': summary}, ensure_ascii=False))
    if summary.get('request_failed') or summary.get('invalid_response'):
        raise SystemExit('Some requests failed; inspect the report before using it.')


if __name__ == '__main__':
    main()
