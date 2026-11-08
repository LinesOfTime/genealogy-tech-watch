"""UI assertions for concise evidence presentation; not product trials."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class EvidenceClarityTests(unittest.TestCase):
    def test_project_detail_keeps_positive_trial_evidence(self):
        js=(ROOT/"docs/project-ui.js").read_text(encoding="utf-8")
        self.assertIn("x.evaluation?.independent_test === true",js)
        self.assertIn("x.evaluation?.test_report_url",js)
        self.assertIn("trials.html?project=",js)
        self.assertIn("Новая проверка первоисточников",js)
        self.assertNotIn("Независимое тестирование: ' + (r.test_status || x.test_status || 'Не подтверждено')",js)
        self.assertNotIn("независимая проверка функций не проводилась.",js)

    def test_evidence_levels_remain_accessible_without_negative_label(self):
        shared=(ROOT/"docs/watch-ui.js").read_text(encoding="utf-8")
        priorities=(ROOT/"docs/priorities-ui.js").read_text(encoding="utf-8")
        self.assertIn("const priorityAxes = card =>",shared)
        self.assertIn("const independent = ",shared)
        self.assertIn("const reportOf = x =>",priorities)
        self.assertIn("link(reportUrl,'Отчёт об испытании')",priorities)
        self.assertNotIn("Независимое испытание не подтверждено.",shared)
        self.assertNotIn("В ведомости нет ссылки на независимый отчёт.",priorities)
        self.assertNotIn("Работа проекта независимо не проверялась.",priorities)

if __name__=="__main__":
    unittest.main()
