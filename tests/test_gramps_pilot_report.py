"""Tests cover structural checks, not Gramps MCP functionality."""
import tempfile
import unittest
import hashlib
from pathlib import Path
from tools.gramps_pilot_report import check

class ValidationTests(unittest.TestCase):
    def fixture(self,root):
        (root/"response.json").write_text("{}",encoding="utf-8")
        for name,content in (("fixture.gramps",b"fixture"),("before.gramps",b"same-tree"),("after.gramps",b"same-tree")):
            (root/name).write_bytes(content)
        digest=lambda name: hashlib.sha256((root/name).read_bytes()).hexdigest()
        return {"project":"genealogy-mcp/gramps-mcp","project_version":"TEST_ONLY",
          "project_commit":"TEST_ONLY","gramps_web_version":"TEST_ONLY","api_version":"TEST_ONLY",
          "environment":"TEST_ONLY","fixture_file":"fixture.gramps","fixture_sha256":digest("fixture.gramps"),
          "before_file":"before.gramps","before_sha256":digest("before.gramps"),
          "after_file":"after.gramps","after_sha256":digest("after.gramps"),
          "executed_at_utc":"2026-11-09T01:00:00Z",
          "cases":[{"id":f"T{i}","observed":"mock","expected":"mock","notes":"fixture only",
                    "passed":True,"evidence_file":"response.json"} for i in range(1,8)]}
    def test_valid_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            self.assertEqual(check(self.fixture(root),root)["result"],"operator_reported_pass")
    def test_missing_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"][0]["evidence_file"]="missing"
            with self.assertRaises(ValueError):check(data,root)
    def test_changed_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);(root/"after.gramps").write_bytes(b"changed-tree")
            data["after_sha256"]=hashlib.sha256(b"changed-tree").hexdigest()
            self.assertEqual(check(data,root)["result"],"failed_or_changed")
    def test_partial_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"].pop()
            with self.assertRaises(ValueError):check(data,root)
    def test_false_declared_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["before_sha256"]="a"*64
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):check(data,root)
    def test_tampered_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);(root/"after.gramps").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):check(data,root)
    def test_same_before_after_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["after_file"]="before.gramps"
            with self.assertRaisesRegex(ValueError,"distinct"):check(data,root)
    def test_invalid_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["executed_at_utc"]="TEST_ONLY"
            with self.assertRaisesRegex(ValueError,"UTC timestamp"):check(data,root)
    def test_missing_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["after_file"]="not-here.gramps"
            with self.assertRaisesRegex(ValueError,"Evidence missing"):check(data,root)
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=self.fixture(root);data["cases"][0]["evidence_file"]="../secret"
            with self.assertRaises(ValueError):check(data,root)

if __name__=="__main__":unittest.main()
