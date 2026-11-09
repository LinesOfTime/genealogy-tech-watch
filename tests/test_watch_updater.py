import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

import test_apply_changes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from apply_changes import digest_bytes, encoded, write_plan
from catalog_model import MODEL_FILES
from discoveries import read_jsonl
from watch_pipeline import validate
from watch_updater import authorize, load_package, prepare


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        fixture = test_apply_changes.ApplyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        (self.root / 'data/discoveries.jsonl').write_bytes(b'')
        event = copy.deepcopy(fixture.record)
        for field in ('reviewed_at', 'reviewer', 'reviewed_content_hash'):
            del event[field]
        event.update(review_status='pending', event_type='new_project',
                     repo_full_name='b/new', canonical_url='https://github.com/b/new',
                     preliminary_priority='P2', initialize_research_profile=True,
                     catalog_profile=dict(description='Purpose', use_case='Use',
                                          limitations='Untested', project_type='CLI'))
        path = 'data/evidence/updater/test/source.json'
        url = 'https://github.com/b/new/releases/tag/v2'
        check = event['source_checks'][0]
        snapshot = json.dumps(dict(url=url, checked_at=check['checked_at'],
                                   http_status=200, content='Synthetic fixture'))
        check.update(url=url, evidence_file=path, sha256=digest_bytes(snapshot.encode()))
        event['source_urls'][0]['url'] = url
        self.packet = dict(version=1, edition_date='2026-10-22', events=[event],
                           evidence={path: snapshot})
        self.stamp = datetime.now(timezone.utc).isoformat()

    def test_preview_approval_and_apply_preserve_history(self):
        before = (self.root / 'catalog.json').read_bytes()
        raw = encoded(self.packet)
        packet, preview, key = prepare(self.root, raw, 'base')
        self.assertIn('b/new', preview['diff'])
        self.assertEqual(before, (self.root / 'catalog.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Approval hash'):
            authorize(self.root, packet, key, 'wrong', 'editor', self.stamp)
        plan = authorize(self.root, packet, key, key, 'editor', self.stamp)
        write_plan(self.root, plan, plan['plan_hash'])
        old, added = json.loads((self.root / 'catalog.json').read_bytes())
        self.assertEqual(old, json.loads(before)[0])
        self.assertEqual(added['priority'], 'P2')
        self.assertEqual(added['preliminary_priority'], 'P2')
        records = read_jsonl(self.root / 'data/discoveries.jsonl')
        self.assertEqual(records[0]['reviewer'], 'GitHub @editor')
        self.assertEqual(validate(self.root)['errors'], 0)
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            prepare(self.root, raw, 'base')

    def test_classified_catalog_accepts_new_project_and_counts_review_once(self):
        for name in MODEL_FILES[:3]:
            (self.root / name).write_bytes(encoded({'projects': {}}))
        packet, _, key = prepare(self.root, encoded(self.packet), 'base')
        plan = authorize(self.root, packet, key, key, 'editor', self.stamp)
        write_plan(self.root, plan, plan['plan_hash'])
        card = json.loads((self.root / 'catalog.json').read_bytes())[-1]
        self.assertEqual(card['classification']['primary_type'], 'unknown')
        self.assertEqual(len(card['assessment_currency']['sources']), 1)
        self.assertEqual(validate(self.root)['errors'], 0)

    def test_existing_project_requires_priority_review_even_if_unchanged(self):
        event = self.packet['events'][0]
        event.update(repo_full_name='a/repo', canonical_url='https://github.com/a/repo',
                     event_type='release')
        for key in ('preliminary_priority', 'initialize_research_profile', 'catalog_profile'):
            del event[key]
        with self.assertRaisesRegex(ValueError, 'requires priority_review'):
            prepare(self.root, encoded(self.packet), 'base')
        event['priority_review'] = dict(previous='P2', proposed='P2',
                                        reason='New release does not change pilot readiness',
                                        next_action='Test API on a small sample')
        packet, preview, key = prepare(self.root, encoded(self.packet), 'base')
        plan = authorize(self.root, packet, key, key, 'editor', self.stamp)
        write_plan(self.root, plan, plan['plan_hash'])
        card = json.loads((self.root / 'catalog.json').read_text())[0]
        self.assertEqual(card['practical_priority'], 'P2')
        self.assertEqual(card['practical_priority_history'][-1]['proposed'], 'P2')
        self.assertEqual(card['practical_priority_next_action'], 'Test API on a small sample')

    def test_hash_binds_base_and_exact_package(self):
        raw = encoded(self.packet)
        hashes = []
        for base, value in [('base', raw), ('new-base', raw), ('base', raw + b' ')]:
            hashes.append(prepare(self.root, value, base)[2])
            for name in self.packet['evidence']:
                (self.root / name).unlink()
        self.assertEqual(len(set(hashes)), 3)

    def test_refuses_forged_approval_and_duplicate_repository(self):
        event = self.packet['events'][0]
        event['reviewer'] = 'forged'
        with self.assertRaisesRegex(ValueError, 'pending events'):
            load_package(encoded(self.packet))
        del event['reviewer']
        self.packet['events'].append(dict(event, discovery_id='another', canonical_url='https://github.com/B/New.git'))
        with self.assertRaisesRegex(ValueError, 'distinct repository'):
            load_package(encoded(self.packet))

    def test_refuses_bad_json_evidence_paths_and_hashes(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            load_package(b'{"version":1,"version":2}')
        check = self.packet['events'][0]['source_checks'][0]
        path = check['evidence_file']
        check['evidence_file'] = 'data/evidence/updater/../forged.json'
        with self.assertRaisesRegex(ValueError, 'evidence path'):
            load_package(encoded(self.packet))
        check['evidence_file'] = path
        self.packet['evidence'][path] += ' '
        with self.assertRaisesRegex(ValueError, 'Evidence bytes/hash differ'):
            prepare(self.root, encoded(self.packet), 'base')

    def test_refuses_new_project_if_catalog_already_has_it(self):
        event = self.packet['events'][0]
        event.update(repo_full_name='A/Repo', canonical_url='https://github.com/A/Repo.git')
        del event['catalog_profile'], event['preliminary_priority'], event['initialize_research_profile']
        with self.assertRaisesRegex(ValueError, 'material_update'):
            prepare(self.root, encoded(self.packet), 'base')
