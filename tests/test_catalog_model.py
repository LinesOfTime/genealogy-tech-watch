import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_model import MODEL_FILES, CURRENCY, DOMAINS, TYPES, enrich, model_issues, assessment_hash


class CatalogModelTests(unittest.TestCase):
    def setUp(self):
        self.cards=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        self.research=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))

    def test_preserves_original_records_priorities_and_history(self):
        actual={c['name'].lower():c for c in self.cards}
        self.assertEqual(len(actual),len(self.cards))
        original=copy.deepcopy(self.cards)
        for card in original:
            del card['classification'],card['assessment_currency']
        self.assertEqual(enrich(ROOT,original,self.research), self.cards)
        self.assertEqual(enrich(ROOT,self.cards,self.research), self.cards)
        self.assertEqual(model_issues(ROOT,self.cards,self.research), [])

    def test_types_directions_and_origins_are_independent(self):
        cards={c['name'].lower():c for c in self.cards}
        for c in self.cards:
            model=c['classification']
            self.assertIn(model['primary_type'],TYPES)
            self.assertTrue(set(model['domains'])<=set(DOMAINS))
            self.assertEqual(model['original_section'],c['section'])
            self.assertNotIn('GitHub Watch',model['domain_labels'])
        for name in ('openseadragon/openseadragon','archival-iiif/viewer','projectmirador/mirador'):
            self.assertNotIn('ocr',cards[name]['classification']['domains'])
        self.assertEqual(cards['familysearch/gedcom']['classification']['primary_type'],'standard')

    def test_source_check_never_implies_current_or_approves_proposals(self):
        before=copy.deepcopy(self.cards)
        for c in enrich(ROOT,self.cards,self.research):
            state=c['assessment_currency']
            self.assertIn(state['status'],CURRENCY)
            if state['pending_proposal']:
                self.assertEqual(state['status'],'proposed')
                self.assertEqual(state['pending_proposal']['review_status'],'pending')
                self.assertEqual(c.get('practical_priority'),next(row for row in before if row['name']==c['name']).get('practical_priority'))
        self.assertEqual(self.cards,before)
        c=next(row for row in self.cards if row.get('practical_priority',{}).get('priority')=='P1')
        changed=copy.deepcopy(self.cards)
        next(row for row in changed if row['name']==c['name'])['practical_priority']['rationale']='Changed after review'
        self.assertEqual(enrich(ROOT,changed,self.research)[self.cards.index(c)]['assessment_currency']['status'],'insufficient')

    def test_rejects_forged_current_tags_missing_model_and_changed_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in MODEL_FILES:
                (root/name).parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,root/name)
            review=json.loads((root/MODEL_FILES[1]).read_text(encoding='utf-8'))
            decisions=json.loads((root/MODEL_FILES[0]).read_text(encoding='utf-8'))
            proofs=review.get('evidence',[])+[
                dict(file=source['file']) for row in decisions['projects'].values()
                for source in row['sources'] if source['file'].startswith('data/evidence/')]
            for proof in proofs:
                (root/proof['file']).parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/proof['file'],root/proof['file'])
            row=next(iter(review['projects'].values()))
            row['status']='current'
            (root/MODEL_FILES[1]).write_text(json.dumps(review),encoding='utf-8')
            self.assertTrue(any('all assessment facets' in issue['message'] for issue in model_issues(root,self.cards,self.research)))
            row['status']='insufficient'
            (root/MODEL_FILES[1]).write_text(json.dumps(review),encoding='utf-8')
            proof=review['evidence'][0]
            (root/proof['file']).write_text('changed',encoding='utf-8')
            self.assertTrue(any('evidence changed' in issue['message'] for issue in model_issues(root,self.cards,self.research)))
            (root/MODEL_FILES[0]).unlink()
            self.assertTrue(model_issues(root,self.cards,self.research))
