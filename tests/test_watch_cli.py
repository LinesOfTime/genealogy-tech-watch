import importlib.util,io,json,sys,tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('watch_cli',ROOT/'tools/watch.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class WatchCLITests(TestCase):
    def test_derived_data_is_refreshed_before_validation_tests_and_ui(self):
        with patch.object(mod.subprocess,'run') as run:
            run.return_value.returncode=0;mod.refresh_and_check()
        commands=[c.args[0] for c in run.call_args_list]
        self.assertIn('tools/build_task_matches.py',commands[0]);self.assertIn('validate',commands[2])
        self.assertEqual(commands[-1],['node','tests/ui_smoke.cjs'])

    def test_ingest_preserves_existing_bytes_and_deduplicates_input(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.watch-e2e-test-') as tmp:
            root=Path(tmp);journal=root/'journal.jsonl';incoming=root/'incoming.jsonl'
            original=b'{ "discovery_id" : "old", "review_status" : "approved" }\r\n'
            journal.write_bytes(original)
            row=dict(discovery_id='new',review_status='pending')
            incoming.write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n',encoding='utf-8')
            with patch.object(mod,'ROOT',root),patch.object(mod,'JOURNAL',journal),patch('discoveries.compare',return_value={'errors':0}),redirect_stdout(io.StringIO()):
                mod.ingest(incoming)
                self.assertTrue(journal.read_bytes().startswith(original))
                self.assertEqual(len(journal.read_text().splitlines()),2)
                saved=journal.read_bytes();mod.ingest(incoming);self.assertEqual(journal.read_bytes(),saved)

    def test_ingest_rejects_approval_without_mutation(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.watch-e2e-test-') as tmp:
            root=Path(tmp);journal=root/'journal.jsonl';source=root/'input.jsonl'
            journal.write_bytes(b'');source.write_text(json.dumps(dict(discovery_id='bad',review_status='approved'))+'\n')
            with patch.object(mod,'ROOT',root),patch.object(mod,'JOURNAL',journal):
                with self.assertRaisesRegex(ValueError,'pending'):mod.ingest(source)
            self.assertEqual(journal.read_bytes(),b'')
