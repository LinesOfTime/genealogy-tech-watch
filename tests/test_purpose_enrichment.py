import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from enrich_purposes import enrich


class PurposeTests(unittest.TestCase):
    def test_sources_preservation_idempotence_and_conflicts(self):
        c=[dict(name='a/b',description='Не установлен',priority='P2')]
        r={'a/b':dict(editorial_summary='',project_type='Тип',guide_excerpt='Назначение: Не установлен')}
        fixes=[dict(project='a/b',summary='Описание назначения по авторам; без испытаний.',sources=['https://example.org/'])]
        new_c,new_r,report=enrich(c,r,fixes)
        self.assertEqual(c[0]['description'],'Не установлен')
        self.assertEqual(new_r['a/b']['guide_excerpt'],r['a/b']['guide_excerpt'])
        self.assertEqual(new_r['a/b']['project_type'],'Тип')
        self.assertEqual(new_c[0]['priority'],'P2')
        self.assertEqual(new_c[0]['description_provenance']['original_description'],'Не установлен')
        self.assertEqual(new_c[0]['description_provenance']['source']['field'],'editorial_summary')
        self.assertEqual(enrich(new_c,new_r,fixes),(new_c,new_r,report))
        altered=copy.deepcopy(new_r);altered['a/b']['editorial_summary']='Подмена'
        with self.assertRaises(ValueError):enrich(new_c,altered,fixes)
        altered=copy.deepcopy(new_c);altered[0]['description']='Подмена'
        with self.assertRaises(ValueError):enrich(altered,new_r,fixes)

    def test_real_cohort_keeps_qualifiers_and_other_fields(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        fixes=json.loads((ROOT/'data/purpose-corrections.json').read_text(encoding='utf-8'))
        updated,research,report=enrich(c,r,fixes)
        self.assertEqual(updated,c);self.assertEqual(research,r)
        self.assertEqual(report['summary']['total'],47)
        self.assertEqual(sum(row['result']=='restored_provisional' for row in report['records']
                             if row['source'] and row['source']['field']=='guide_excerpt'),17)
        self.assertEqual(report['summary']['sources'],{'guide_excerpt':42,'editorial_summary':4})
        self.assertEqual([x['name'] for x in report['records'] if not x['restored']],['linesoftime/yarchive-downloader'])


if __name__=='__main__':unittest.main()
