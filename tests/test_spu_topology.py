"""Verify original static initialization before admitting the topology job."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalTopologyConstructorsTests(unittest.TestCase):
    def test_original_constructor_sequence_returns_without_modifying_code(self):
        self.check_original_constructors('aififa_topologycache', '--test-spu-topology-constructors',
            '06cb06e15272bef85f694bb916226be58677518355088bb38c2d55ddbfa254b7', 7)

    def test_original_railtracks_constructors_return_without_modifying_code(self):
        self.check_original_constructors('railtracks_movetotarget', '--test-spu-railtracks-constructors',
            'f0d60bc73fa56d84a06dc6085e2308b6d502a416d5b27a7997fb76d2bb62cf8b', 4)

    def test_original_secondary_ant_constructors_return_without_modifying_code(self):
        self.check_original_constructors('ant_kernel_secondary', '--test-spu-ant-secondary-constructors',
            '18664f851235de1b95b6fc827b73bfc18b9714425043fdcbf416a029373a94e4', 2)

    def check_original_constructors(self, module, command, sha256, count):
        image = ROOT / 'private/generated/spu_overlays' / module / 'image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), sha256)
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
            command, str(image)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=count, code_preserved=True, ai_algorithm_validated=False))
