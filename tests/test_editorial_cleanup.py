import copy
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from editorial_hygiene import split_service
from repository_integrity import rejection_issues,verified_recheck,repository_url
from remove_invalid_reference import transform,KEY,URL
from audit_repositories import classify


class CleanupTests(unittest.TestCase):
    def test_service_only_and_real_limits_preserved(self):
        note='Часть 51: незакрытые поля: первоисточник'
        self.assertEqual(split_service('Нужны Python и ручная проверка | '+note),('Нужны Python и ручная проверка',[note]))
        self.assertEqual(split_service(note),('',[note]))
        self.assertEqual(split_service('Ч48: Предрелиз; не готово'),('Ч48: Предрелиз; не готово',[]))
        self.assertEqual(split_service('Возможно, нужен сервер'),('Возможно, нужен сервер',[]))

    def test_exclusion_snapshots_digest_and_idempotence(self):
        c=[dict(name=KEY,url=URL,description='Не установлен'),dict(name='a/b',limitations='Нужна проверка | Часть 51: незакрытые поля: тип')]
        r={KEY:dict(guide_excerpt='Старый текст'),'a/b':dict(audit_notes='Нужна проверка | Часть 51: незакрытые поля: тип',guide_excerpt='Не менять')}
        d=[dict(date='2026-10-23',items=[dict(repo=KEY,link=URL),dict(repo='a/b',link='https://github.com/a/b')])]
        evidence=dict(http_status=404,request_url='https://api.github.com/repos/'+KEY,checked_at='2026-10-23T07:29:39+00:00')
        new_c,new_r,new_d,j=transform(c,r,d,[],evidence)
        self.assertEqual(len(new_c),1);self.assertNotIn(KEY,new_r)
        self.assertEqual(new_d[0]['items'],[d[0]['items'][1]])
        self.assertEqual(j[0]['archived_catalog'],c[0]);self.assertEqual(j[0]['archived_research'],r[KEY])
        self.assertEqual(new_c[0]['limitations'],'Нужна проверка')
        self.assertEqual(new_r['a/b']['guide_excerpt'],'Не менять')
        self.assertEqual(transform(new_c,new_r,new_d,j,evidence),(new_c,new_r,new_d,j))
        with self.assertRaises(ValueError):transform(c,r,d,[],dict(evidence,http_status=403))

    def test_rejection_blocks_variants_and_requires_newer_api_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').mkdir()
            rejection=dict(reason='invalid_repository_reference',url=URL,checked_at='2026-10-23T07:00:00+00:00')
            (root/'data/editorial-corrections.json').write_text(json.dumps([rejection]),encoding='utf-8')
            for value in [URL,URL.upper()+'.git/',URL+'/issues/2']:
                self.assertTrue(rejection_issues(root,[dict(url=value)],{},[]))
            self.assertTrue(rejection_issues(root,[],{KEY:{}},[]))
            self.assertTrue(rejection_issues(root,[],{},[dict(items=[dict(repo=KEY)])]))
            self.assertFalse(rejection_issues(root,[dict(url=URL+'-other')],{},[]))
            body=dict(http_status=200,request_url='https://api.github.com/repos/'+KEY,
                checked_at=datetime.now(timezone.utc).isoformat(),response=dict(id=123,full_name=KEY))
            raw=json.dumps(body).encode();(root/'data/proof.json').write_bytes(raw)
            check=dict(url=URL,http_status=200,checked_at=body['checked_at'],evidence_file='data/proof.json',sha256=hashlib.sha256(raw).hexdigest())
            self.assertTrue(verified_recheck(root,rejection,check))
            for delta in [dict(http_status=404),dict(checked_at='2026-10-22T08:00:00+00:00'),dict(sha256='bad'),dict(evidence_file='../outside.json')]:
                self.assertFalse(verified_recheck(root,rejection,dict(check,**delta)))
            (root/'data/repository-rechecks.json').write_text(json.dumps([check]),encoding='utf-8')
            self.assertFalse(rejection_issues(root,[dict(url=URL)],{},[]))

    def test_audit_does_not_turn_network_errors_into_missing_projects(self):
        self.assertEqual(classify(404),'not_found')
        self.assertEqual(classify(200),'exists')
        for status in [None,403,429,500]:self.assertEqual(classify(status),'check_inconclusive')

    def test_actual_active_content_and_preservation(self):
        c=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
        r=json.loads((ROOT/'docs/research.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(c),163);self.assertGreaterEqual(len(r),141)
        self.assertNotIn(KEY,r);self.assertFalse(any(x['name'].lower()==KEY for x in c))
        for record in c:
            for field in ('description','use_case','limitations'):self.assertFalse(split_service(record.get(field))[1])
        for record in r.values():
            for field in ('editorial_summary','editorial_use_case','editorial_limitations','audit_notes'):self.assertFalse(split_service(record.get(field))[1])
        for record in c+list(r.values()):
            for note in record.get('editorial_service_notes',[]):
                self.assertEqual(split_service(note['original_text']),(record[note['field']],note['notes']))
        self.assertFalse(rejection_issues(ROOT,c,r,json.loads((ROOT/'digest.json').read_text(encoding='utf-8'))))
