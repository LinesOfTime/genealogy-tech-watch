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
