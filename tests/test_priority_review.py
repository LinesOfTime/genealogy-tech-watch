import copy,json,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from priority_review import build

class PriorityTests(unittest.TestCase):
    def card(self,**extra):return dict(name='a/b',url='https://github.com/a/b',priority='P1',description='OCR',**extra)
    def test_no_reclassification_or_unknown_zero(self):
        card=self.card();before=copy.deepcopy(card);row=build([card],{})['projects'][0]
        self.assertEqual(row['state'],'missing');self.assertIsNone(row['maturity'])
        self.assertEqual(row['legacy_priority'],'P1');self.assertEqual(card,before)
    def test_later_review_requests_recheck_not_upgrade(self):
        c=self.card(evaluation=dict(review_status='triaged',evidence_level='E0',reviewed_at='2026-10-28'))
        r={'a/b':dict(watch_events=[dict(review_status='approved',date='2026-10-25',reviewed_at='2026-11-04T10:00:00Z')])}
        row=build([c],r)['projects'][0]
        self.assertEqual(row['state'],'changed');self.assertEqual(row['evidence_level'],'E0')
        self.assertIn('автоматически не повышать',row['next_action'])
    def test_404_and_profile_are_reference_issues(self):
        c=self.card();checks=dict(records=[dict(url=c['url'],result='not_found',http_status=404)])
        self.assertEqual(build([c],{},checks)['projects'][0]['state'],'reference_issue')
        c['url']='https://github.com/a'
        self.assertEqual(build([c],{})['projects'][0]['state'],'reference_issue')
    def test_proposed_is_not_approved_and_e2_needs_version(self):
        c=self.card(evaluation=dict(review_status='proposed',evidence_level='E2',source_urls=['https://github.com/a/b/blob/HEAD/README.md']))
        row=build([c],{})['projects'][0]
        self.assertEqual(row['state'],'proposed');self.assertTrue(any('версии' in f for f in row['flags']))
        c['evaluation']['source_urls']=['https://github.com/a/b/blob/'+'a'*40+'/README.md']
        self.assertFalse(any('версии' in f for f in build([c],{})['projects'][0]['flags']))
    def test_generated_full_audit(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        checks=json.loads((ROOT/'reports/repository-existence.json').read_text(encoding='utf-8'))
        actual=json.loads((ROOT/'docs/priority-review.json').read_text(encoding='utf-8'))
        self.assertEqual(build(c,r,checks),actual)
        self.assertEqual(actual['counts']['total'],len(c))
        self.assertEqual(len({x['url'] for x in actual['projects']}),len(c))

if __name__=='__main__':unittest.main()
