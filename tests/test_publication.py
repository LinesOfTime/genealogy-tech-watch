from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from check_publication import scan_blob


class PublicationTests(unittest.TestCase):
    def test_credential_redacted(self):
        token=b'ghp_'+b'a'*36
        results=scan_blob('example.txt',token)
        self.assertEqual(len(results),1)
        self.assertNotIn(token.decode(),str(results))

    def test_actions_and_artifacts_blocked(self):
        self.assertIn('GitHub Actions workflow',scan_blob('.github/workflows/test.yml',b'name: test'))
        self.assertIn('File larger than 5 MiB',scan_blob('big.txt',b'x'*(5*1024*1024+1)))
        self.assertIn('Binary content',scan_blob('binary.bin',b'\0'))

    def test_ordinary_source_allowed(self):
        self.assertEqual(scan_blob('docs/example.json','{"source":"https://github.com/a/b"}'.encode()),[])


if __name__=='__main__':
    unittest.main()
