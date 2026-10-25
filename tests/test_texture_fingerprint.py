"""Mutable font atlas content must invalidate the uploaded texture cache."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TextureFingerprintTests(unittest.TestCase):
    def test_glyph_rectangles_and_tail_bytes_change_the_content_fingerprint(self):
        result = subprocess.run([str(ROOT / 'private/build/boot/fifa_boot.exe'),
                                 '--test-texture-fingerprint'], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            old_atlas_blindspot_reproduced=True, glyph_change_detected=True,
            byte_mutations=63, stable_and_readonly=True))
