"""Exercise original fixed-address CRT without entering the module's main."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FixedSpuStartupTests(unittest.TestCase):
    def test_raw_1ee9580_crt_zeros_bss_and_walks_ten_original_constructors(self):
        image = ROOT / 'private/analysis/job_1ee9580.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '56ac370c9307000bf6b33c207a065bedd7812ce2066b6a10faade884cb4f5a0f')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-fixed-startup', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=10, reverse_order=True, bss_zero_before_constructors=True,
            bss_guards_preserved=True, code_preserved=True, original_stop=0x3fff,
            main_executed=False, algorithm_validated=False))
