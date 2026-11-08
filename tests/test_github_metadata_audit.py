import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'github_metadata_audit', Path(__file__).resolve().parents[1] / 'tools/github_metadata_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class GitHubMetadataAuditTests(unittest.TestCase):
    def test_repo_url(self):
        self.assertEqual(audit.repository_name('https://github.com/org/repo/tree/main'), 'org/repo')
        self.assertEqual(audit.repository_name('https://github.com/org/repo.git'), 'org/repo')
        self.assertIsNone(audit.repository_name('https://example.org/org/repo'))

    def test_audits_all_cards_and_deduplicates_requests(self):
        calls = []
        def fetch(repo):
            calls.append(repo)
            return {'archived': False, 'pushed_at': '2026-11-01T00:00:00Z',
                    'license': {'spdx_id': 'MIT'}}
        cards = [{'name': 'A', 'url': 'https://github.com/org/repo'},
                 {'name': 'B', 'url': 'https://github.com/org/repo'},
                 {'name': 'C', 'url': 'https://other.example/item'}]
        result = audit.inspect(cards, fetch)
        self.assertEqual(len(result), 3)
        self.assertEqual(calls, ['org/repo'])
        self.assertEqual(result[0]['license_spdx'], 'MIT')
        self.assertEqual(result[2]['status'], 'not_github_repository')

    def test_request_errors_are_visible(self):
        result = audit.inspect([{'name': 'A', 'url': 'https://github.com/a/b'}],
                               lambda repo: (_ for _ in ()).throw(RuntimeError('HTTP 404')))
        self.assertEqual(result[0]['status'], 'request_failed')
        self.assertIn('404', result[0]['error'])


if __name__ == '__main__':
    unittest.main()
