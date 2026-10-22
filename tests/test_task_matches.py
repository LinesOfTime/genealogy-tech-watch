import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_task_matches import build


class TaskTests(unittest.TestCase):
    def test_candidate_qualifiers_preserved_and_not_ranked(self):
        catalog=[dict(name='a/b',url='https://github.com/a/b',description='Возможно, кандидат OCR',priority='P1')]
        before=copy.deepcopy(catalog)
        result=build(catalog,{})
        self.assertEqual(result['matches'][0]['status'],'candidate')
        self.assertEqual(result['matches'][0]['evidence'][0]['excerpt'],catalog[0]['description'])
        self.assertNotIn('priority',result['matches'][0])
        self.assertEqual(catalog,before)
        self.assertEqual(result,build(catalog,{}))

    def test_components_only_candidate_and_no_test_inference(self):
        result=build([dict(name='a/b',url='https://github.com/a/b',components=['OCR/HTR'])],{})
        self.assertEqual(result['matches'][0]['status'],'candidate')
        self.assertEqual(result['matches'][0]['test_status'],'Испытания не подтверждены')

    def test_negative_fields_and_names_do_not_match(self):
        result=build([dict(name='a/OCR',url='https://github.com/a/OCR',limitations='OCR не проверен')],
                     {'a/ocr':dict(project_type='OCR',guide_excerpt='Ограничения: OCR\nЛицензия: OCR')})
        self.assertEqual(result['matches'],[])

    def test_generated_data_matches_sources(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        result=build(c,r)
        self.assertEqual(result,json.loads((ROOT/'docs/task-matches.json').read_text(encoding='utf-8')))
        self.assertEqual(len({(x['task'],x['project']) for x in result['matches']}),len(result['matches']))


if __name__=='__main__':unittest.main()
