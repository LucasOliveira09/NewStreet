"""Check each reviewed PIC initializer independently at four LS placements."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ('bandpass_fir64', '0f79910a2458b2f5769c4c924bb61258d9bf124a877431acba1bf098ccd293ed', False, 0),
    ('bandpass_iir2', 'd8e840f15c74513b8a033fc4a60c536ec51a0fde784919c7390c4046e7bda539', False, 0),
    ('distortion_clip', 'fdc2c46f854a82b18b0152e09afd0dc13569f8c3447d183ed6734d58cf38b102', False, 0),
    ('spureverbir1', '60f7f69085a1ffaca04f125b1ff2adb76fa9577125ddd69d078da7a3d4eaf0bc', True, 208),
)


class AudioEffectInitializationTests(unittest.TestCase):
    def test_each_reviewed_initializer_preserves_its_contract(self):
        for name, digest, context, untouched in CASES:
            with self.subTest(module=name):
                image = ROOT / 'private/analysis' / ('audio_' + name + '.bin')
                self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), digest)
                result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                         '--test-spu-audio-effect-init', name, str(image)],
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                expected = dict(positions=4, initialization_validated=True,
                                callbacks_relocated=True, external_pointer_preserved=True,
                                code_preserved=True, guards_preserved=True,
                                untouched_state_bytes=untouched)
                expected[name + '_algorithm_validated'] = False
                if context:
                    expected['context_vector_preserved'] = True
                self.assertEqual(json.loads(result.stdout.splitlines()[-1]), expected)
