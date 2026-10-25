"""Original AOT SPU DMA copy compared with a host byte-copy oracle."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalSpuMemcpyTests(unittest.TestCase):
    def test_original_dma_copy_handles_byte_alignment_and_double_buffer_boundaries(self):
        image = ROOT / 'private/generated/spu_overlays/job_util_memcpy/image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         'da7145f8a13b2500457cc9de0b086d278037b4cbce75008be2468bed66a60c1f')
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
            '--test-spu-job-memcpy', str(image)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                         dict(original_entries=['0x1d0', '0xb0'], cases=576, bss_checks=16, bytes_match=True,
                              source_preserved=True, destination_guards=True))
