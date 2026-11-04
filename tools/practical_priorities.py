"""Load pending, source-bound practical proposals; never apply or approve them."""
import hashlib
import json
import re


def merge_source_audit(root, checks):
    """Retain the historical audit; prefer the new, dated public check per URL."""
    path = root / 'reports/priority-source-audit-2026-11-04.json'
    if not path.exists():
        return checks
    records = {r['url'].lower().rstrip('/'): r for r in checks.get('records', [])}
    for row in json.loads(path.read_text(encoding='utf-8')):
        if row['result'] == 'exists':
            records[row['url'].lower().rstrip('/')] = dict(
                url=row['url'].lower().rstrip('/'), result='exists', http_status=200,
                checked_at=row['checked_on'])
        if row['result'] == 'not_found' and row.get('http_status') == 404:
            records[row['url'].lower().rstrip('/')] = dict(
                url=row['url'].lower().rstrip('/'), result='not_found', http_status=404,
                checked_at=row['checked_on'], request_url=row['request_url'], response=row['response'])
    return dict(records=list(records.values()))


def load_proposals(root, catalog):
    path = root / 'data/practical-priority-proposals.json'
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or data.get('status') != 'pending':
        raise ValueError('Practical proposals must remain pending until a separate approved migration')
    cards = {c['name'].lower(): c for c in catalog}
    unavailable = {r['url'].lower().rstrip('/') for r in merge_source_audit(root, {}).get('records', [])
                   if r['result'] == 'not_found'}
    result = {}
    for p in data['projects']:
        key = p['project'].lower()
        if key in result or key not in cards:
            raise ValueError('Duplicate or unknown practical proposal: ' + key)
        c = cards[key]
        if c['url'].lower().rstrip('/') in unavailable:
            raise ValueError('Repository has a newer 404 check: ' + key)
        expected = dict(priority=c.get('priority'), priority_original=c.get('priority_original'), evaluation=c.get('evaluation'))
        if p.get('previous') != expected:
            raise ValueError('Practical proposal baseline changed: ' + key)
        if p.get('review_status') != 'pending' or p.get('independent_test') is not False or p.get('evidence_level') not in ('E0', 'E1'):
            raise ValueError('Proposal cannot manufacture approval or independent testing: ' + key)
        if p.get('proposed_priority') not in ('P1', 'P2', 'P3', 'Не оценён'):
            raise ValueError('Invalid practical priority: ' + key)
        for field in ('role', 'task', 'scope', 'input_output', 'rationale', 'pilot', 'recheck_trigger'):
            if not isinstance(p.get(field), str) or not p[field].strip():
                raise ValueError('Missing practical proposal field: ' + field)
        evidence = (root / p['evidence_file']).resolve()
        directory = (root / 'data/evidence/priority-2026-11-04').resolve()
        if not evidence.is_relative_to(directory):
            raise ValueError('Evidence outside practical review directory')
        raw = evidence.read_bytes()
        if hashlib.sha256(raw).hexdigest() != p['evidence_sha256']:
            raise ValueError('Practical evidence changed: ' + key)
        snapshot = json.loads(raw)
        if snapshot.get('name') != c['name'] or snapshot.get('error') or not snapshot.get('content'):
            raise ValueError('Missing substantive source: ' + key)
        sha = snapshot.get('sha', '')
        if not re.fullmatch('[0-9a-f]{40}', sha):
            raise ValueError('Source version missing: ' + key)
        license = snapshot.get('license') or {}
        if snapshot.get('document_kind') == 'directory_listing':
            if p['evidence_level'] != 'E0' or p['proposed_priority'] != 'Не оценён':
                raise ValueError('Directory listing cannot establish project capabilities: ' + key)
        elif p['evidence_level'] != 'E1':
            raise ValueError('README review must remain E1: ' + key)
        if license.get('kind') == 'root_listing':
            if p['proposed_priority'] not in ('Не оценён', 'P3'):
                raise ValueError('Missing license terms cannot establish a runnable pilot: ' + key)
            if not isinstance(json.loads(license['content']), list):
                raise ValueError('Missing license inspection listing: ' + key)
        urls = [snapshot.get('url'), license.get('url')]
        prefix = 'https://api.github.com/repos/' + '/'.join(c['url'].rstrip('/').split('/')[-2:]) + '/contents'
        if (not license.get('content') or license.get('error') or p.get('source_urls') != urls
                or any(not (u.startswith(prefix + '/') or u.startswith(prefix + '?ref='))
                       or not u.endswith('?ref=' + sha) for u in urls)):
            raise ValueError('README and license must match repository and pinned version: ' + key)
        result[key] = p
    if 'coverage' in data:
        audit = json.loads((root / 'reports/priority-source-audit-2026-11-04.json').read_text(encoding='utf-8'))
        expected = {r['name'].lower() for r in audit if r['result'] == 'exists'}
        if set(result) != expected or {r['name'].lower() for r in audit} != set(cards):
            raise ValueError('Full practical review lost projects or reference issues')
        if data['coverage'] != dict(catalog=len(cards), reviewed_repositories=len(expected),
                                    reference_issues=len(cards) - len(expected)):
            raise ValueError('Full practical review coverage counts differ')
    return result
