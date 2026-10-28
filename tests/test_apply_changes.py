import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from apply_changes import build_plan, write_plan, sync_payloads
from discoveries import content_hash


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        self.card = dict(name='a/repo', url='https://github.com/a/repo', section='Test',
                         description='Original', priority='P2', priority_original='B',
                         history=[dict(date='2026-10-01', change='Original history')], license='Original license')
        self.research = {'a/repo': dict(guide_excerpt='Для России: Высокий',
                                      editorial_summary='Original research', custom=['Preserve'])}
        for name, value in [('catalog', [self.card]), ('digest', [])]:
            text = json.dumps(value)
            (self.root / (name + '.json')).write_text(text, encoding='utf-8')
            (self.root / 'docs' / (name + '.json')).write_text(text, encoding='utf-8')
            page = 'index' if name == 'catalog' else 'digest'
            (self.root / 'docs' / (page + '.html')).write_text(
                '<script id="seed" type="application/json">' + text + '</script>', encoding='utf-8')
        self.write('docs/research.json', self.research)
        self.record = dict(discovery_id='test-event', repo_full_name='a/repo',
                           canonical_url='https://github.com/a/repo', aliases=[],
                           detected_at='2026-10-22T10:00:00+03:00', event_date='2026-10-21',
                           event_type='release', source_urls=[dict(type='release',
                           url='https://github.com/a/repo/releases/tag/v2')],
                           change_summary='New API', previous_state='v1', new_state='v2',
                           significance_reason='Useful API', components=['API/MCP/agent layer'],
                           maturity='Unknown', license='Unknown', license_evidence=[],
                           claims_vs_verified='Author claim', risks=['Untested'], decision='publish',
                           decision_reason='Review API', review_status='approved',
                           reviewer='Test reviewer', reviewed_at='2026-10-22T12:00:00+03:00')
        self.approve()

    def test_rejected_repo_cannot_return_via_approved_event(self):
        (self.root/'data').mkdir(exist_ok=True)
        self.write('data/editorial-corrections.json',[dict(reason='invalid_repository_reference',
            url='https://github.com/a/repo',checked_at='2026-10-23T07:00:00+00:00')])
        with self.assertRaisesRegex(ValueError,'Rejected repository gate'):
            build_plan(self.root,[self.record],'2026-10-23')

    def approve(self):
        import hashlib
        if isinstance(self.record.get('claims_vs_verified'),str):self.record['claims_vs_verified']=dict(verified='Synthetic fixture only',author_claims=self.record['claims_vs_verified'],independent_testing='Not performed')
        folder=self.root/'data/evidence';folder.mkdir(parents=True,exist_ok=True)
        self.record['source_checks']=[]
        for i,s in enumerate(self.record['source_urls']):
            stamp='2026-10-22T11:00:00+03:00'
            raw=json.dumps(dict(url=s['url'],checked_at=stamp,http_status=200,content='Synthetic fixture, not research evidence')).encode()
            name=f'data/evidence/{self.record["discovery_id"]}-source-{i}.json';(self.root/name).write_bytes(raw)
            self.record['source_checks'].append(dict(url=s['url'],checked_at=stamp,evidence_file=name,sha256=hashlib.sha256(raw).hexdigest(),verified_scope='Test fixture only'))
        self.record['reviewed_content_hash'] = content_hash(self.record)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding='utf-8')

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def plan(self, records=None):
        return build_plan(self.root, [self.record] if records is None else records, '2026-10-22')

    def test_initial_profile_is_reviewed_and_preserves_defaults(self):
        self.record.update(repo_full_name='b/new', canonical_url='https://github.com/b/new')
        profile=dict(description='Purpose from README, not independently tested',
                     use_case='Editorial scenario', limitations='Untested; author claims only',
                     project_type='CLI tools')
        self.record['catalog_profile']=profile
        self.approve()
        plan=self.plan()
        write_plan(self.root,plan,plan['plan_hash'])
        catalog=json.loads((self.root/'catalog.json').read_text(encoding='utf-8'))
        card=catalog[-1]
        self.assertEqual({k:card[k] for k in profile},profile)
        from discoveries import compare
        report=compare(self.root,[self.record])
        self.assertEqual(report['errors'],0)
        self.assertEqual(report['eligible'],0)
        self.assertEqual(report['results'][0]['novelty_status'],'duplicate')
        self.assertEqual(card['catalog_profile_provenance']['previous_values']['use_case'],'Не оценено')
        self.assertIsNone(card['catalog_profile_provenance']['previous_values']['project_type'])
        from watch_pipeline import validate
        self.assertEqual(validate(self.root)['errors'],0)
        catalog[-1]['description']='Unsupported replacement'
        from apply_changes import sync_payloads
        for name,raw in sync_payloads(self.root,catalog,None).items():
            (self.root/name).write_bytes(raw)
        self.assertTrue(any('profile differs' in x['message'] for x in validate(self.root)['issues']))

    def test_new_research_profile_is_bound_to_review_and_preserved_on_reapply(self):
        self.record.update(repo_full_name='b/new', canonical_url='https://github.com/b/new',
                           initialize_research_profile=True,
                           catalog_profile=dict(description='Purpose',use_case='Use',limitations='Untested',project_type='CLI'))
        self.approve()
        plan=self.plan()
        write_plan(self.root,plan,plan['plan_hash'])
        r=json.loads((self.root/'docs/research.json').read_text(encoding='utf-8'))['b/new']
        self.assertEqual(r['editorial_summary'],'Purpose')
        self.assertEqual(r['editorial_limitations'],'Untested')
        self.assertEqual(r['test_status'],'Не тестировалось')
        self.assertEqual(r['russia_applicability']['rating'],'Не оценено')
        self.assertEqual(r['profile_provenance']['reviewed_content_hash'],content_hash(self.record))
        self.assertFalse(self.plan()['files'])
        from watch_pipeline import validate
        self.assertEqual(validate(self.root)['errors'],0)
        data=json.loads((self.root/'docs/research.json').read_text(encoding='utf-8'))
        data['b/new']['editorial_summary']='Unsupported claim'
        self.write('docs/research.json',data)
        self.assertTrue(any('research profile differs' in x['message'] for x in validate(self.root)['issues']))

    def test_already_serialized_journal_is_in_validation_snapshot(self):
        self.record.update(repo_full_name='b/new',canonical_url='https://github.com/b/new')
        self.approve()
        raw=(json.dumps(self.record,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        (self.root/'data/discoveries.jsonl').write_bytes(raw)
        plan=self.plan()
        self.assertNotIn('data/discoveries.jsonl',plan['files'])
        write_plan(self.root,plan,plan['plan_hash'])
        from watch_pipeline import validate
        self.assertEqual(validate(self.root)['errors'],0)

    def test_research_profile_initialization_requires_reviewed_new_project(self):
        self.record['initialize_research_profile']=True
        self.approve()
        with self.assertRaisesRegex(ValueError,'requires true'):self.plan()
        self.record['catalog_profile']=dict(description='D',use_case='U',limitations='L',project_type='T')
        self.approve()
        with self.assertRaisesRegex(ValueError,'new project only'):self.plan()
        self.record.update(repo_full_name='b/new',canonical_url='https://github.com/b/new')
        self.approve()
        self.record['catalog_profile']['description']='After approval'
        with self.assertRaises(ValueError):self.plan()

    def test_profile_cannot_overwrite_existing_research_or_add_arbitrary_fields(self):
        self.record['catalog_profile']=dict(description='D',use_case='U',limitations='L',project_type='T')
        self.approve()
        with self.assertRaisesRegex(ValueError,'new project only'):self.plan()
        self.record.update(repo_full_name='b/new',canonical_url='https://github.com/b/new')
        self.record['catalog_profile']['priority']='P1'
        self.approve()
        with self.assertRaisesRegex(ValueError,'catalog_profile requires'):self.plan()

    def test_first_research_event_preserves_unrated_assessment(self):
        from russia_applicability import derive
        catalog=[dict(self.card,russia_applicability=derive('a/repo',None))]
        self.write('catalog.json',catalog)
        self.write('docs/catalog.json',catalog)
        self.write('docs/research.json',{})
        for name,raw in sync_payloads(self.root,catalog,None).items():
            (self.root/name).write_bytes(raw)
        plan=self.plan()
        write_plan(self.root,plan,plan['plan_hash'])
        result=json.loads((self.root/'catalog.json').read_text(encoding='utf-8'))[0]
        self.assertEqual(result['russia_applicability']['rating'],'Не оценено')
        self.assertEqual(result['russia_applicability_history'][0]['previous_value'],catalog[0]['russia_applicability'])
        self.assertIsNone(result['russia_applicability']['source'])
        from watch_pipeline import validate
        self.assertEqual(validate(self.root)['errors'],0)

    def test_profile_change_invalidates_approval(self):
        self.record.update(repo_full_name='b/new',canonical_url='https://github.com/b/new')
        self.record['catalog_profile']=dict(description='D',use_case='U',limitations='L',project_type='T')
        self.approve()
        self.record['catalog_profile']['description']='Changed after review'
        with self.assertRaises(ValueError):self.plan()

    def test_apply_preserves_fields_and_is_idempotent(self):
        before = self.snapshot()
        plan = self.plan()
        self.assertEqual(before, self.snapshot())
        self.assertIn('New API', plan['diff'])
        write_plan(self.root, plan, plan['plan_hash'])
        catalog = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))
        for key, value in self.card.items():
            if key != 'history':
                self.assertEqual(catalog[0][key], value)
        self.assertEqual(catalog[0]['history'][0], self.card['history'][0])
        research = json.loads((self.root / 'docs/research.json').read_text(encoding='utf-8'))
        for key, value in self.research['a/repo'].items():
            self.assertEqual(research['a/repo'][key], value)
        applied = self.snapshot()
        second = self.plan()
        self.assertEqual(second['files'], {})
        write_plan(self.root, second, None)
        self.assertEqual(applied, self.snapshot())
        from watch_pipeline import validate
        self.assertEqual(validate(self.root)['errors'], 0)

    def test_empty_and_pending_leave_digest_unchanged(self):
        before = self.snapshot()
        self.assertEqual(self.plan([])['files'], {})
        self.record['review_status'] = 'pending'
        self.assertEqual(self.plan()['files'], {})
        self.assertEqual(before, self.snapshot())

    def test_new_project_unknown_fields(self):
        self.record.update(repo_full_name='b/new', canonical_url='https://github.com/b/new')
        self.approve()
        plan = self.plan()
        write_plan(self.root, plan, plan['plan_hash'])
        cards = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(cards[-1]['priority'], 'Не оценён')
        self.assertEqual(cards[-1]['test_status'], 'Не тестировалось')
        self.assertEqual(cards[0], self.card)

    def test_bad_hash_and_concurrent_edit(self):
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Plan hash'):
            write_plan(self.root, plan, 'bad')
        self.assertEqual(before, self.snapshot())
        (self.root / 'catalog.json').write_text('[]', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Concurrent'):
            write_plan(self.root, plan, plan['plan_hash'])

    def test_changed_applied_event_blocked(self):
        plan = self.plan()
        write_plan(self.root, plan, plan['plan_hash'])
        self.record['change_summary'] = 'Rewritten'
        self.approve()
        with self.assertRaisesRegex(ValueError, 'Applied event changed'):
            self.plan()

    def test_stale_approval_and_bad_seed(self):
        before = self.snapshot()
        self.record['change_summary'] = 'Unapproved'
        with self.assertRaisesRegex(ValueError, 'Candidate errors'):
            self.plan()
        self.assertEqual(before, self.snapshot())
        self.approve()
        (self.root / 'docs/index.html').write_text('No seed', encoding='utf-8')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'seed'):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_sync_copies_and_script_escape(self):
        self.card['description'] = '</script><script>alert(1)</script>'
        self.write('catalog.json', [self.card])
        files = sync_payloads(self.root)
        self.assertEqual(files['catalog.json'], files['docs/catalog.json'])
        self.assertIn(b'<\\/script>', files['docs/index.html'])

    def test_failure_rolls_back(self):
        import os
        original = os.replace
        count = 0
        def fail(source, target):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('Injected failure')
            return original(source, target)
        plan = self.plan()
        before = self.snapshot()
        with patch('apply_changes.os.replace', side_effect=fail):
            with self.assertRaises(OSError):
                write_plan(self.root, plan, plan['plan_hash'])
        self.assertEqual(before, self.snapshot())

    def test_research_only_does_not_create_digest(self):
        self.record['decision'] = 'research_only'
        self.approve()
        before = (self.root / 'digest.json').read_bytes()
        plan = self.plan()
        write_plan(self.root, plan, plan['plan_hash'])
        self.assertEqual(before, (self.root / 'digest.json').read_bytes())
        self.assertNotIn('digest.json', plan['files'])
        self.assertEqual(self.plan()['files'], {})

    def test_multiple_events_one_card_blocked(self):
        import copy
        second = copy.deepcopy(self.record)
        second.update(discovery_id='second', change_summary='Other change')
        second['source_urls'][0]['url'] += '.1'
        original=self.record;self.record=second;self.approve();self.record=original
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Multiple pending'):
            self.plan([self.record, second])
        self.assertEqual(before, self.snapshot())

    def test_validator_rejects_downgraded_new_review(self):
        from watch_pipeline import validate
        plan=self.plan(); write_plan(self.root,plan,plan['plan_hash'])
        digest=json.loads((self.root/'digest.json').read_text(encoding='utf-8'))
        digest[0]['items'][0]['review_status']='pending'
        self.write('digest.json',digest)
        self.assertTrue(any(x['code']=='reviewed_event' for x in validate(self.root)['issues']))

    def test_validator_rejects_missing_ledger_or_changed_history(self):
        from watch_pipeline import validate
        plan=self.plan(); write_plan(self.root,plan,plan['plan_hash'])
        self.write('data/applied-events.json',{})
        self.assertTrue(any(x['code']=='reviewed_event' for x in validate(self.root)['issues']))

    def test_validator_rejects_lost_publication_with_journal(self):
        from watch_pipeline import validate
        plan=self.plan(); write_plan(self.root,plan,plan['plan_hash'])
        (self.root/'data/discoveries.jsonl').write_text(json.dumps(self.record)+'\n',encoding='utf-8')
        self.write('digest.json',[])
        self.assertTrue(any(x['code']=='reviewed_event' for x in validate(self.root)['issues']))

    def test_applied_external_input_is_journaled_and_journal_loss_blocked(self):
        from watch_pipeline import validate
        plan=self.plan(); write_plan(self.root,plan,plan['plan_hash'])
        journal=self.root/'data/discoveries.jsonl'
        self.assertEqual(json.loads(journal.read_text(encoding='utf-8')), self.record)
        journal.unlink()
        self.assertTrue(any(x['code']=='reviewed_event' for x in validate(self.root)['issues']))


if __name__ == '__main__':
    unittest.main()
