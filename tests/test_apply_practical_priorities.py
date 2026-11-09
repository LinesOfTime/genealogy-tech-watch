import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from practical_priorities import load_proposals, package_hash
from apply_practical_priorities import build_plan
from apply_changes import write_plan


class ApplyPracticalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT, prefix='.watch-e2e-practical-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        p = json.loads((ROOT / 'data/practical-priority-proposals.json').read_text(encoding='utf-8'))['projects'][0]
        self.card = copy.deepcopy(next(c for c in json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8')) if c['name'] == p['project']))
        self.card.pop('practical_priority', None)
        self.package = dict(version=1, status='pending', projects=[p])
        self.put('catalog.json', [self.card])
        self.put('digest.json', [])
        profile = dict(marker='retained')
        if self.card.get('legal_notes'):
            profile['legal_notes'] = copy.deepcopy(self.card['legal_notes'])
        self.put('docs/research.json', {p['project'].lower(): profile})
        self.put('data/practical-priority-proposals.json', self.package)
        self.put('reports/priority-source-audit-2026-11-04.json', [dict(name=p['project'], url=self.card['url'], result='exists', checked_on='2026-11-04')])
        source = self.root / p['evidence_file']
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((ROOT / p['evidence_file']).read_bytes())
        for page in ('index', 'digest'):
            (self.root / 'docs' / (page + '.html')).write_text('<script id="seed" type="application/json">[]</script>', encoding='utf-8')
        self.approval = dict(status='approved', approved_by='Synthetic test reviewer',
            approved_at='2026-11-04T12:00:00+00:00', source_instruction='Publish synthetic fixture',
            package_hash=package_hash(self.package))

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def test_exact_package_apply_preserves_history_and_is_idempotent(self):
        before = copy.deepcopy(self.card)
        plan = build_plan(self.root, self.approval)
        self.assertEqual(json.loads((self.root / 'catalog.json').read_text(encoding='utf-8')), [before])
        write_plan(self.root, plan, plan['plan_hash'])
        card = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))[0]
        self.assertEqual({k: v for k, v in card.items() if k != 'practical_priority'}, before)
        self.assertEqual(card['practical_priority']['review_status'], 'approved')
        self.assertEqual(json.loads((self.root / 'docs/catalog.json').read_text(encoding='utf-8'))[0], card)
        self.assertEqual(build_plan(self.root, self.approval)['files'], {})

    def test_missing_or_stale_approval_never_writes(self):
        for change in ({'status': 'pending'}, {'package_hash': '0' * 64}, {'source_instruction': ''}):
            with self.assertRaises(ValueError):
                build_plan(self.root, {**self.approval, **change})
        self.assertFalse((self.root / 'data/practical-priority-application.json').exists())

    def test_applied_content_and_receipt_cannot_disappear(self):
        plan = build_plan(self.root, self.approval)
        write_plan(self.root, plan, plan['plan_hash'])
        card = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))[0]
        card['practical_priority']['priority'] = 'P1'
        self.put('catalog.json', [card])
        with self.assertRaises(ValueError):
            load_proposals(self.root, [card])
        (self.root / 'data/practical-priority-application.json').unlink()
        with self.assertRaises(ValueError):
            load_proposals(self.root, [card])


    def apply_watch_review(self, proposed="P1"):
        from apply_changes import build_plan as watch_plan, digest_bytes
        from discoveries import content_hash
        for field in ('classification', 'assessment_currency', 'russia_applicability'):
            self.card.pop(field, None)
        self.put('catalog.json', [self.card])
        self.put('docs/source-updates.json', dict(version=1, items=[]))
        plan = build_plan(self.root, self.approval)
        write_plan(self.root, plan, plan['plan_hash'])
        card = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))[0]
        stamp = '2026-11-05T12:00:00+00:00'
        url = card['url'] + '/commit/' + 'a' * 40
        evidence = 'data/evidence/updater/test-review/source.json'
        raw = json.dumps(dict(url=url, checked_at=stamp, http_status=200,
                              content='Synthetic fixture: new source editing capability.'))
        self.put(evidence, json.loads(raw))
        raw_bytes = (self.root / evidence).read_bytes()
        event = dict(discovery_id='synthetic-approved-review', repo_full_name=card['name'],
            canonical_url=card['url'], aliases=[], detected_at=stamp, event_date='2026-11-05',
            event_type='capability', source_urls=[dict(type='commit', url=url)],
            change_summary='Synthetic source editing update', previous_state='Old editor',
            new_state='New editor', significance_reason='Explicit new editing capability',
            components=['Research Workspace'], maturity='Synthetic fixture', license='MIT',
            license_evidence=[url], claims_vs_verified=dict(verified='Synthetic text saved',
                author_claims='Not a real research assertion', independent_testing='Not performed'),
            risks=['Synthetic test only'], decision='publish', decision_reason='Test approved update',
            review_status='approved', reviewer='Synthetic later reviewer', reviewed_at=stamp,
            priority_review=dict(previous=card['practical_priority']['priority'], proposed=proposed or card['practical_priority']['priority'],
                reason='Synthetic source-bound rationale', next_action='Test a source citation'),
            source_checks=[dict(url=url, checked_at=stamp, evidence_file=evidence,
                sha256=digest_bytes(raw_bytes), verified_scope='Synthetic source text only')])
        event['reviewed_content_hash'] = content_hash(event)
        plan = watch_plan(self.root, [event], '2026-11-05')
        write_plan(self.root, plan, plan['plan_hash'])
        return json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))[0], event

    def test_source_bound_watch_review_updates_catalog_and_research(self):
        card, event = self.apply_watch_review()
        result = load_proposals(self.root, [card])[card['name'].lower()]
        self.assertEqual(result['proposed_priority'], 'P1')
        self.assertEqual(card['practical_priority']['approved_by'], event['reviewer'])
        research = json.loads((self.root / 'docs/research.json').read_text(encoding='utf-8'))
        self.assertEqual(research[card['name'].lower()]['practical_priority'], card['practical_priority'])
        self.assertEqual(research[card['name'].lower()]['marker'], 'retained')

    def test_retaining_grade_still_records_a_source_bound_review(self):
        card, event = self.apply_watch_review(proposed=None)
        load_proposals(self.root, [card])
        self.assertEqual(event['priority_review']['previous'], event['priority_review']['proposed'])
        self.assertEqual(len(card['practical_priority_history']), 1)

    def test_reassessment_requires_original_approval_journal_ledger_and_evidence(self):
        card, event = self.apply_watch_review()
        paths = ['data/applied-events.json', 'data/discoveries.jsonl',
                 event['source_checks'][0]['evidence_file'], 'data/practical-priority-application.json']
        for name in paths:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(b'{}' if name.endswith('.json') else b'')
                try:
                    with self.assertRaises((ValueError, KeyError)):
                        load_proposals(self.root, [card])
                finally:
                    path.write_bytes(original)
        changed = copy.deepcopy(card)
        changed['practical_priority_history'][0]['reason'] = 'Unapproved assertion'
        with self.assertRaises(ValueError):
            load_proposals(self.root, [changed])
        changed = copy.deepcopy(card)
        changed['practical_priority']['priority'] = 'P3'
        with self.assertRaises(ValueError):
            load_proposals(self.root, [changed])


if __name__ == '__main__':
    unittest.main()
