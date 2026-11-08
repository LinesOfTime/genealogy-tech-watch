"""Tests cover structural checks, not Gramps MCP functionality."""
import tempfile
import unittest
from pathlib import Path
from tools.gramps_pilot_report import check

class ValidationTests(unittest.TestCase):
    def fixture(self,root):
        (root/"response.json").write_text("{}",encoding="utf-8")
        return {"project":"genealogy-mcp/gramps-mcp","project_version":"TEST_ONLY",
          "project_commit":"TEST_ONLY","gramps_web_version":"TEST_ONLY","api_version":"TEST_ONLY",
          "environment":"TEST_ONLY","fixture_sha256":"a"*64,"before_sha256":"a"*64,
          "after_sha256":"a"*64,"executed_at_utc":"TEST_ONLY",
          "cases":[{"id":f"T{i}","observed":"mock","expected":"mock","notes":"fixture only",
                    "passed":True,"evidence_file":"response.json"} for i in range(1,8)]}
    def test_valid_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            self.assertEqual(check(self.fixture(root),root)["result"],"pass_reported")
    def test_missing_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"][0]["evidence_file"]="missing"
            with self.assertRaises(ValueError):check(data,root)
    def test_changed_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["after_sha256"]="b"*64
            self.assertEqual(check(data,root)["result"],"failed_or_changed")
    def test_partial_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"].pop()
            with self.assertRaises(ValueError):check(data,root)
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"][0]["evidence_file"]="../secret"
            with self.assertRaises(ValueError):check(data,root)

if __name__=="__main__":unittest.main()
