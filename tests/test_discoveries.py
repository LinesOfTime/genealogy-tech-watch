import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('discoveries', ROOT / 'tools/discoveries.py')
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        self.write('catalog.json', [dict(name='Friendly name', url='https://github.com/a/repo')])
        self.write('docs/research.json', {'a/repo': {'guide_excerpt': 'Preserve'}})
        self.write('digest.json', [])
        self.record = dict(discovery_id='event-1', repo_full_name='A/Repo',
                           canonical_url='https://github.com/A/Repo/', aliases=[],
                           detected_at='2026-10-22T10:00:00+03:00', event_date='2026-10-21',
                           event_type='release', source_urls=[dict(type='release',
                           url='https://github.com/a/repo/releases/tag/v2')],
                           change_summary='New API', previous_state='v1', new_state='v2',
                           significance_reason='New useful API', components=['API/MCP/agent layer'],
                           maturity='Unknown', license='Unknown', license_evidence=[],
                           claims_vs_verified='Author claim only', risks=['Untested'],
                           decision='publish', decision_reason='Useful API', review_status='pending',
                           reviewed_at=None, reviewer=None)

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data), encoding='utf-8')

    def check(self, records=None):
        return discovery.compare(self.root, records if records is not None else [self.record])

    def approve(self):
        import hashlib
        if isinstance(self.record.get('claims_vs_verified'),str):self.record['claims_vs_verified']=dict(verified='Synthetic fixture only',author_claims=self.record['claims_vs_verified'],independent_testing='Not performed')
        folder=self.root/'data/evidence';folder.mkdir(parents=True,exist_ok=True)
        self.record['source_checks']=[]
        for i,s in enumerate(self.record['source_urls']):
            stamp='2026-10-22T10:30:00+03:00'
            raw=json.dumps(dict(url=s['url'],checked_at=stamp,http_status=200,content='Synthetic test fixture, not real research evidence')).encode()
            name=f'data/evidence/source-{i}.json';(self.root/name).write_bytes(raw)
            self.record['source_checks'].append(dict(url=s['url'],checked_at=stamp,evidence_file=name,sha256=hashlib.sha256(raw).hexdigest(),verified_scope='Test fixture only'))
        self.record.update(review_status='approved', reviewer='Human reviewer',
                           reviewed_at='2026-10-22T11:00:00+03:00')
        self.record['reviewed_content_hash'] = discovery.content_hash(self.record)

    def test_pending_and_bound_approval(self):
        self.assertEqual(self.check()['eligible'], 0)
        self.approve()
        self.assertEqual(self.check()['eligible'], 1)
        self.record['new_state'] = 'Changed after approval'
        self.assertEqual(self.check()['eligible'], 0)

    def test_catalog_url_and_research_match(self):
        row = self.check()['results'][0]
        self.assertEqual(row['novelty_status'], 'material_update')
        self.assertEqual(row['research_matches'], ['a/repo'])

    def test_same_name_different_owner_is_new(self):
        self.record.update(repo_full_name='b/repo', canonical_url='https://github.com/b/repo')
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'new_project')

    def test_transfer_and_alias_conflict(self):
        self.record.update(repo_full_name='b/repo', canonical_url='https://github.com/b/repo',
                           aliases=['a/repo'])
        self.assertGreater(self.check()['errors'], 0)
        self.record['alias_evidence'] = ['https://github.com/b/repo/blob/main/README.md']
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'material_update')
        self.write('catalog.json', [dict(url='https://github.com/a/repo'),
                                   dict(url='https://github.com/b/repo')])
        self.approve()
        self.assertEqual(self.check()['eligible'], 0)

    def test_repeated_event_and_distinct_event_history(self):
        second = copy.deepcopy(self.record)
        second['discovery_id'] = 'event-2'
        self.assertEqual(self.check([self.record, second])['results'][1]['novelty_status'], 'duplicate')
        second['source_urls'][0]['url'] += '.1'
        second['change_summary'] = 'Different delta'
        self.assertEqual(self.check([self.record, second])['results'][1]['novelty_status'], 'material_update')

    def test_past_digest_duplicate(self):
        self.write('digest.json', [dict(date='2026-10-21', items=[dict(repo='a/repo',
                   change='Different wording', link=self.record['source_urls'][0]['url'])])])
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'duplicate')

    def test_cosmetic_and_no_delta_blocked(self):
        self.approve()
        self.record['event_type'] = 'cosmetic'
        self.record['reviewed_content_hash'] = discovery.content_hash(self.record)
        self.assertEqual(self.check()['eligible'], 0)
        self.record.update(event_type='release', new_state='v1')
        self.record['reviewed_content_hash'] = discovery.content_hash(self.record)
        self.assertEqual(self.check()['eligible'], 0)

    def test_invalid_partial_and_duplicate_ids(self):
        self.assertGreater(self.check([{}])['errors'], 0)
        self.assertGreater(self.check([self.record, self.record])['errors'], 0)

    def test_empty_idempotent_and_no_writes(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.check([])['candidates'], 0)
        self.assertEqual(self.check(), self.check())
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_jsonl_malformed_line(self):
        path = self.root / 'test.jsonl'
        path.write_text('{}\n[]\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, ':2:'):
            discovery.read_jsonl(path)

    def test_wrong_types_and_homepage_evidence_blocked(self):
        self.record.update(event_type=[], decision=[], review_status=[])
        self.assertGreater(self.check()['errors'], 0)
        self.record.update(event_type='release', decision='publish', review_status='pending',
                           source_urls=[dict(type='README', url='https://github.com/a/repo')])
        self.approve()
        self.assertEqual(self.check()['eligible'], 0)

    def test_duplicate_in_catalogue_history_without_digest(self):
        self.write('catalog.json', [dict(name='Friendly name', url='https://github.com/a/repo',
                   history=[dict(change='Other wording', url=self.record['source_urls'][0]['url'])])])
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'duplicate')

    def test_duplicate_in_research_watch_events(self):
        self.write('docs/research.json', {'a/repo': dict(watch_events=[dict(
            change='Other wording', source_urls=self.record['source_urls'])])})
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'duplicate')

    def test_digest_friendly_catalogue_name(self):
        self.write('digest.json', [dict(date='2026-10-21',items=[dict(repo='Friendly name',
                   change='New API',link='https://github.com/a/repo/releases/tag/v2')])])
        self.assertEqual(self.check()['results'][0]['novelty_status'], 'duplicate')


if __name__ == '__main__':
    unittest.main()
