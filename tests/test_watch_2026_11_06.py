import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from discoveries import read_jsonl, content_hash
from source_evidence import evidence_errors


class NovemberSixTests(unittest.TestCase):
    def test_two_new_cards_and_one_existing_update_have_evidence(self):
        catalog=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        research=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        journal=read_jsonl(ROOT/'data/discoveries.jsonl')
        for repo in ('semanticmeaning/kinship-kit','joaquimrcarvalho/personal-historical-archive','kinprove/genealogy-research-recipes'):
            cards=[c for c in catalog if c['url'].lower().rstrip('/')=='https://github.com/'+repo]
            self.assertEqual(len(cards),1)
            record=next(r for r in journal if r['discovery_id']=='github:'+repo+':watch-2026-11-06')
            self.assertEqual(evidence_errors(ROOT,record),[])
            self.assertEqual(record['reviewed_content_hash'],content_hash(record))
            self.assertIn('не',record['claims_vs_verified']['independent_testing'].lower())
            self.assertEqual(sum(e.get('discovery_id')==record['discovery_id'] for e in cards[0]['history']),1)
            self.assertEqual(sum(e.get('discovery_id')==record['discovery_id'] for e in research[cards[0]['name'].lower()]['watch_events']),1)
        pha=next(c for c in catalog if c['name']=='joaquimrcarvalho/personal-historical-archive')
        self.assertIn('Не установлена',pha['license'])
        self.assertIn('не проверены',pha['limitations'])
        kinship=next(c for c in catalog if c['name']=='semanticmeaning/kinship-kit')
        self.assertEqual(kinship['license'],'MIT')
        self.assertNotEqual(kinship['project_type'],kinship['description'])
        recipes=next(c for c in catalog if c['name']=='kinprove/genealogy-research-recipes')
        self.assertEqual(recipes['practical_priority']['priority'],'P2')
        self.assertIn('FSL-1.1-MIT',recipes['license'])


if __name__=='__main__':unittest.main()
