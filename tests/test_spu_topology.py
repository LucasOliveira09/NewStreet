"""Verify original static initialization before admitting the topology job."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalTopologyConstructorsTests(unittest.TestCase):
    def test_original_constructor_sequence_returns_without_modifying_code(self):
        image = ROOT / 'private/generated/spu_overlays/aififa_topologycache/image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '06cb06e15272bef85f694bb916226be58677518355088bb38c2d55ddbfa254b7')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
            '--test-spu-topology-constructors', str(image)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=7, code_preserved=True, ai_algorithm_validated=False))
