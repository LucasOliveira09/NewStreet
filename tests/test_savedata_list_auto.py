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
    def query(self, root, name='AUTHORED_SAVE', **environment):
        result = subprocess.run([str(BOOT), '--test-savedata-list-item', name],
            env=dict(os.environ, PS3_GAMEDATA_ROOT=str(root), **environment),
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout.splitlines()[-1])

    def test_list_item_reads_existing_metadata_size_and_dates_without_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.probe(root, root)
            save = root / 'dev_hdd0/home/00000001/savedata/AUTHORED_SAVE'
            before = {p.name: p.read_bytes() for p in save.iterdir()}
            actual = self.query(root)
            self.assertEqual(actual['result'], 0)
            self.assertEqual(actual['title'], 'Authored save fixture')
            self.assertEqual(actual['name'], 'AUTHORED_SAVE')
            self.assertEqual(actual['size_kb'], 36)
            self.assertEqual(actual['bind'], 0)
            self.assertGreater(actual['mtime'], 0)
            self.assertAlmostEqual(actual['mtime'], save.stat().st_mtime, delta=2)
            self.assertEqual({p.name: p.read_bytes() for p in save.iterdir()}, before)
            optional = self.query(root, FIFA_TEST_SAVEDATA_QUERY_NULL_OUTPUTS='1')
            self.assertEqual(optional['result'], 0)
            self.assertTrue(optional['outputs_preserved'])

    def test_list_item_errors_preserve_outputs_and_existing_save(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.probe(root, root)
            for name in ['<null>', '../escape', 'MISSING', 'A' * 32]:
                with self.subTest(name=name):
                    result = self.query(root, name)
                    self.assertNotEqual(result['result'], 0)
                    self.assertTrue(result['outputs_preserved'])
            sfo = root / 'dev_hdd0/home/00000001/savedata/AUTHORED_SAVE/PARAM.SFO'
            sfo.write_bytes(b'preserve invalid metadata for diagnosis')
            result = self.query(root)
            self.assertNotEqual(result['result'], 0)
            self.assertTrue(result['outputs_preserved'])
            self.assertEqual(sfo.read_bytes(), b'preserve invalid metadata for diagnosis')

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
