"""Original SPU LZMA job versus authored data compressed by independent liblzma."""
import hashlib
import json
import lzma
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalSpuLzmaTests(unittest.TestCase):
    def test_original_job_decodes_raw_blocks_across_dma_boundaries(self):
        image = ROOT / 'private/generated/spu_overlays/asset_lzma/image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(),
                         '6d5c19b1e71f7889531143ba08df360180077a8009b98cf4ddbbc1fdbaa21697')
        filters = [dict(id=lzma.FILTER_LZMA1, dict_size=65536, lc=3, lp=0, pb=2)]
        rng = random.Random(30882)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for size in (0, 1, 15, 16, 17, 255, 256, 4096, 16384, 65536, 65672):
                for pattern in ('constant', 'sequence', 'random'):
                    with self.subTest(size=size, pattern=pattern):
                        expected = (b'x' * size if pattern == 'constant' else
                                    bytes(i % 256 for i in range(size)) if pattern == 'sequence' else
                                    rng.randbytes(size))
                        source = folder / 'authored.raw'
                        actual = folder / 'decoded.bin'
                        source.write_bytes(lzma.compress(expected, format=lzma.FORMAT_RAW, filters=filters))
                        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                            '--test-spu-job-lzma', str(image), str(source), str(actual), str(size)],
                            capture_output=True, text=True, timeout=30)
                        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                            dict(original_entry='0x100', source_preserved=True, dma_guards=True))
                        self.assertEqual(actual.read_bytes(), expected)
