"""Check OCR benchmark math and corpus safety; not an OCR model test."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ocr_benchmark import score,calculate,safe_path

class BenchmarkTests(unittest.TestCase):
    def test_pre_reform_letters_are_distinct(self):
        result=score('міръ и мѣра\n','миръ и мера\n')
        self.assertEqual((result['ref_chars'],result['char_errors']),(11,2))
        self.assertEqual(result['word_errors'],2)

    def test_unicode_nfc_and_strict_spelling(self):
        self.assertEqual(score('е\u0308','ё')['char_errors'],0)
        self.assertEqual(score('ѣ','е')['char_errors'],1)
        self.assertEqual(score('А','а')['char_errors'],1)

    def test_micro_average_uses_total_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for filename,value in [('a.txt','Иван Петров\n'),('a-pred.txt','Иван Петров\n'),
                                   ('b.txt','мѣсто\n'),('b-pred.txt','место\n')]:
                (root/filename).write_text(value,encoding='utf-8')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'schema_version':1,'cases':[
                {'id':'a','reference':'a.txt','prediction':'a-pred.txt'},
                {'id':'b','reference':'b.txt','prediction':'b-pred.txt'}]}),encoding='utf-8')
            result=calculate(manifest)
            self.assertEqual(len(result['cases']),2)
            self.assertEqual(result['micro']['char_errors'],1)
            self.assertEqual(result['micro']['word_errors'],1)

    def test_unsafe_paths_and_missing_files_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):safe_path(root,'../outside.txt')
            with self.assertRaises(ValueError):safe_path(root,'missing.txt')

    def test_duplicate_case_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'ref.txt').write_text('слово',encoding='utf-8')
            item={'id':'a','reference':'ref.txt','prediction':'ref.txt'}
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'schema_version':1,'cases':[item,item]}),encoding='utf-8')
            with self.assertRaises(ValueError):calculate(manifest)

if __name__=='__main__':unittest.main()
