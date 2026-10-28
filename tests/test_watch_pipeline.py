import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('pipeline', ROOT / 'tools/watch_pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        self.catalog = [dict(name='Owner/Repo', url='https://github.com/Owner/Repo',
                             section='Test', description='Test', priority='P1', history=[])]
        self.digest = []
        self.write()

    def write(self):
        for stem, data, page in [('catalog', self.catalog, 'index'), ('digest', self.digest, 'digest')]:
            payload = json.dumps(data)
            (self.root / (stem + '.json')).write_text(payload, encoding='utf-8')
            (self.root / 'docs' / (stem + '.json')).write_text(payload, encoding='utf-8')
            (self.root / 'docs' / (page + '.html')).write_text(
                '<script type="application/json" id="seed">' + payload + '</script>', encoding='utf-8')
        (self.root / 'docs/research.json').write_text('{}', encoding='utf-8')

    def codes(self):
        return {x['code'] for x in pipeline.validate(self.root)['issues']}

    def test_evaluation_evidence_gates(self):
        self.catalog[0]['evaluation'] = dict(
            evidence_level='E0', review_status='triaged', component_fit=None,
            russia_fit=None, maturity=None, integration_effort=None,
            license_risk=None, source_urls=['https://github.com/Owner/Repo'],
            next_action='Check upstream')
        self.write()
        self.assertNotIn('evaluation_triadge_scores', self.codes())
        self.catalog[0]['evaluation']['component_fit'] = 4
        self.write()
        self.assertIn('evaluation_triadge_scores', self.codes())
        self.catalog[0]['evaluation']['component_fit'] = None
        self.catalog[0]['evaluation']['evidence_level'] = 'E4'
        self.catalog[0]['evaluation']['review_status'] = 'proposed'
        self.write()
        self.assertIn('evaluation_test_evidence', self.codes())
        self.catalog[0]['evaluation']['test_report_url'] = 'https://example.org/report'
        self.write()
        self.assertNotIn('evaluation_test_evidence', self.codes())

    def test_partial_cards_empty_result_and_idempotence(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        first = pipeline.validate(self.root)
        self.assertEqual(first['errors'], 0)
        self.assertEqual(first, pipeline.validate(self.root))
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_normalization_does_not_merge_similar_names(self):
        self.assertIsNone(pipeline.canonical_url('https://[broken'))
        self.assertEqual(pipeline.canonical_url('https://www.github.com/OWNER/Repo.git/'),
                         'https://github.com/owner/repo')
        self.assertNotEqual(pipeline.canonical_url('https://github.com/a/repo'),
                            pipeline.canonical_url('https://github.com/b/repo'))

    def test_duplicate_and_malformed_card(self):
        self.catalog += [dict(self.catalog[0], url='https://github.com/owner/repo/'), None]
        self.write()
        self.assertTrue({'duplicate_url', 'duplicate_name', 'card_type'} <= self.codes())

    def test_copy_seed_and_json_conflicts(self):
        (self.root / 'docs/catalog.json').write_text('[]', encoding='utf-8')
        (self.root / 'docs/index.html').write_text('<script id="seed">[]</script>', encoding='utf-8')
        self.assertTrue({'copy_mismatch', 'seed_mismatch'} <= self.codes())
        (self.root / 'catalog.json').write_text('{', encoding='utf-8')
        self.assertIn('json', self.codes())

    def test_duplicate_events_and_legacy_evidence(self):
        item = dict(repo='owner/repo', priority='P1', change='Delta',
                    link='https://github.com/owner/repo', components='OCR/HTR', action='Review')
        self.digest = [dict(date='2026-10-22', title='Test', summary='Test', items=[item, item])]
        self.write()
        self.assertTrue({'duplicate_event', 'legacy_evidence', 'broad_source'} <= self.codes())

    def test_baseline_reports_changes(self):
        with tempfile.TemporaryDirectory() as old:
            import shutil
            shutil.copytree(self.root, Path(old) / 'snapshot')
            self.catalog[0]['description'] = 'Changed'
            self.write()
            report = pipeline.validate(self.root, Path(old) / 'snapshot')
            self.assertIn('baseline_changed', {x['code'] for x in report['issues']})

    def test_bad_shapes_do_not_crash(self):
        self.digest = [None, dict(date=None, items=[None])]
        self.write()
        (self.root / 'docs/research.json').write_text('{"bad": null}', encoding='utf-8')
        self.assertGreater(pipeline.validate(self.root)['errors'], 0)

    def test_service_notes_and_rejected_repository_gate(self):
        self.catalog[0]['limitations']='Нужен сервер | Часть 51: незакрытые поля: тип'
        self.write()
        self.assertIn('service_note_in_content',self.codes())
        (self.root/'data').mkdir()
        rejection=dict(reason='invalid_repository_reference',url='https://github.com/owner/repo',checked_at='2026-10-23T07:00:00+00:00')
        (self.root/'data/editorial-corrections.json').write_text(json.dumps([rejection]),encoding='utf-8')
        self.assertIn('rejected_repository',self.codes())


if __name__ == '__main__':
    unittest.main()
