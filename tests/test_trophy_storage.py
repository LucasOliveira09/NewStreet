"""Exercise real TRP extraction and remaining-space queries through public HLE APIs."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'private/build/boot/fifa_boot.exe'


def archive(entries, version=1):
    start = 64 + len(entries) * 64
    records, payload = bytearray(), bytearray()
    for name, data in entries:
        records += struct.pack('>32sQQI12x', name.encode(), start + len(payload), len(data), 0)
        payload += data
    result = bytearray(struct.pack('>IIQIII20s16x', 0xdca24d00, version,
        start + len(payload), len(entries), 64, 0, b'\0' * 20) + records + payload)
    if version >= 2:
        result[28:48] = hashlib.sha1(result).digest()
    return result


class TrophyStorageTests(unittest.TestCase):
    def run_probe(self, disc, storage, **environment):
        result = subprocess.run([str(BOOT), '--test-trophy-storage', str(disc), str(storage)],
            capture_output=True, text=True, timeout=10, env=dict(os.environ, **environment))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout.splitlines()[-1])

    def setup_disc(self, root, blob):
        path = root / 'disc/PS3_GAME/TROPDIR/NPWR00001_00/TROPHY.TRP'
        path.parent.mkdir(parents=True)
        path.write_bytes(blob)
        return root / 'disc', root / 'storage'

    def test_install_real_files_and_query_zero_after_restart(self):
        entries = [('TROPCONF.SFM', b'<trophyconf><trophy id="000"/></trophyconf>'),
                   ('ICON0.PNG', b'authored icon payload')]
        for version in (1, 2):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                disc, storage = self.setup_disc(root, archive(entries, version))
                first = self.run_probe(disc, storage)
                self.assertEqual(first['before_result'], 0)
                self.assertEqual(first['before'], sum(len(data) for _, data in entries))
                self.assertEqual((first['registered'], first['after_result'], first['after']), (0, 0, 0))
                self.assertEqual(first['statuses'], [1, 8])
                installed = storage / 'NPWR00001_00'
                for name, data in entries:
                    self.assertEqual((installed / name).read_bytes(), data)
                second = self.run_probe(disc, storage)
                self.assertEqual(second['before'], 0)
                self.assertEqual(second['statuses'], [3, 8])
                self.assertEqual(second['invalid_handle'], 0x80022917)
                self.assertTrue(second['error_preserved'])

    def test_negative_permission_callback_cancels_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            disc, storage = self.setup_disc(Path(folder), archive([('TROPCONF.SFM', b'<trophyconf/>')]))
            result = self.run_probe(disc, storage, FIFA_TEST_TROPHY_DENY='1')
            self.assertEqual(result['registered'], 0x8002290f)
            self.assertEqual(result['statuses'], [1])
            self.assertFalse((storage / 'NPWR00001_00').exists())
            self.assertGreater(result['after'], 0)

    def test_existing_progress_is_preserved_byte_for_byte_at_registration(self):
        with tempfile.TemporaryDirectory() as folder:
            disc, storage = self.setup_disc(Path(folder), archive([('TROPCONF.SFM', b'<trophyconf/>')]))
            storage.mkdir()
            progress = storage / 'NPWR00001.json'
            original = b'{ "trophies": [ { "id": 0, "timestamp": 123456789 } ] }\n'
            progress.write_bytes(original)
            result = self.run_probe(disc, storage)
            self.assertEqual(result['registered'], 0)
            self.assertEqual(progress.read_bytes(), original)

    def test_reject_malformed_archives_without_callbacks_or_installed_files(self):
        valid = archive([('TROPCONF.SFM', b'<trophyconf/>')])
        bad_offset = bytearray(valid)
        struct.pack_into('>Q', bad_offset, 64 + 32, len(valid) + 1)
        bad_sha = archive([('TROPCONF.SFM', b'<trophyconf/>')], 2)
        bad_sha[-1] ^= 1
        for blob in (valid[:30], bad_offset, bad_sha,
                     archive([('../escape', b'x')]),
                     archive([('ICON0.PNG', b'a'), ('icon0.png', b'b')])):
            with self.subTest(blob=bytes(blob[:8])), tempfile.TemporaryDirectory() as folder:
                disc, storage = self.setup_disc(Path(folder), blob)
                result = self.run_probe(disc, storage)
                self.assertNotEqual(result['before_result'], 0)
                self.assertNotEqual(result['registered'], 0)
                self.assertEqual(result['statuses'], [])
                self.assertFalse((storage / 'NPWR00001_00').exists())

    def test_storage_failure_cannot_signal_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            disc, storage = self.setup_disc(Path(folder), archive([('TROPCONF.SFM', b'<trophyconf/>')]))
            storage.write_bytes(b'preserve existing file')
            result = self.run_probe(disc, storage)
            self.assertNotEqual(result['registered'], 0)
            self.assertNotIn(8, result['statuses'])
            self.assertEqual(storage.read_bytes(), b'preserve existing file')

    def test_corrupted_install_is_not_reported_as_zero_required_space(self):
        with tempfile.TemporaryDirectory() as folder:
            disc, storage = self.setup_disc(Path(folder), archive([('TROPCONF.SFM', b'<trophyconf/>')]))
            self.run_probe(disc, storage)
            config = storage / 'NPWR00001_00/TROPCONF.SFM'
            config.write_bytes(b'preserve damaged data for diagnosis')
            result = self.run_probe(disc, storage)
            self.assertNotEqual(result['before_result'], 0)
            self.assertNotEqual(result['registered'], 0)
            self.assertNotIn(8, result['statuses'])
            self.assertEqual(config.read_bytes(), b'preserve damaged data for diagnosis')
