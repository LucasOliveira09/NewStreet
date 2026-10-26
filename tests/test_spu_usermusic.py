"""Validate the original PIC user-music initializer and two-channel fades."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UserMusicTests(unittest.TestCase):
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
