import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from correct_card_usecases import correct


class CardUseCaseTests(unittest.TestCase):
    def test_preservation_provenance_and_repeat(self):
        c=[dict(name='a/b',use_case='',limitations='Старое',description='Сохранить',priority='P2')]
        r={'a/b':dict(project_type='Тип',guide_excerpt='Исходный текст',editorial_use_case='',editorial_limitations='Старое')}
        fix=dict(id='one',project='a/b',use_case='Редакционный сценарий; не испытывался',limitations='Нужна проверка',sources=['https://example.org/'],verified_scope='Описано в руководстве')
        new_c,new_r=correct(c,r,[fix])
        self.assertEqual(c[0]['use_case'],'')
        self.assertEqual(new_c[0]['description'],'Сохранить')
        self.assertEqual(new_r['a/b']['guide_excerpt'],'Исходный текст')
        self.assertEqual(new_r['a/b']['project_type'],'Тип')
        self.assertEqual(new_c[0]['editorial_corrections'][0]['previous_catalog']['limitations'],'Старое')
        self.assertEqual((new_c,new_r),correct(new_c,new_r,[fix]))
        new_c[0]['use_case']='Подмена'
        with self.assertRaises(ValueError):correct(new_c,new_r,[fix])

    def test_actual_batch_has_sources_and_test_caveat(self):
        fixes=json.loads((ROOT/'data/card-usecase-corrections.json').read_text(encoding='utf-8'))
        self.assertEqual(len(fixes),5)
        self.assertEqual(len({x['id'] for x in fixes}),5)
        for fix in fixes:
            self.assertTrue(fix['sources'])
            self.assertIn('независимо не испытывался',fix['use_case'])


if __name__=='__main__':unittest.main()
