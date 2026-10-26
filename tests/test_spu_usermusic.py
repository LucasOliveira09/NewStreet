"""Validate the original PIC user-music initializer and two-channel fades."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UserMusicTests(unittest.TestCase):
    def test_matrix_panner_init_relocates_descriptor_at_four_placements(self):
        image = ROOT / 'private/analysis/audio_spumatrixpanner.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         'e6b4418602e124e7530e7ec55b59eded3b036b04b49d387618560e887691e7aa')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-matrixpanner-init', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            positions=4, initialization_validated=True, callbacks_relocated=True,
            external_pointer_preserved=True, code_preserved=True, guards_preserved=True,
            untouched_state_bytes=0, matrix_algorithm_validated=False))

    def test_reverb_init_preserves_additional_state_at_four_placements(self):
        image = ROOT / 'private/analysis/audio_spureverbmodel1.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '9f527fbfc677a8d598b9b3b635f5bbfeafa9e273fc738893a4a3496489a653c0')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-reverb-init', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            positions=4, initialization_validated=True, callbacks_relocated=True,
            external_pointer_preserved=True, context_vector_preserved=True,
            code_preserved=True, guards_preserved=True, untouched_state_bytes=32,
            reverb_algorithm_validated=False))

    def test_compressor_init_relocates_internal_callback_and_preserves_external_context(self):
        image = ROOT / 'private/analysis/audio_spucompressor1.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '78403fd4cfc8924d2d17a10ee1b58f06cb99db5246df630819eef4f9b09dec07')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-compressor-init', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            positions=4, initialization_validated=True, callbacks_relocated=True,
            external_pointer_preserved=True, context_vector_preserved=True,
            code_preserved=True, guards_preserved=True, untouched_state_bytes=0,
            compressor_algorithm_validated=False))

    def test_original_fades_match_linear_sample_oracle_at_four_placements(self):
        image = ROOT / 'private/analysis/audio_spuusermusicarbiter.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '5297121e39d5e9b1d9feee385a35e07f9c22ecf9dfa1817f65a79179099a3701')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-spu-usermusic', str(image)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            positions=4, fade_cases=8, channels=2, compared_samples=4096,
            initialization_validated=True, relocation_validated=True,
            code_preserved=True, guards_preserved=True))
