"""Decode original BC encoders' output using the independent Microsoft BC layout.

https://learn.microsoft.com/en-us/windows/win32/direct3d10/d3d10-graphics-programming-guide-resources-block-compression
Uniform 4x4 blocks avoid assuming any particular lossy encoder's endpoint choice.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def decode_block(block, bc3):
    color = block[8:] if bc3 else block
    c0, c1, indices = struct.unpack('<HHI', color)
    def rgb(c):
        r, g, b = c >> 11, (c >> 5) & 63, c & 31
        return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)
    colors = [rgb(c0), rgb(c1)]
    if bc3 or c0 > c1:
        colors += [tuple((2*a+b)//3 for a,b in zip(*colors)),
                   tuple((a+2*b)//3 for a,b in zip(*colors))]
    else:
        colors += [tuple((a+b)//2 for a,b in zip(*colors)), (0,0,0)]
    alphas, alpha_indices = [255] * 8, 0
    if bc3:
        a, b = block[:2]
        alphas = [a,b] + ([( (7-i)*a+i*b)//7 for i in range(1,7)] if a > b else
                           [((5-i)*a+i*b)//5 for i in range(1,5)] + [0,255])
        alpha_indices = int.from_bytes(block[2:8], 'little')
    return [colors[(indices >> (i*2)) & 3] +
            ((0 if not bc3 and c0 <= c1 and (indices >> (i*2)) & 3 == 3 else
              alphas[(alpha_indices >> (i*3)) & 7]),)
            for i in range(16)]


class OriginalSpuDxtTests(unittest.TestCase):
    def test_reference_bc_block_layouts(self):
        color = struct.pack('<HHI', 0xf800, 0x001f, 0xe4e4e4e4)
        self.assertEqual(decode_block(color, False)[:4],
                         [(255,0,0,255), (0,0,255,255), (170,0,85,255), (85,0,170,255)])
        transparent = struct.pack('<HHI', 0x001f, 0xf800, 0xe4e4e4e4)
        self.assertEqual(decode_block(transparent, False)[3], (0,0,0,0))
        indices = sum((i % 8) << (i*3) for i in range(16)).to_bytes(6, 'little')
        for endpoints, expected in ((bytes((255,0)), [255,0,218,182,145,109,72,36]),
                                    (bytes((0,255)), [0,255,51,102,153,204,0,255])):
            self.assertEqual([p[3] for p in decode_block(endpoints+indices+color, True)][:8], expected)

    def test_original_bc1_and_bc3_preserve_block_colors_and_padded_rows(self):
        self.check_original_encoder('sportsutil_dxt', '--test-spu-dxt',
            '3f1371daeeb5282209b1d95f45ae4f3608766b81cd009dffb32f98276c100604')

    def test_complete_original_job_preserves_colors_dma_guards_and_atomic_completion(self):
        self.check_original_encoder('dxt_encoder_job', '--test-spu-dxt-job',
            'd1cd200c70dd379efd997680333a35b7c1a16b7d5fdd0c3791ba69193b4824c0', queued_job=True)

    def check_original_encoder(self, module, command, sha256, queued_job=False):
        image = ROOT / 'private/generated/spu_overlays' / module / 'image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), sha256)
        palette = [(0,0,0,255), (255,255,255,255), (255,0,0,0),
                   (0,255,0,64), (0,0,255,128), (63,127,191,255)]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for bc3 in (False, True):
                for width,height in ((4,4), (8,8), (16,12), (64,64)):
                    for rotation in range(len(palette)):
                        with self.subTest(bc3=bc3, width=width, height=height, rotation=rotation):
                            def pixel(bx,by):
                                return palette[(by * (width//4) + bx + rotation) % len(palette)]
                            pitch = width * 4 + 16
                            source = bytearray([0xa5] * (pitch * height))
                            for y in range(height):
                                for x in range(width):
                                    r,g,b,a = pixel(x//4,y//4)
                                    source[y*pitch+x*4:y*pitch+x*4+4] = bytes((a,r,g,b))
                            (folder/'pixels.argb').write_bytes(source)
                            output = folder/'blocks.bin'
                            result = subprocess.run([str(ROOT/'private/build/fifazf_full/fifa_boot.exe'),
                                command, str(image), str(folder/'pixels.argb'), str(output),
                                str(width), str(height), '3' if bc3 else '1'],
                                capture_output=True, text=True, timeout=30)
                            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
                            checks = dict(source_preserved=True, output_guards=True, row_padding=True)
                            if queued_job: checks['atomic_completion'] = True
                            self.assertEqual(json.loads(result.stdout.splitlines()[-1]), checks)
                            blocks = output.read_bytes()
                            block_size = 16 if bc3 else 8
                            output_pitch = width//4 * block_size + 16
                            for by in range(height//4):
                                for bx in range(width//4):
                                    offset = by*output_pitch+bx*block_size
                                    decoded = decode_block(blocks[offset:offset+block_size], bc3)
                                    expected = pixel(bx,by)
                                    for rgba in decoded:
                                        # The full job's BC1 mode encodes one-bit
                                        # alpha (<128 is transparent). RGB has no
                                        # meaning for those transparent texels.
                                        if queued_job and not bc3 and expected[3] < 128:
                                            self.assertEqual(rgba[3], 0)
                                            continue
                                        self.assertLessEqual(max(abs(a-b) for a,b in zip(rgba[:3],expected[:3])), 9)
                                        if bc3: self.assertLessEqual(abs(rgba[3]-expected[3]), 1)
                                        elif queued_job: self.assertEqual(rgba[3], 255)
