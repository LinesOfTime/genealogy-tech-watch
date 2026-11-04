"""Safety regression tests for the one-command publication wrapper."""
import importlib.util
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "tools" / "watch_publish_pr.py"
spec = importlib.util.spec_from_file_location("watch_publish_pr", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PublishPRTests(TestCase):
    def invoke(self,handler):
        with patch.object(mod,'command',side_effect=handler),patch.object(mod,'allowed_paths',return_value=set(mod.ALLOWED)), \
             patch('sys.argv',['watch_publish_pr.py','--date','2026-11-04','--expect-plan','test-hash','--execute']), \
             redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            return mod.main()

    def handler(self,receipt=False,changed='catalog.json'):
        calls=[]
        def run(*args,**kwargs):
            calls.append(args)
            if args[:3]==('git','branch','--show-current'):return 'watch-test'
            if args[:3]==('git','merge-base','origin/main'):return 'base-sha'
            if args[:3]==('git','log','-1'):return 'Watch-Plan: test-hash\nWatch-Date: 2026-11-04' if receipt else ''
            if args[:3]==('gh','pr','view'):return '{"url":"https://github.com/a/b/pull/1","state":"OPEN"}'
            if args[:3]==('git','diff','--name-only'):
                return '' if len(args)>3 else changed
            if args[:4]==('git','diff','--cached','--name-only'):return changed
            if args[:3]==('git','rev-list','--count'):return '1'
            return ''
        return calls,run

    def test_recovery_checks_and_pushes_without_reapplying(self):
        calls,run=self.handler(receipt=True,changed='')
        self.assertEqual(self.invoke(run),0)
        self.assertTrue(any(str(mod.WATCH) in c and 'check' in c for c in calls))
        self.assertFalse(any(str(mod.WATCH) in c and 'publish' in c for c in calls))
        self.assertTrue(any('tools/check_publication.py' in c for c in calls))
        self.assertTrue(any(c[:2]==('git','push') for c in calls))

    def test_fresh_publish_checks_exact_tree_before_commit_push(self):
        calls,run=self.handler()
        self.assertEqual(self.invoke(run),0)
        guard=next(i for i,c in enumerate(calls) if 'tools/check_publication.py' in c)
        commit=next(i for i,c in enumerate(calls) if c[:2]==('git','commit'))
        self.assertLess(guard,commit)
        self.assertIn('[skip ci]',calls[commit][3])
        self.assertTrue(any('Watch-Plan: test-hash' in str(v) for v in calls[commit]))

    def test_unexpected_changes_and_unowned_recovery_never_push(self):
        for changed in ('tools/unrelated.py',''):
            calls,run=self.handler(changed=changed)
            self.assertEqual(self.invoke(run),1)
            self.assertFalse(any(c[:2] in [('git','push'),('git','commit'),('gh','pr')] and ('create' in c or c[0]=='git') for c in calls))

    def test_closed_pr_is_not_reused_or_duplicated(self):
        calls,base=self.handler()
        def run(*args,**kwargs):
            if args[:3]==('gh','pr','view'):return '{"url":"https://github.com/a/b/pull/1","state":"CLOSED"}'
            return base(*args,**kwargs)
        self.assertEqual(self.invoke(run),1)
        self.assertFalse(any(c[:2]==('git','push') or 'publish' in c for c in calls))

    def test_preview_does_not_require_github_auth_or_apply(self):
        def fake_command(*args, **kwargs):
            if args[:3] == ("git", "branch", "--show-current"):
                return "watch-test"
            if args[:3] == ("git", "status", "--porcelain"):
                return ""
            self.fail("Unexpected command in preview: " + repr(args))

        with patch.object(mod, "command", side_effect=fake_command), \
             patch("sys.argv", ["watch_publish_pr.py", "--date", "2026-11-04",
                                "--expect-plan", "test-hash"]), redirect_stdout(io.StringIO()):
            self.assertEqual(mod.main(), 0)

    def test_refuses_main_branch(self):
        with patch.object(mod, "command", return_value="main") as call, \
             patch("sys.argv", ["watch_publish_pr.py", "--date", "2026-11-04",
                                "--expect-plan", "test-hash", "--execute"]), \
             redirect_stderr(io.StringIO()):
            self.assertEqual(mod.main(), 1)
            self.assertEqual(call.call_count, 1)

    def test_refuses_dirty_worktree(self):
        def fake_command(*args, **kwargs):
            if args[:3] == ("git", "branch", "--show-current"):
                return "watch-test"
            if args[:3] == ("git", "status", "--porcelain"):
                return " M catalog.json"
            self.fail("Unexpected command: " + repr(args))

        with patch.object(mod, "command", side_effect=fake_command), \
             patch("sys.argv", ["watch_publish_pr.py", "--date", "2026-11-04",
                                "--expect-plan", "test-hash", "--execute"]), \
             redirect_stderr(io.StringIO()):
            self.assertEqual(mod.main(), 1)
