#!/usr/bin/env python3
"""Read-only GitHub metadata audit for every repository card in catalog.json.

Metadata is a screening signal, not independent verification of software quality.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

# Verified project homepage; a replacement URL is a review suggestion, not an automatic edit.
KNOWN_RELOCATIONS = {
    'scripta/escriptorium': 'https://gitlab.com/scripta/escriptorium',
}



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


def screening(card, metadata, checked_at):
    """Prioritize manual inspection; activity is NOT evidence of material changes."""
    if metadata.get('resolution') == 'known_external_repository_candidate':
        return 'repository_url_correction_candidate'
    if metadata.get('resolution') == 'repository_not_found_needs_review':
        return 'repository_not_found_review'
    if metadata.get('status') != 'ok':
        return 'unverified'
    if metadata.get('archived') or metadata.get('disabled'):
        return 'repository_status_change_candidate'
    pushed = metadata.get('pushed_at')
    if not pushed:
        return 'unknown_activity'
    try:
        last_push = datetime.fromisoformat(pushed.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return 'unknown_activity'
    if last_push > checked_at + timedelta(days=1):
        return 'invalid_future_timestamp'
    history = card.get('history') or []
    latest = max((event.get('date', '')[:10] for event in history
                  if isinstance(event, dict) and isinstance(event.get('date'), str)), default='')
    if latest:
        try:
            review_day = datetime.fromisoformat(latest).replace(tzinfo=timezone.utc)
            if last_push > review_day + timedelta(days=1):
                return 'activity_after_catalog_event'
        except ValueError:
            pass
    if last_push >= checked_at - timedelta(days=30):
        return 'recent_activity_review'
    return 'no_recent_activity_signal'


def inspect(cards, fetch, pause=0, checked_at=None):
    checked_at = checked_at or datetime.now(timezone.utc)
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
                if 'HTTP 404' in data['_error']:
                    row['resolution'] = 'repository_not_found_needs_review'
                if repo in KNOWN_RELOCATIONS and '404' in data['_error']:
                    row['suggested_url'] = KNOWN_RELOCATIONS[repo]
                    row['resolution'] = 'known_external_repository_candidate'
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
        row['screening'] = screening(card, row, checked_at)
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
    priority_order = {'repository_not_found_review': 0,
                      'repository_url_correction_candidate': 1,
                      'repository_status_change_candidate': 2,
                      'activity_after_catalog_event': 3,
                      'recent_activity_review': 4,
                      'invalid_future_timestamp': 5,
                      'unknown_activity': 6,
                      'unverified': 7}
    candidates = [item for item in items if item['screening'] in priority_order]
    candidates.sort(key=lambda item: (priority_order[item['screening']], str(item['name'])))
    summary = dict(Counter(item['status'] for item in items))
    screening_counts = dict(Counter(item['screening'] for item in items))
    report = {'checked_at': datetime.now(timezone.utc).isoformat(),
              'catalog_count': len(cards), 'status_counts': summary,
              'screening_counts': screening_counts,
              'candidate_count': len(candidates), 'candidates': candidates,
              'items': items,
              'limitations': 'Activity screening only. Pushed-at timestamps and archived flags do not establish a substantive release, change, or quality. Inspect source commits, README, release notes, license and tests before updating cards.'}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'catalog_count': len(cards), 'status_counts': summary, 'screening_counts': screening_counts}, ensure_ascii=False))
    unresolved = [item for item in items if item['status'] in ('request_failed', 'invalid_response')
                  and item.get('resolution') != 'known_external_repository_candidate']
    # A missing repository is a review task, not an infrastructure failure.
    # Keep the run red for transport failures and invalid API responses only.
    infrastructure_errors = [item for item in unresolved
                             if item.get('resolution') != 'repository_not_found_needs_review']
    if infrastructure_errors:
        raise SystemExit(str(len(infrastructure_errors)) + ' API checks failed; inspect the report.')
    if unresolved:
        print(str(len(unresolved)) + ' repository URLs need manual review.')


if __name__ == '__main__':
    main()
