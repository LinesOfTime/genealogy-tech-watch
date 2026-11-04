from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from history_integrity import git_baseline, read_git_objects


class GitObjectReadTests(unittest.TestCase):
    def test_binary_newlines_and_duplicate_objects_keep_exact_bytes(self):
        sha = 'a' * 40
        data = b'first\r\n\x00second\n'
        response = (sha + ' blob ' + str(len(data)) + '\n').encode() + data + b'\n'
        with patch('history_integrity.subprocess.check_output', return_value=response) as run:
            self.assertEqual(read_git_objects(ROOT, [('a name', sha), ('other', sha)]),
                             {'a name': data, 'other': data})
        self.assertEqual(run.call_args.kwargs['input'], (sha + '\n').encode())

    def test_missing_or_truncated_blob_is_rejected(self):
        sha = 'b' * 40
        for response in [(sha + ' missing\n').encode(), (sha + ' blob 10\nx\n').encode()]:
            with patch('history_integrity.subprocess.check_output', return_value=response):
                with self.assertRaises(ValueError):
                    read_git_objects(ROOT, [('file', sha)])

    def test_baseline_matches_individual_git_show(self):
        baseline = git_baseline(ROOT, 'HEAD')
        # Publication snapshots have no .git; exercise the actual checkout only.
        if not baseline:
            self.skipTest('No Git baseline in isolated publication snapshot')
        names = sorted(baseline)
        for name in (names[0], names[len(names) // 2], names[-1]):
            expected = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
            self.assertEqual(baseline[name], expected)


if __name__ == '__main__':
    unittest.main()
