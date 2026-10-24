"""Exercise the actual runtime's four unsupported-call boundaries."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'private/build/boot/fifa_boot.exe'


class BootDiagnosticsTests(unittest.TestCase):
    def test_missing_runtime_work_cannot_report_success(self):
        for boundary in ('hle', 'syscall', 'indirect', 'unlifted'):
            with self.subTest(boundary=boundary):
                result = subprocess.run([str(BOOT), '--test-missing', boundary],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                lines = [line for line in result.stderr.splitlines()
                         if line.startswith('[fifa-block] ')]
                self.assertEqual(len(lines), 1, result.stderr)
                event = json.loads(lines[0].removeprefix('[fifa-block] '))
                self.assertEqual(event['kind'], boundary)
                self.assertEqual(event['guest_lr'], 0x12345678)
                self.assertNotIn('faking CELL_OK', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
