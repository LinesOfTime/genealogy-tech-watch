import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_task_matches import build, role_for


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

    def test_roles_keep_uncertainty_and_conflicting_types(self):
        cases=[('Набор исторических документов с OCR','data'),
               ('Библиотека сопоставления записей','tool'),
               ('Спецификация GEDCOM 7','reference'),
               ('Возможно, инструмент для OCR','unknown'),
               ('Спецификация и CLI-приложение','unknown'),
               ('Не установлен','unknown')]
        for text,expected in cases:
            with self.subTest(text=text):
                r=role_for({},dict(project_type=text))
                self.assertEqual(r['id'],expected)
                if r['source']:self.assertEqual(r['source']['excerpt'],text)
        self.assertEqual(role_for(dict(description='Движок HTR/OCR'),{})['id'],'tool')
        self.assertEqual(role_for({},dict(project_type='Корпус, не программа'))['id'],'unknown')

    def test_comparison_retains_source_values_without_priority_ranking(self):
        card=dict(name='a/b',url='https://github.com/a/b',description='Возможно, OCR',
                  use_case='Проверить OCR на копии',license='Не установлена',priority='P1')
        row=build([card],{})['matches'][0]
        self.assertEqual(row['purpose'],card['description'])
        self.assertEqual(row['use_case'],card['use_case'])
        self.assertEqual(row['license'],card['license'])
        self.assertNotIn('priority',row)
        self.assertEqual(row['status'],'candidate')
        self.assertEqual(row['role']['id'],'unknown')

    def test_generated_data_matches_sources(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        result=build(c,r)
        self.assertEqual(result,json.loads((ROOT/'docs/task-matches.json').read_text(encoding='utf-8')))
        self.assertEqual(len({(x['task'],x['project']) for x in result['matches']}),len(result['matches']))


if __name__=='__main__':unittest.main()
