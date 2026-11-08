import importlib.util
from datetime import date
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'priority_review_queue', Path(__file__).resolve().parents[1] / 'tools/priority_review_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PriorityQueueTests(unittest.TestCase):
    def test_unrated_and_missing_review_are_queued(self):
        cards = [{'name': 'A', 'priority': 'Не оценён'},
                 {'name': 'B', 'priority': 'P2'}]
        result = module.queue(cards, date(2026, 11, 8))
        self.assertEqual(len(result), 2)
        self.assertIn('unrated', result[0]['reasons'])
        self.assertIn('no_dated_review', result[1]['reasons'])

    def test_recent_review_not_queued(self):
        card = {'name': 'A', 'practical_priority': 'P1',
                'practical_priority_history': [{'reviewed_at': '2026-11-07T12:00:00Z'}]}
        self.assertEqual(module.queue([card], date(2026, 11, 8)), [])

    def test_stale_review_and_next_action(self):
        card = {'name': 'A', 'practical_priority': 'P2',
                'practical_priority_history': [
                    {'reviewed_at': '2026-01-01T12:00:00Z', 'next_action': 'Pilot'}]}
        result = module.queue([card], date(2026, 11, 8))
        self.assertIn('stale_review', result[0]['reasons'])
        self.assertEqual(result[0]['next_action'], 'Pilot')

if __name__ == '__main__':
    unittest.main()
