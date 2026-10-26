"""A truncated concurrent diagnostic must not discard the native run result."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import run_native

RAW = (b'[fifa-spawn] {"path":"/dev_bdvd/game.self"}\n'
       b'[fifa-spu-state] {"kind":"spu-indirect","image":526\n'
       b'[fifa-memory] []\n'
       b'[fifa-block] {"kind":"spu-indirect","value":384}\n')


class NativeEventParserTests(unittest.TestCase):
    def test_invalid_json_and_invalid_types_preserve_later_events(self):
        events, errors = run_native.parse_native_events(RAW)
        self.assertEqual([e['type'] for e in events], ['fifa-spawn', 'fifa-block'])
        self.assertEqual(events[-1]['data']['value'], 384)
        self.assertEqual([e['line'] for e in errors], [2, 3])
        self.assertTrue(all(e['raw'] and e['error'] for e in errors))

    def exercise_fake_run(self, root, fail_parser=False):
        for name in ('private/build/fifazf_full/fifa_boot.exe',
                     'private/build/boot/fifa_boot.exe', 'private/EBOOT.elf', 'private/FIFAZF.elf'):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        def fake_popen(*args, **kwargs):
            kwargs['stderr'].write(RAW)
            return SimpleNamespace(pid=1234, wait=Mock(return_value=90))
        with patch.object(run_native, 'ROOT', root), patch.object(
                run_native.subprocess, 'Popen', side_effect=fake_popen):
            if fail_parser:
                with patch.object(run_native, 'parse_native_events', side_effect=RuntimeError('parser failure')):
                    with self.assertRaisesRegex(RuntimeError, 'parser failure'):
                        run_native.run_native()
                return None
            return run_native.run_native()

    def test_report_retains_exit_code_and_records_truncated_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = self.exercise_fake_run(root)
            self.assertEqual(report['exit_code'], 90)
            self.assertEqual(len(report['event_parse_errors']), 2)
            output = root / report['logs']
            self.assertEqual(json.loads((output/'process-exit.json').read_text())['exit_code'], 90)
            self.assertEqual(json.loads((output/'result.json').read_text())['exit_code'], 90)

    def test_process_status_is_saved_before_a_later_parser_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.exercise_fake_run(root, fail_parser=True)
            status = next((root/'private/analysis/runs').glob('*/process-exit.json'))
            recorded = json.loads(status.read_text())
            self.assertEqual(recorded['pid'], 1234)
            self.assertEqual(recorded['exit_code'], 90)
