import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate_asset_jobs import refpack_decode


class RefpackOracleTests(unittest.TestCase):
    def test_literal_stop_and_overlapping_lookbacks(self):
        cases = [(b'\xffabc', b'abc'),
                 (b'\xe0ABCD\x00\x03\xfc', b'ABCDABC'),
                 (b'\xe0ABCD\x80\x00\x03\xfc', b'ABCDABCD'),
                 (b'\xe0ABCD\xc0\x00\x03\x00\xfc', b'ABCDABCDA'),
                 (b'\x01\x00a\xfc', b'aaaa')]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                stream = b'\x10\xfb' + len(expected).to_bytes(3, 'big') + payload
                self.assertEqual(refpack_decode(stream), expected)

    def test_optional_compressed_size_and_large_size_header(self):
        for flag, width in ((0x11, 3), (0x90, 4), (0x91, 4)):
            header = bytes([flag, 0xfb])
            if flag & 1:
                header += (4).to_bytes(width, 'big')
            header += (3).to_bytes(width, 'big')
            self.assertEqual(refpack_decode(header + b'\xffabc'), b'abc')

    def test_truncated_invalid_and_oversized_commands_are_rejected(self):
        for stream in (b'', b'\x10\xfb\x00\x00', b'\x10\xfb\x00\x00\x03\xffab',
                       b'\x10\xfb\x00\x00\x03\x00\x00\xfc',
                       b'\x10\xfb\x00\x00\x01\xffabc',
                       b'\x10\xfb\xff\xff\xff\xfc'):
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                refpack_decode(stream)


if __name__ == '__main__':
    unittest.main()
