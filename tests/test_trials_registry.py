"""Independent registry invariants: do not invent or auto-promote evidence."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
class TrialRegistryTests(unittest.TestCase):
    def test_registry_shape_and_unique_ids(self):
        r=json.loads((ROOT/"docs/trials.json").read_text(encoding="utf-8"))
        self.assertEqual(r["schema_version"],"1.0")
        self.assertIsInstance(r["trials"],list)
        ids=[x["id"] for x in r["trials"]]
        self.assertEqual(len(ids),len(set(ids)))
        catalog=json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"))
        projects={x["name"].lower() for x in catalog}
        for t in r["trials"]:
            self.assertIn(t["project"].lower(),projects)
            self.assertIn(t["status"],{"submitted","reviewed","accepted","rejected"})
            self.assertTrue(t["report_url"].startswith("https://"))
            self.assertRegex(t["report_sha256"],r"^[0-9a-f]{64}$")
            self.assertTrue(t["method"] and t["metrics"] and t["dataset"]["reference_truth"])
            for metric in t["metrics"]:
                self.assertGreater(metric["sample_size"],0)
    def test_publication_does_not_promote_catalog(self):
        page=(ROOT/"docs/trials-ui.js").read_text(encoding="utf-8")
        self.assertIn("trials.json",page)
        self.assertNotIn("localStorage.setItem",page)
        self.assertNotIn("E3 =",page)
        schema=json.loads((ROOT/"docs/trials.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"],"1.0")

if __name__=="__main__":
    unittest.main()
