import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from russia_applicability import derive, migrate, catalog_assessment


class RussiaTests(unittest.TestCase):
    def test_original_text_and_fields_preserved_and_idempotent(self):
        catalog = [dict(name='a/b', priority='P1', history=[{'change':'Preserve'}])]
        research = {'a/b': dict(guide_excerpt='Before\nДля России: Высокий\nAfter', editorial_summary='Preserve')}
        old = copy.deepcopy((catalog, research))
        result = migrate(catalog, research)
        self.assertEqual((catalog, research), old)
        for key, value in research['a/b'].items():
            self.assertEqual(result[1]['a/b'][key], value)
        self.assertEqual(result[0][0]['priority'], 'P1')
        self.assertEqual(result, migrate(*result))
        self.assertEqual(result[1]['a/b']['russia_applicability']['original_line'], 'Для России: Высокий')

    def test_missing_and_specialized(self):
        self.assertEqual(derive('a/b', None)['rating'], 'Не оценено')
        self.assertIsNone(derive('a/b', {})['source'])
        self.assertEqual(derive('a/b', {'guide_excerpt':'Для России: Специализированный / зависит от задачи'})['rating'], 'Специализированный / зависит от задачи')

    def test_conflicts_and_multiple_lines_blocked(self):
        with self.assertRaises(ValueError):
            derive('a/b', {'guide_excerpt':'Для России: Высокий\nДля России: Высокий'})
        with self.assertRaises(ValueError):
            derive('a/b', {'guide_excerpt':'Для России: Придумано'})
        with self.assertRaises(ValueError):
            migrate([dict(name='a/b', russia_applicability={'rating':'Changed'})], {})

    def test_actual_dataset_preserved(self):
        catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
        research = json.loads((ROOT / 'docs/research.json').read_text(encoding='utf-8'))
        c, r = migrate(catalog, research)
        for old, new in zip(catalog, c):
            self.assertEqual(old, {k:v for k,v in new.items() if k in old})
        for key, old in research.items():
            self.assertEqual(old, {k:v for k,v in r[key].items() if k in old})
        from collections import Counter
        expected = Counter(catalog_assessment(x['name'].lower(), x, research.get(x['name'].lower()))['rating'] for x in catalog)
        self.assertEqual(Counter(x['russia_applicability']['rating'] for x in c), expected)

    def test_post_guide_editorial_assessments_preserve_text_and_source(self):
        assessment=dict(rating='Не оценено', original_line=None,
                        source='https://github.com/a/b',basis='Not tested in Russia')
        catalog=[dict(name='a/b',russia_applicability=assessment)]
        research={'a/b':dict(russia_applicability=dict(assessment,basis='Separate editorial wording'))}
        self.assertEqual(migrate(catalog,research),(catalog,research))
        self.assertEqual(migrate(catalog,{}),(catalog,{}))
        bad=copy.deepcopy(research)
        bad['a/b']['russia_applicability']['source']='https://github.com/other/repo'
        with self.assertRaises(ValueError):migrate(catalog,bad)
        bad=copy.deepcopy(research)
        bad['a/b']['russia_applicability']['rating']='Invented'
        with self.assertRaises(ValueError):migrate(catalog,bad)
        # Explicit assessments cannot override an existing guide line.
        bad=copy.deepcopy(research)
        bad['a/b']['guide_excerpt']='Для России: Высокий'
        with self.assertRaises(ValueError):migrate(catalog,bad)


if __name__ == '__main__':
    unittest.main()
