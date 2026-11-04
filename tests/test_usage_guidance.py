import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from usage_guidance import build_context,load_context,usage_issues,TASK_CHECKS
from build_task_matches import build


class UsageTests(unittest.TestCase):
    def test_country_of_developer_or_russia_rating_is_not_coverage(self):
        card=dict(name='a/b',url='https://github.com/a/b',description='OCR разработан в Финляндии',
                  russia_applicability=dict(rating='Высокий'))
        self.assertEqual(build_context([card],{},dict(projects=[]))['projects'],{})
        row=build([card],{})['matches'][0]
        self.assertIsNone(row['usage_context'])

    def test_guidance_requires_retained_description_and_does_not_mutate_it(self):
        card=dict(name='a/b',url='https://github.com/a/b',description='Возможный кандидат для шведских архивов')
        profile=dict(repository='a/b',label='Швеция',regions=['Швеция'],scope='archive',
                     scenario='Проверить на копии',boundary='Поддержка другого архива не установлена',
                     source=dict(file='catalog.json',field='description',excerpt='шведских архивов'))
        before=copy.deepcopy(card)
        context=build_context([card],{},dict(projects=[profile]))
        self.assertEqual(context['projects']['a/b']['evidence']['original_text'],card['description'])
        self.assertEqual(before,card)
        profile['source']['excerpt']='России'
        with self.assertRaisesRegex(ValueError,'Stale'):build_context([card],{},dict(projects=[profile]))
        profile['source']['field']='russia_applicability'
        with self.assertRaisesRegex(ValueError,'descriptive source'):build_context([card],{},dict(projects=[profile]))

    def test_task_checks_are_specific_and_do_not_promote_candidates(self):
        card=dict(name='a/b',url='https://github.com/a/b',description='Возможно OCR и MCP')
        rows=build([card],{})['matches']
        self.assertTrue(all(r['status']=='candidate' for r in rows))
        self.assertEqual(len(set(TASK_CHECKS.values())),7)
        self.assertIn('страницу',next(r for r in rows if r['task']=='transcribe')['next_check'])
        self.assertIn('права',next(r for r in rows if r['task']=='agents')['next_check'])

    def test_published_geography_and_seed_match_evidence(self):
        catalog=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        research=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        data=load_context(ROOT,catalog,research)
        self.assertEqual(usage_issues(ROOT,catalog,research),[])
        self.assertEqual(len(data['projects']),7)
        self.assertEqual(data['projects']['ai-riksarkivet/ra-mcp']['regions'],['Швеция'])
        self.assertEqual(data['projects']['k-woitas/eperiodica-explorer']['regions'],['Швейцария'])
        self.assertNotIn('geiserx/gramps-web-toolkit',data['projects'])
        self.assertNotIn('nafrec',data['projects'])
        self.assertEqual(data['projects']['magicianmarty/heritage-research-mcp']['scope'],'mixed')


if __name__=='__main__':unittest.main()
