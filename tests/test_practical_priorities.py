import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from practical_priorities import load_proposals
from priority_review import build


class PracticalPriorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT, prefix='.watch-e2e-priority-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        cards = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
        package = json.loads((ROOT / 'data/practical-priority-proposals.json').read_text(encoding='utf-8'))
        self.proposal = copy.deepcopy(package['projects'][0])
        self.cards = [copy.deepcopy(next(c for c in cards if c['name'] == self.proposal['project']))]
        self.cards[0].pop('practical_priority', None)  # synthetic pending review
        self.package = dict(version=1, status='pending', projects=[self.proposal])
        evidence = self.root / self.proposal['evidence_file']
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes((ROOT / self.proposal['evidence_file']).read_bytes())
        self.save()

    def save(self):
        path = self.root / 'data/practical-priority-proposals.json'
        path.write_text(json.dumps(self.package), encoding='utf-8')

    def reject(self):
        self.save()
        with self.assertRaises(ValueError):
            load_proposals(self.root, self.cards)

    def test_pending_proposal_preserves_active_priority_and_evaluation(self):
        before = copy.deepcopy(self.cards)
        proposals = load_proposals(self.root, self.cards)
        row = build(self.cards, {}, proposals=proposals)['projects'][0]
        self.assertEqual(row['legacy_priority'], before[0]['priority'])
        self.assertEqual(row['practical_proposal']['review_status'], 'pending')
        self.assertEqual(self.cards, before)

    def test_cannot_claim_approval_or_independent_test(self):
        for field, value in [('review_status', 'approved'), ('independent_test', True), ('evidence_level', 'E3')]:
            original = self.proposal[field]
            self.proposal[field] = value
            self.reject()
            self.proposal[field] = original

    def test_changed_baseline_requires_new_review(self):
        self.cards[0]['priority'] = 'P1'
        self.reject()

    def test_changed_evidence_is_rejected(self):
        with (self.root / self.proposal['evidence_file']).open('ab') as out:
            out.write(b' ')
        self.reject()

    def test_404_snapshot_cannot_support_proposal_even_with_new_hash(self):
        path = self.root / self.proposal['evidence_file']
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        snapshot['error'] = 'GitHub 404'
        raw = json.dumps(snapshot).encode()
        path.write_bytes(raw)
        self.proposal['evidence_sha256'] = hashlib.sha256(raw).hexdigest()
        self.reject()

    def test_duplicate_and_foreign_sources_rejected(self):
        self.package['projects'].append(copy.deepcopy(self.proposal))
        self.reject()
        self.package['projects'].pop()
        self.proposal['source_urls'][0] = 'https://github.com/other/project'
        self.reject()

    def test_newer_repository_404_blocks_old_readme(self):
        report = self.root / 'reports/priority-source-audit-2026-11-04.json'
        report.parent.mkdir()
        report.write_text(json.dumps([dict(url=self.cards[0]['url'], result='not_found',
            http_status=404, checked_on='2026-11-04', request_url='https://api.github.com/repos/a/b',
            response=dict(status='404'))]), encoding='utf-8')
        self.reject()

    def test_missing_license_supports_uncertainty_not_pilot_readiness(self):
        path = self.root / self.proposal['evidence_file']
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        snapshot['license']['kind'] = 'root_listing'
        snapshot['license']['content'] = '[]'
        raw = json.dumps(snapshot).encode()
        path.write_bytes(raw)
        self.proposal['evidence_sha256'] = hashlib.sha256(raw).hexdigest()
        self.proposal['proposed_priority'] = 'P1'
        self.reject()
        self.proposal['proposed_priority'] = 'Не оценён'
        self.save()
        self.assertEqual(len(load_proposals(self.root, self.cards)), 1)

    def test_full_review_covers_each_available_repository_once(self):
        cards = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
        audit = json.loads((ROOT / 'reports/priority-source-audit-2026-11-04.json').read_text(encoding='utf-8'))
        proposals = load_proposals(ROOT, cards)
        expected = {r['name'].lower() for r in audit if r['result'] == 'exists'}
        self.assertEqual(set(proposals), expected)
        self.assertEqual(len(audit) - len(proposals), 4)
        # A dated assessment stays immutable when later Watch cards are added.
        self.assertTrue({r['name'].lower() for r in audit}.issubset({c['name'].lower() for c in cards}))

    def test_dated_scope_allows_new_unrated_card_but_not_loss(self):
        cards = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(len(load_proposals(ROOT, cards + [dict(name='new/unrated', url='https://github.com/new/unrated')])), 180)
        with self.assertRaises(ValueError):
            load_proposals(ROOT, [c for c in cards if c['name'] != 'gramps-project/gramps'])

    def test_directory_listing_cannot_borrow_readme_evidence(self):
        path = self.root / self.proposal['evidence_file']
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        snapshot['document_kind'] = 'directory_listing'
        snapshot['content'] = '[]'
        raw = json.dumps(snapshot).encode()
        path.write_bytes(raw)
        self.proposal['evidence_sha256'] = hashlib.sha256(raw).hexdigest()
        self.proposal['proposed_priority'] = 'Не оценён'
        self.reject()
        self.proposal['evidence_level'] = 'E0'
        self.save()
        self.assertEqual(len(load_proposals(self.root, self.cards)), 1)


if __name__ == '__main__':
    unittest.main()
