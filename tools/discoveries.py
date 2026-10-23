"""Offline candidate comparison. Review metadata never authorizes publication by itself."""
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
import re
from urllib.parse import urlsplit

COMPONENTS = {'Research Workspace', 'Archive Adapter', 'OCR/HTR', 'Indexer',
              'Person Resolver', 'Place Resolver/АТД', 'provenance/evidence',
              'GEDCOM/data model', 'API/MCP/agent layer'}
SOURCE_TYPES = {'release', 'commit', 'PR', 'README', 'ADR', 'paper', 'benchmark'}
MATERIAL_EVENTS = {'new_project', 'release', 'architecture', 'api', 'benchmark', 'license', 'capability'}
DECISIONS = {'publish', 'research_only', 'watch', 'reject'}


def repo_key(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if '://' in value:
        try:
            p = urlsplit(value)
            if p.scheme != 'https' or p.netloc.lower() not in ('github.com', 'www.github.com'):
                return None
            value = p.path
        except ValueError:
            return None
    value = re.sub(r'\.git$', '', value.strip('/'), flags=re.I)
    return value.lower() if re.fullmatch(r'[\w.-]+/[\w.-]+', value, re.ASCII) else None


def read_jsonl(path):
    records = []
    for line, text in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        if text.strip():
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f'{path}:{line}: expected object')
            records.append(value)
    return records


def content_hash(record):
    # Approval is bound to the entire submitted evidence/decision, excluding review fields.
    content = {k: v for k, v in record.items()
               if k not in {'review_status', 'reviewed_at', 'reviewer', 'reviewed_content_hash'}}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def http_url(value):
    try:
        p = urlsplit(value)
        return p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password
    except (ValueError, TypeError, AttributeError):
        return False


def compare(root, records):
    root = Path(root)
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
    research = json.loads((root / 'docs/research.json').read_text(encoding='utf-8'))
    digest = json.loads((root / 'digest.json').read_text(encoding='utf-8'))
    results, ids, prior = [], set(), []
    for r in records:
        errors = []
        identity = repo_key(r.get('repo_full_name'))
        if not identity or repo_key(r.get('canonical_url')) != identity:
            errors.append('repo_full_name/canonical_url must identify the same GitHub repository')
        aliases = r.get('aliases', [])
        if not isinstance(aliases, list) or any(not repo_key(a) for a in aliases):
            errors.append('aliases must be repository names or URLs')
            aliases = []
        # Aliases are explicit assertions requiring source-backed human review.
        identities = {identity} | {repo_key(a) for a in aliases}
        alias_evidence = r.get('alias_evidence')
        if aliases and (not isinstance(alias_evidence, list) or not alias_evidence or
                        any(not http_url(s) for s in alias_evidence)):
            errors.append('repository transfer/alias requires alias_evidence')
        discovery_id = r.get('discovery_id')
        if not isinstance(discovery_id, str) or not discovery_id.strip() or discovery_id in ids:
            errors.append('missing or duplicate discovery_id')
        if isinstance(discovery_id, str):
            ids.add(discovery_id)
        for field in ('change_summary', 'previous_state', 'new_state', 'significance_reason',
                      'decision_reason', 'maturity', 'license'):
            if not isinstance(r.get(field), str) or not r[field].strip():
                errors.append('missing text: ' + field)
        for field in ('license_evidence', 'claims_vs_verified', 'risks'):
            if field not in r:
                errors.append('missing field: ' + field)
        for field in ('event_date', 'detected_at'):
            try:
                if field == 'event_date':
                    date.fromisoformat(r[field])
                else:
                    stamp = datetime.fromisoformat(r[field].replace('Z', '+00:00'))
                    if stamp.tzinfo is None:
                        raise ValueError('timezone required')
            except (KeyError, TypeError, ValueError, AttributeError):
                errors.append('invalid date: ' + field)
        components = r.get('components')
        if not isinstance(components, list) or not components or any(
                not isinstance(c, str) or c not in COMPONENTS for c in components):
            errors.append('invalid controlled components')
        sources = r.get('source_urls')
        if not isinstance(sources, list) or not sources or any(
                not isinstance(s, dict) or not isinstance(s.get('type'), str) or s.get('type') not in SOURCE_TYPES or
                not http_url(s.get('url')) for s in sources):
            errors.append('source_urls requires typed HTTPS evidence')
            sources = []
        if not isinstance(r.get('decision'), str) or r.get('decision') not in DECISIONS:
            errors.append('invalid decision')
        if not isinstance(r.get('review_status'), str) or r.get('review_status') not in {'pending', 'approved', 'rejected'}:
            errors.append('invalid review_status')
        matches = [c['url'] for c in catalog if repo_key(c.get('url')) in identities]
        matched_names = {c['name'].lower() for c in catalog if c.get('url') in matches and isinstance(c.get('name'), str)}
        research_matches = [k for k in research if repo_key(k) in identities or k in matched_names]
        history = [dict(date=d['date'], **item) for d in digest for item in d['items']
                   if repo_key(item.get('repo')) in identities or str(item.get('repo', '')).lower() in matched_names]
        catalogue_events = [event for c in catalog if c.get('url') in matches for event in c.get('history', [])]
        research_events = [event for key in research_matches for event in research[key].get('watch_events', [])]
        links = {s['url'].rstrip('/') for s in sources}
        delta = str(r.get('change_summary', '')).strip().casefold()
        def repeated(event):
            event_links = {str(event.get('link', event.get('url', ''))).rstrip('/')}
            event_links.update(s['url'].rstrip('/') for s in event.get('source_urls', [])
                               if isinstance(s, dict) and isinstance(s.get('url'), str))
            return (str(event.get('change', '')).strip().casefold() == delta or
                    bool(event_links & links) or
                    (bool(discovery_id) and event.get('discovery_id') == discovery_id))
        duplicate = any(repeated(event) for event in history + catalogue_events + research_events)
        duplicate |= any(identities & keys and (delta == old_delta or bool(links & old_links))
                         for keys, old_delta, old_links in prior)
        prior.append((identities, delta, links))
        event_type = r.get('event_type')
        material = isinstance(event_type, str) and event_type in MATERIAL_EVENTS and bool(r.get('significance_reason'))
        if not isinstance(event_type, str) or not event_type.strip():
            errors.append('missing event_type')
        specific_sources = [s for s in sources if
                            re.search(r'/(commit|pull|releases|blob)/', s['url']) or
                            (urlsplit(s['url']).hostname not in ('github.com', 'www.github.com') and
                             urlsplit(s['url']).path.strip('/'))]
        if r.get('decision') == 'publish' and not specific_sources:
            errors.append('publish needs a specific primary-source URL, not a repository homepage')
        changed = r.get('previous_state') != r.get('new_state')
        if duplicate:
            novelty = 'duplicate'
        elif errors:
            novelty = 'insufficient_evidence'
        elif not changed or not material:
            novelty = 'known_unchanged' if matches or research_matches or history else 'insufficient_evidence'
        else:
            novelty = 'material_update' if matches or research_matches or history else 'new_project'
        if len(matches) > 1:
            errors.append('identity conflict: aliases match multiple catalogue cards')
        approved = r.get('review_status') == 'approved'
        if approved:
            from source_evidence import evidence_errors
            errors.extend(evidence_errors(root,r))
            if not isinstance(r.get('reviewer'), str) or not r['reviewer'].strip():
                errors.append('approved record needs reviewer')
            try:
                stamp = datetime.fromisoformat(r['reviewed_at'].replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    raise ValueError('timezone required')
            except (KeyError, TypeError, ValueError, AttributeError):
                errors.append('approved record needs timestamp with timezone')
            if r.get('reviewed_content_hash') != content_hash(r):
                errors.append('approval missing or stale: reviewed_content_hash differs')
        eligible = not errors and approved and r.get('decision') in ('publish', 'research_only') and novelty in {
            'new_project', 'material_update'}
        results.append(dict(discovery_id=discovery_id, catalog_match=matches,
                            research_matches=research_matches, previous_digest_matches=history,
                            previous_catalog_events=catalogue_events, previous_research_events=research_events,
                            novelty_status=novelty, eligible_for_apply=eligible,
                            content_hash=content_hash(r), errors=errors))
    return dict(candidates=len(records), eligible=sum(x['eligible_for_apply'] for x in results),
                errors=sum(len(x['errors']) for x in results), results=results,
                mode='offline dry-run; evidence URLs have not been fetched or verified')
