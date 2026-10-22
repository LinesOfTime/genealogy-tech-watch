import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from restore_descriptions import restore, PREFIX


class DescriptionTests(unittest.TestCase):
    def test_summary_precedes_purpose_and_preserves_original(self):
        c=[dict(name='a/b',description='Тип: Не установлен',priority='P2',history=[])]
        r={'a/b':dict(project_type='Библиотека',editorial_summary='Возможно, кандидат для поиска',guide_excerpt='Назначение: Иное')}
        old=copy.deepcopy((c,r))
        updated,report=restore(c,r)
        self.assertEqual((c,r),old)
        self.assertEqual(updated[0]['description'],PREFIX+r['a/b']['editorial_summary'])
        self.assertEqual(updated[0]['description_provenance']['original_description'],c[0]['description'])
        self.assertEqual(updated[0]['description_provenance']['source']['field'],'editorial_summary')
        self.assertEqual(report['summary']['provisional'],1)
        self.assertEqual((updated,report),restore(updated,r))

    def test_empty_or_placeholder_summary_falls_back(self):
        for summary in ['', 'Не установлен', None]:
            updated,report=restore([dict(name='a/b',description='Не установлен')],
                {'a/b':dict(editorial_summary=summary,guide_excerpt='Назначение: Возможно, инструмент\nДля России: Высокий')})
            self.assertEqual(updated[0]['description'],PREFIX+'Возможно, инструмент')
            self.assertEqual(report['records'][0]['source']['original_text'],'Назначение: Возможно, инструмент')

    def test_no_type_fallback_and_ambiguous_purpose_unchanged(self):
        c=[dict(name='a/b',description='Не установлен')]
        for research in [dict(project_type='Тип не должен стать назначением'),
                         dict(guide_excerpt='Назначение: Не установлен'),
                         dict(guide_excerpt='Назначение: Один\nНазначение: Два')]:
            updated,report=restore(c,{'a/b':research})
            self.assertEqual(updated,c)
            self.assertEqual(report['summary']['unresolved'],1)

    def test_non_targets_and_partial_cards_unchanged(self):
        c=[dict(name='a/b',description='Установленное редакционное описание'),dict(name='c/d',description='Не установлен')]
        updated,report=restore(c,{})
        self.assertEqual(updated,c)
        self.assertEqual(report['summary']['total'],1)

    def test_conflicting_edit_and_source_blocked(self):
        r={'a/b':dict(editorial_summary='Назначение')}
        updated,_=restore([dict(name='a/b',description='Не установлен')],r)
        edited=copy.deepcopy(updated); edited[0]['description']='Подмена'
        with self.assertRaises(ValueError): restore(edited,r)
        with self.assertRaises(ValueError): restore(updated,{'a/b':dict(editorial_summary='Иное')})

    def test_actual_47_preserve_other_data_and_qualifiers(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        updated,report=restore(c,r)
        self.assertEqual(report['summary']['total'],47)
        self.assertEqual(report['summary']['restored'],46)
        self.assertEqual(report['summary']['unresolved'],1)
        self.assertEqual(sum(row['result']=='restored_provisional' for row in report['records']
                             if row['source'] and row['source']['field']=='guide_excerpt'),17)
        for old,new in zip(c,updated):
            self.assertEqual({k:v for k,v in old.items() if k not in ('description','description_provenance')},
                             {k:v for k,v in new.items() if k not in ('description','description_provenance')})
        for row in report['records']:
            if row['restored']:
                text=row['source']['original_text']
                if row['source']['field']=='guide_excerpt':text=text.split(':',1)[1].strip()
                self.assertEqual(row['description'],PREFIX+text)


if __name__=='__main__': unittest.main()
