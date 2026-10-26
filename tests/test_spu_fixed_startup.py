"""Exercise original fixed-address CRT without entering the module's main."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FixedSpuStartupTests(unittest.TestCase):
    def test_path_estimates_exit_tail_reaches_original_stop_zero(self):
        image = ROOT / 'private/analysis/railtracks_pathestimates.bin'
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-pathestimates-exit', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            exit_tail_executed=True, original_stop=0, main_executed=False,
            code_preserved=True))

    def test_path_estimates_crt_initializes_four_original_constructors_in_reverse(self):
        image = ROOT / 'private/analysis/railtracks_pathestimates.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         'baccdc7f601823d404686b79fadeab5292015834af196101f3f99053493d1f76')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-pathestimates-startup', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=4, reverse_order=True, bss_bytes=25072,
            bss_zero_before_constructors=True, code_preserved=True,
            bss_guards_preserved=True, original_stop=0x3fff,
            main_executed=False, algorithm_validated=False))

    def test_batchplayer_crt_initializes_two_original_constructors_in_reverse(self):
        image = ROOT / 'private/analysis/fifarna_batchplayer_pass0.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         'c7b9464b73e1715963870666275c024085e842a3c28fb7928e461ad0f8ae6652')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-batchplayer-startup', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=2, reverse_order=True, bss_bytes=448,
            bss_zero_before_constructors=True, constructor_constants_correct=True,
            unused_bss_zero=True, code_preserved=True, bss_guards_preserved=True,
            original_stop=0x3fff, main_executed=False, algorithm_validated=False))

    def test_replay_matrixload_crt_initializes_constants_after_clearing_bss(self):
        image = ROOT / 'private/analysis/replay_matrixload.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '00e35e03ec4bb7d52a9ac86b226d15e60e8bf3c79c5413a4c34081553ccbfc7e')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-matrixload-startup', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=1, bss_bytes=48, bss_zero_before_constructors=True,
            constructor_constants_correct=True, code_preserved=True,
            bss_guards_preserved=True, original_stop=0x3fff,
            main_executed=False, algorithm_validated=False))

    def test_replay_matrixsave_empty_crt_preserves_image_and_guards(self):
        image = ROOT / 'private/analysis/replay_matrixsave.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '3c34933980f768ca7d70bfd9cb937c0e318ad890ac68597469319ac7a5801380')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-matrixsave-startup', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=0, bss_bytes=0, image_preserved=True,
            image_guards_preserved=True, original_stop=0x3fff,
            main_executed=False, algorithm_validated=False))

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
