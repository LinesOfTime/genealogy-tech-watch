"""Plan and apply reviewed events locally. Existing research text is append-only."""
import copy
from datetime import date
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote

from discoveries import compare, content_hash, repo_key, read_jsonl


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sync_payloads(root, catalog=None, digest=None):
    """Prepare all copies and seeds before writing any of them."""
    root = Path(root)
    output = {}
    for source, page, supplied in [('catalog', 'index', catalog), ('digest', 'digest', digest)]:
        raw = (root / (source + '.json')).read_bytes() if supplied is None else encoded(supplied)
        value = json.loads(raw)
        if not isinstance(value, list):
            raise ValueError(source + ' must be an array')
        output[source + '.json'] = raw
        output['docs/' + source + '.json'] = raw
        path = 'docs/' + page + '.html'
        html = (root / path).read_text(encoding='utf-8')
        pattern = r'(<script\b(?=[^>]*\bid=["\x27]seed["\x27])[^>]*>).*?(</script>)'
        if len(re.findall(pattern, html, re.S)) != 1:
            raise ValueError(path + ': expected exactly one seed')
        payload = json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
        output[path] = re.sub(pattern, lambda m: m[1] + payload + m[2], html, flags=re.S).encode('utf-8')
    return output


def build_plan(root, records, edition_date):
    root = Path(root)
    date.fromisoformat(edition_date)
    ledger_path = root / 'data/applied-events.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
    if not isinstance(ledger, dict):
        raise ValueError('Invalid applied-events ledger')
    pending, skipped = [], []
    for record in records:
        key = record.get('discovery_id')
        if isinstance(key, str) and key in ledger:
            if ledger[key] != content_hash(record):
                raise ValueError('Applied event changed: ' + key)
            skipped.append(key)
        else:
            pending.append(record)
    report = compare(root, pending)
    if report['errors']:
        raise ValueError('Candidate errors: ' + json.dumps(report['results'], ensure_ascii=False))
    selected = [(r, result) for r, result in zip(pending, report['results']) if result['eligible_for_apply']]
    if not selected:
        return dict(files={}, before={}, events=[], skipped=skipped, plan_hash=None, diff='')
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
    research = json.loads((root / 'docs/research.json').read_text(encoding='utf-8'))
    digest = json.loads((root / 'digest.json').read_text(encoding='utf-8'))
    items, event_ids = [], []
    touched = set()
    for r, result in selected:
        identity = repo_key(r['repo_full_name'])
        match = result['catalog_match']
        card = next((c for c in catalog if c['url'] in match), None)
        if card is None:
            # No inferred factual description, priority or license claim.
            card = dict(name=identity, url=r['canonical_url'], section='Новые исследования / GitHub Watch',
                        description=r['change_summary'], use_case='Не оценено', limitations='Не оценено',
                        license=r['license'], license_status='См. источники события; независимая проверка не заявлена',
                        priority='Не оценён', priority_original='Не оценён',
                        verification='Редакционная проверка источников события; см. историю', verified_at=r['event_date'],
                        test_status='Не тестировалось', source=r['source_urls'][0]['url'],
                        status='Дополнение из GitHub Watch', history=[], origin='GitHub Watch',
                        components=r['components'])
            profile = r.get('catalog_profile')
            if profile is not None:
                card['catalog_profile_provenance'] = dict(
                    previous_values={field: card.get(field) for field in profile},
                    source_urls=copy.deepcopy(r['source_urls']),
                    discovery_id=r['discovery_id'], reviewed_content_hash=r['reviewed_content_hash'],
                    basis='Редакционное описание по первоисточникам; не независимое испытание')
                card.update(copy.deepcopy(profile))
            catalog.append(card)
        target = card['url']
        if target in touched:
            raise ValueError('Multiple pending events for one card; apply separately: ' + target)
        touched.add(target)
        keys = result['research_matches']
        name_key = card['name'].lower()
        if len(keys) > 1 or (keys and keys[0] != name_key):
            raise ValueError('Research identity needs manual reconciliation: ' + identity)
        key = keys[0] if keys else name_key
        event = dict(discovery_id=r['discovery_id'], date=r['event_date'], change=r['change_summary'],
                     previous_state=r['previous_state'], new_state=r['new_state'],
                     significance_reason=r['significance_reason'], source_urls=r['source_urls'],
                     url=r['source_urls'][0]['url'], claims_vs_verified=r['claims_vs_verified'],
                     risks=r['risks'], license=r['license'], license_evidence=r['license_evidence'],
                     review_status='approved', reviewer=r['reviewer'], reviewed_at=r['reviewed_at'],
                     reviewed_content_hash=r['reviewed_content_hash'])
        card.setdefault('history', []).append(copy.deepcopy(event))
        research_created = key not in research
        research.setdefault(key, {}).setdefault('watch_events', []).append(copy.deepcopy(event))
        if research_created:
            from russia_applicability import derive
            assessment=derive(key,research[key])
            previous=card.get('russia_applicability')
            if previous is not None and previous!=assessment:
                card.setdefault('russia_applicability_history',[]).append(dict(
                    previous_value=copy.deepcopy(previous), discovery_id=r['discovery_id'],
                    reason='Создана расширенная карточка события; оценка применимости не добавлялась'))
            card['russia_applicability']=copy.deepcopy(assessment)
            research[key]['russia_applicability']=copy.deepcopy(assessment)
        item = dict(repo=card['name'], priority=card['priority'], change=r['change_summary'],
                          link=r['source_urls'][0]['url'], components=' · '.join(r['components']),
                          action=r['decision_reason'], event_date=r['event_date'],
                          significance_reason=r['significance_reason'], review_status='approved',
                          reviewer=r['reviewer'], reviewed_at=r['reviewed_at'],
                          discovery_id=r['discovery_id'], source_urls=r['source_urls'],
                          research_link='project.html?repo=' + quote(card['name'], safe=''),
                          previous_state=r['previous_state'], new_state=r['new_state'])
        if r['decision'] == 'publish':
            items.append(item)
        ledger[r['discovery_id']] = content_hash(r)
        event_ids.append(r['discovery_id'])
    edition = next((d for d in digest if d['date'] == edition_date), None)
    if items and edition is None:
        digest.insert(0, dict(date=edition_date, title='Значимые изменения проектов',
                              summary='Утверждённые события; источники и дельты указаны в записях.', items=items))
    elif items:
        edition['items'].extend(items)
    # Research-only events preserve digest bytes, including formatting.
    from repository_integrity import rejection_issues
    rejected=rejection_issues(root,catalog,research,digest)
    if rejected:raise ValueError('Rejected repository gate: '+str(rejected))
    files = sync_payloads(root, catalog, digest if items else None)
    files['docs/research.json'] = encoded(research)
    files['data/applied-events.json'] = encoded(ledger)
    journal_path = root / 'data/discoveries.jsonl'
    journal = read_jsonl(journal_path) if journal_path.exists() else []
    for record, _ in selected:
        matching = [i for i, old in enumerate(journal) if old.get('discovery_id') == record['discovery_id']]
        if len(matching) > 1:
            raise ValueError('Duplicate event in discovery journal: ' + record['discovery_id'])
        if matching:
            if content_hash(journal[matching[0]]) != content_hash(record):
                raise ValueError('Journal event content differs from reviewed input: ' + record['discovery_id'])
            journal[matching[0]] = copy.deepcopy(record)
        else:
            journal.append(copy.deepcopy(record))
    files['data/discoveries.jsonl'] = ('\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':'))
                                              for r in journal) + '\n').encode('utf-8')
    before = {name: (root / name).read_bytes() if (root / name).exists() else None for name in files}
    dependencies=['data/editorial-corrections.json','data/repository-rechecks.json']
    dependencies += [str(p.relative_to(root)).replace('\\','/') for p in (root/'data/evidence').glob('**/*') if p.is_file()]
    for name in dependencies:
        if name not in before:before[name]=(root/name).read_bytes() if (root/name).exists() else None
    files = {name: data for name, data in files.items() if data != before[name]}
    # Validate the complete proposed static snapshot, without touching live files.
    from watch_pipeline import validate
    with tempfile.TemporaryDirectory(prefix='.watch-validation-', dir=root) as temp:
        staging = Path(temp)
        for name, data in files.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in ('catalog.json', 'digest.json', 'docs/catalog.json', 'docs/digest.json',
                     'docs/research.json', 'docs/index.html', 'docs/digest.html'):
            if not (staging / name).exists():
                (staging / name).parent.mkdir(parents=True, exist_ok=True)
                (staging / name).write_bytes((root / name).read_bytes())
        for name in dependencies:
            if (root/name).exists() and not (staging/name).exists():
                (staging/name).parent.mkdir(parents=True,exist_ok=True)
                (staging/name).write_bytes((root/name).read_bytes())
        validation = validate(staging)
        if validation['errors']:
            raise ValueError('Proposed snapshot fails validation: ' + str(validation['issues']))
    manifest = {name: [digest_bytes(before[name]) if before[name] is not None else None,
                       digest_bytes(data)] for name, data in sorted(files.items())}
    for name in dependencies:
        if name not in manifest:manifest[name]=[digest_bytes(before[name]) if before[name] is not None else None]*2
    plan_hash = digest_bytes(encoded(manifest))
    diff = ''.join(''.join(difflib.unified_diff(
        (before[name] or b'').decode('utf-8').splitlines(True), data.decode('utf-8').splitlines(True),
        fromfile='a/' + name, tofile='b/' + name)) for name, data in files.items())
    return dict(files=files, before=before, events=event_ids, skipped=skipped,
                plan_hash=plan_hash, diff=diff)


def write_plan(root, plan, expected_hash):
    if not plan['files']:
        return
    if expected_hash != plan['plan_hash']:
        raise ValueError('Plan hash differs; inspect fresh dry-run before writing')
    root = Path(root)
    for name, old in plan['before'].items():
        current = (root / name).read_bytes() if (root / name).exists() else None
        if current != old:
            raise ValueError('Concurrent file change: ' + name)
    # Stage every replacement first. Roll back on ordinary write/replace failures.
    with tempfile.TemporaryDirectory(prefix='.watch-write-', dir=root) as temp:
        staged, completed = {}, []
        for index, (name, data) in enumerate(plan['files'].items()):
            path = Path(temp) / str(index)
            path.write_bytes(data)
            staged[name] = path
        try:
            for name, path in staged.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, root / name)
                completed.append(name)
        except OSError:
            for name in reversed(completed):
                old = plan['before'][name]
                if old is None:
                    (root / name).unlink()
                else:
                    (root / name).write_bytes(old)
            raise
