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
        self.put('docs/research.json', {p['project'].lower(): dict(marker='retained')})
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


if __name__ == '__main__':
    unittest.main()
