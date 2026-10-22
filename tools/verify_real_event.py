"""Verify a real applied event or exercise a pending event in a disposable snapshot."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from apply_changes import build_plan, encoded, write_plan, digest_bytes
from discoveries import compare, content_hash, read_jsonl
from watch_pipeline import validate


def snapshot(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def verify_applied(root, candidate, baseline=None):
    """Read-only verification of the actual applied record, including repeated/empty plans."""
    ledger = json.loads((root/'data/applied-events.json').read_text(encoding='utf-8'))
    discovery_id = candidate['discovery_id']
    assert candidate['review_status'] == 'approved'
    assert ledger[discovery_id] == content_hash(candidate) == candidate['reviewed_content_hash']
    names = ['catalog.json','digest.json','docs/catalog.json','docs/digest.json',
             'docs/research.json','docs/index.html','docs/digest.html',
             'data/applied-events.json','data/discoveries.jsonl']
    before = {name:(root/name).read_bytes() for name in names}
    catalog = json.loads(before['catalog.json'])
    research = json.loads(before['docs/research.json'])
    digest = json.loads(before['digest.json'])
    history = [event for card in catalog for event in card.get('history', [])
               if event.get('discovery_id') == discovery_id]
    extended = [event for card in research.values() for event in card.get('watch_events', [])
                if event.get('discovery_id') == discovery_id]
    items = [item for day in digest for item in day['items'] if item.get('discovery_id') == discovery_id]
    assert len(history) == len(extended) == len(items) == 1
    assert history[0] == extended[0]
    for event in history + extended + items:
        assert event['reviewer'] == candidate['reviewer']
        assert event['reviewed_at'] == candidate['reviewed_at']
        assert event['review_status'] == 'approved'
        assert candidate['source_urls'] == event['source_urls']
    assert history[0]['reviewed_content_hash'] == content_hash(candidate)
    assert not build_plan(root, [candidate], '2026-10-22')['files']
    assert not build_plan(root, [], '2026-10-22')['files']
    report = validate(root)
    assert report['errors'] == 0
    preserved = None
    baseline_hash = None
    if baseline:
        raw = Path(baseline).read_bytes()
        old = json.loads(raw)
        baseline_hash = digest_bytes(raw)
        cleaned_catalog = copy.deepcopy(catalog)
        for card in cleaned_catalog:
            card['history'] = [e for e in card.get('history', []) if e.get('discovery_id') != discovery_id]
        assert cleaned_catalog == old['catalog.json'] == old['docs/catalog.json']
        cleaned_research = copy.deepcopy(research)
        for key, card in cleaned_research.items():
            if 'watch_events' in card:
                card['watch_events'] = [e for e in card['watch_events'] if e.get('discovery_id') != discovery_id]
                if not card['watch_events'] and 'watch_events' not in old['docs/research.json'][key]:
                    del card['watch_events']
        assert cleaned_research == old['docs/research.json']
        assert digest[1:] == old['digest.json'] == old['docs/digest.json']
        assert len(digest[0]['items']) == 1
        preserved = True
    ui = subprocess.run(['node',str(root/'tests/ui_smoke.cjs'),str(root)], capture_output=True,
                        text=True,encoding='utf-8',check=True)
    assert before == {name:(root/name).read_bytes() for name in names}
    return dict(mode='Read-only verification of actual local application; no publication',
                discovery_id=discovery_id, production_review_status=candidate['review_status'],
                candidate_hash=content_hash(candidate), reviewer=candidate['reviewer'],
                reviewed_at=candidate['reviewed_at'], baseline_hash=baseline_hash,
                counts=dict(catalog=len(catalog),research=len(research),editions=len(digest),
                            events=sum(len(d['items']) for d in digest)),
                validation_errors=report['errors'],validation_warnings=report['warnings'],
                checks=dict(single_event_in_each_store=True,review_metadata_consistent=True,
                            idempotent=True,empty_run_unchanged=True,verification_read_only=True,
                            previous_data_preserved=preserved),ui_smoke=ui.stdout.strip())


def verify(root, discovery_id, baseline=None):
    root = Path(root)
    records = read_jsonl(root / 'data/discoveries.jsonl')
    candidates = [r for r in records if r['discovery_id'] == discovery_id]
    if len(candidates) != 1:
        raise ValueError('Expected one candidate')
    candidate = candidates[0]
    ledger_path = root/'data/applied-events.json'
    if ledger_path.exists() and discovery_id in json.loads(ledger_path.read_text(encoding='utf-8')):
        return verify_applied(root,candidate,baseline)
    production_files = ['catalog.json', 'digest.json', 'docs/catalog.json', 'docs/digest.json',
                        'docs/research.json', 'docs/index.html', 'docs/digest.html', 'data/discoveries.jsonl']
    original = {n:(root/n).read_bytes() for n in production_files}
    scan = compare(root, [candidate])
    if scan['errors'] or scan['results'][0]['novelty_status'] not in ('new_project','material_update'):
        raise ValueError('Real candidate is not a valid novel event')
    with tempfile.TemporaryDirectory(prefix='.watch-e2e-', dir=root) as temporary:
        staging = Path(temporary)
        for name in ['catalog.json','digest.json']:
            shutil.copyfile(root/name, staging/name)
        shutil.copytree(root/'docs', staging/'docs')
        before = snapshot(staging)
        pending_plan = build_plan(staging, [candidate], '2026-10-22')
        assert not pending_plan['files'], 'Pending record must not write anything'
        # Test approval exists only in this disposable in-memory scenario. It is not a human review.
        simulation = copy.deepcopy(candidate)
        simulation.update(review_status='approved', reviewer='SIMULATION ONLY — not human approval',
                          reviewed_at='2026-10-22T09:08:56Z')
        simulation['reviewed_content_hash'] = content_hash(simulation)
        plan = build_plan(staging, [simulation], '2026-10-22')
        assert plan['events'] == [discovery_id]
        assert before == snapshot(staging), 'Dry-run changed files'
        write_plan(staging, plan, plan['plan_hash'])
        first = snapshot(staging)
        repeated = build_plan(staging, [simulation], '2026-10-22')
        assert not repeated['files'], 'Repeated application is not idempotent'
        empty = build_plan(staging, [], '2026-10-22')
        assert not empty['files']
        assert first == snapshot(staging), 'Repeated/empty run changed files'
        report = validate(staging)
        assert report['errors'] == 0, report['issues']
        old_catalog = json.loads(original['catalog.json'])
        new_catalog = json.loads((staging/'catalog.json').read_text(encoding='utf-8'))
        target = scan['results'][0]['catalog_match'][0]
        for old, new in zip(old_catalog, new_catalog):
            if old['url'] == target:
                assert new['history'][:-1] == old['history']
                assert {k:v for k,v in new.items() if k!='history'} == {k:v for k,v in old.items() if k!='history'}
            else:
                assert old == new
        old_research = json.loads(original['docs/research.json'])
        new_research = json.loads((staging/'docs/research.json').read_text(encoding='utf-8'))
        key = scan['results'][0]['research_matches'][0]
        for k, old in old_research.items():
            if k == key:
                assert {f:v for f,v in new_research[k].items() if f!='watch_events'} == {f:v for f,v in old.items() if f!='watch_events'}
                assert new_research[k]['watch_events'][:-1] == old.get('watch_events', [])
            else:
                assert new_research[k] == old
        new_digest = json.loads((staging/'digest.json').read_text(encoding='utf-8'))
        assert new_digest[1:] == json.loads(original['digest.json'])
        assert new_digest[0]['items'][0]['discovery_id'] == discovery_id
        ui = subprocess.run(['node', str(root/'tests/ui_smoke.cjs'), str(staging)],
                            capture_output=True, text=True, encoding='utf-8', check=True)
        proposed = dict(catalog_history_added=new_catalog[next(i for i,c in enumerate(new_catalog) if c['url']==target)]['history'][-1],
                        research_watch_event_added=new_research[key]['watch_events'][-1],
                        digest_edition_added=new_digest[0])
        output = dict(discovery_id=discovery_id, production_review_status=candidate['review_status'],
                      mode='Disposable integration simulation; no production approval or apply',
                      candidate_hash=content_hash(candidate), novelty_status=scan['results'][0]['novelty_status'],
                      planned_files=list(plan['files']),
                      plan_hash_simulation_only=plan['plan_hash'],
                      validation_errors=report['errors'], validation_warnings=report['warnings'],
                      checks=dict(pending_blocked=True, dry_run_read_only=True, idempotent=True,
                                  empty_run_unchanged=True, previous_data_preserved=True),
                      ui_smoke=ui.stdout.strip(), proposed_changes_simulation_only=proposed)
    assert original == {n:(root/n).read_bytes() for n in production_files}, 'Production data changed'
    output['checks']['production_unchanged'] = True
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--discovery-id', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, help='Pre-application JSON snapshot for preservation verification')
    args = parser.parse_args()
    result = verify(args.root, args.discovery_id, args.baseline)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encoded(result))
    print(json.dumps({k:v for k,v in result.items() if k!='proposed_changes_simulation_only'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
