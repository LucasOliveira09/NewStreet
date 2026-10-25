"""Native HLE dispatch, ninth argument, real files and write-failure regression."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'private/build/boot/fifa_boot.exe'


class SaveDataListAutoTests(unittest.TestCase):
    def probe(self, volume, root):
        result = subprocess.run([str(BOOT), '--test-savedata-list-auto', str(volume)],
            env=dict(os.environ, PS3_GAMEDATA_ROOT=str(root)), capture_output=True,
            text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout.splitlines()[-1])

    def test_write_load_and_callback_userdata_match_the_actual_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            actual = self.probe(root, root)
            self.assertEqual((actual['save'], actual['load']), (0, 0))
            self.assertEqual((actual['fixed'], actual['stat'], actual['file']), (2, 2, 4))
            self.assertTrue(actual['userdata'])
            self.assertTrue(actual['contents'])
            self.assertEqual(actual['new'], [1, 0])
            for kb in actual['free_kb']:
                self.assertGreaterEqual(kb * 1024, min(actual['before'], actual['after']) - 262144)
                self.assertLessEqual(kb * 1024, max(actual['before'], actual['after']) + 262144)
            save = root / 'dev_hdd0/home/00000001/savedata/AUTHORED_SAVE'
            self.assertEqual((save / 'DATA.BIN').read_bytes(), bytes([0, 1, 2, 127, 128, 254, 255]))
            self.assertEqual((save / 'PARAM.SFO').read_bytes()[:4], b'\0PSF')

    def test_storage_failure_does_not_report_a_completed_save(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            blocked = root / 'blocked'
            blocked.write_bytes(b'preserve this existing file')
            actual = self.probe(root, blocked)
            self.assertNotEqual(actual['save'], 0)
            self.assertLess(actual['file'], 2)
            self.assertEqual(blocked.read_bytes(), b'preserve this existing file')
