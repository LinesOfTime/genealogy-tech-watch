"""Adversarial correctness tests; synthetic evidence is never research evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import test_apply_changes as applyfixtures
from apply_changes import build_plan,write_plan
from discoveries import compare,content_hash
from event_integrity import event_issues
from history_integrity import history_errors
from repository_integrity import rejection_issues,verified_recheck
from source_evidence import evidence_errors


class AssuranceTests(unittest.TestCase):
    def setUp(self):
        self.f=applyfixtures.ApplyTests('test_apply_preserves_fields_and_is_idempotent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.root=self.f.root

    def test_approved_url_without_saved_source_is_blocked(self):
        record=copy.deepcopy(self.f.record);record.pop('source_checks')
        record['reviewed_content_hash']=content_hash(record)
        self.assertEqual(compare(self.root,[record])['eligible'],0)
        before=self.f.snapshot()
        with self.assertRaises(ValueError):build_plan(self.root,[record],'2026-10-23')
        self.assertEqual(before,self.f.snapshot())

    def test_tampered_lost_mismatched_and_failed_snapshots_are_blocked(self):
        record=self.f.record;check=record['source_checks'][0];p=self.root/check['evidence_file'];original=p.read_bytes()
        for mutate in [lambda b:b+b' ',lambda b:json.dumps(dict(json.loads(b),http_status=404)).encode(),
                       lambda b:json.dumps(dict(json.loads(b),url='https://github.com/other/repo')).encode(),
                       lambda b:json.dumps(dict(json.loads(b),content='')).encode()]:
            raw=mutate(original);p.write_bytes(raw)
            changed=copy.deepcopy(record)
            # Also try updating the claimed checksum: source identity/status still must match.
            if raw!=original+b' ':changed['source_checks'][0]['sha256']=hashlib.sha256(raw).hexdigest()
            self.assertTrue(evidence_errors(self.root,changed))
        p.unlink();self.assertTrue(evidence_errors(self.root,record))

    def test_evidence_path_escape_and_future_review_are_blocked(self):
        record=copy.deepcopy(self.f.record)
        record['source_checks'][0]['evidence_file']='../outside.json'
        self.assertTrue(evidence_errors(self.root,record))
        record=copy.deepcopy(self.f.record);record['reviewed_at']='2099-01-01T00:00:00Z'
        self.assertTrue(evidence_errors(self.root,record))

    def test_source_change_after_approval_is_blocked(self):
        record=copy.deepcopy(self.f.record);record['source_checks'][0]['verified_scope']='Changed assertion'
        self.assertEqual(compare(self.root,[record])['eligible'],0)

    def test_undifferentiated_or_empty_claims_are_blocked(self):
        for claims in ['',[],{},'Everything is verified',dict(verified='fact',author_claims='claim')]:
            record=copy.deepcopy(self.f.record);record['claims_vs_verified']=claims
            record['reviewed_content_hash']=content_hash(record)
            self.assertEqual(compare(self.root,[record])['eligible'],0)

    def test_evidence_change_between_plan_and_write_is_blocked(self):
        plan=self.f.plan();p=self.root/self.f.record['source_checks'][0]['evidence_file']
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Concurrent file change'):write_plan(self.root,plan,plan['plan_hash'])

    def test_removing_all_event_projections_does_not_hide_ledger(self):
        self.f.write('data/applied-events.json',{'lost':'hash'})
        self.assertTrue(event_issues(self.root,[],{},[]))

    def test_journal_truncation_and_evidence_deletion_fail_trusted_baseline(self):
        old=[dict(reason='invalid_repository_reference',url='https://github.com/a/repo',checked_at='2026-10-22T00:00:00Z')]
        baseline={'data/editorial-corrections.json':json.dumps(old).encode(),'data/evidence/pin.json':b'proof'}
        self.f.write('data/editorial-corrections.json',[])
        with patch('history_integrity.git_baseline',return_value=baseline):
            self.assertTrue(rejection_issues(self.root,[dict(url='https://github.com/a/repo')],{},[]))
        self.assertEqual(len(history_errors(self.root,baseline)),2)

    def test_malformed_registry_fails_closed(self):
        for value in [None,{},[None],[dict(reason='invalid_repository_reference')]]:
            self.f.write('data/editorial-corrections.json',value)
            self.assertTrue(rejection_issues(self.root,[],{},[]))

    def test_historical_approved_artifact_is_required(self):
        from source_evidence import LEGACY
        key=next(iter(LEGACY));record=dict(discovery_id=key,reviewed_content_hash=LEGACY[key][0])
        self.assertTrue(evidence_errors(self.root,record))
