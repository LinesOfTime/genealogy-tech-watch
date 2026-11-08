"""Guard verified source updates displayed on project detail pages."""
import json
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class SourceUpdatesTests(unittest.TestCase):
    def test_records_refer_to_catalog_projects_and_fixed_sources(self):
        data=json.loads((ROOT/"docs/source-updates.json").read_text(encoding="utf-8"))
        projects={p["project"].lower() for p in json.loads((ROOT/"docs/priority-review.json").read_text(encoding="utf-8"))["projects"]}
        self.assertEqual(data["version"],1)
        seen=set()
        for row in data["items"]:
            key=row["project"].lower()
            self.assertIn(key,projects)
            self.assertNotIn(key,seen)
            seen.add(key)
            for field in ("checked_at","kind","status","summary","verified","limitations","next_action"):
                self.assertTrue(isinstance(row.get(field),str) and row[field].strip(),(key,field))
            self.assertRegex(row["checked_at"],r"^20\d\d-\d\d-\d\d$")
            self.assertTrue(row["sources"])
            for url in row["sources"]:
                self.assertTrue(url.startswith("https://github.com/"))
                if row["status"]!="needs_recheck":
                    self.assertRegex(url,r"/blob/[0-9a-f]{40}/")
        self.assertEqual(len(seen),len(data["items"]))

    def test_render_does_not_rewrite_catalog(self):
        js=(ROOT/"docs/project-ui.js").read_text(encoding="utf-8")
        self.assertIn("source-updates.json",js)
        self.assertIn("Новая проверка первоисточников",js)
        self.assertIn("esc(u.summary)",js)
        self.assertIn("esc(u.limitations)",js)

if __name__=="__main__":
    unittest.main()
