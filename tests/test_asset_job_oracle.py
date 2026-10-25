import sys
import json
import lzma
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate_asset_jobs import refpack_decode, validate


class RefpackOracleTests(unittest.TestCase):
    def test_interrupted_metadata_preserves_other_results_and_fails_validation(self):
        for partial in ('', '{"codec":', '[]', '{"codec":"refpack"}'):
            with self.subTest(partial=partial), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                compressed = b'\x10\xfb\x00\x00\x03\xffabc'
                for name in ('complete', 'interrupted'):
                    (root / (name + '.input')).write_bytes(compressed)
                    (root / (name + '.output')).write_bytes(b'abc')
                (root / 'complete.json').write_text(json.dumps(dict(
                    codec='refpack', captured=True, input_bytes=len(compressed), output_bytes=3)))
                (root / 'interrupted.json').write_text(partial)
                observed = validate(root)
                self.assertFalse(observed['all_passed'])
                self.assertEqual(observed['passed'], 1)
                self.assertEqual(observed['total'], 2)
                self.assertEqual(observed['incomplete'], ['interrupted'])
                self.assertIn('error', next(j for j in observed['jobs'] if j['job'] == 'interrupted'))

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


class LzmaOracleTests(unittest.TestCase):
    def test_raw_asset_stream_and_mismatching_output(self):
        expected = bytes(range(256)) * 257
        compressed = lzma.compress(expected, format=lzma.FORMAT_RAW, filters=[dict(
            id=lzma.FILTER_LZMA1, dict_size=65536, lc=3, lp=0, pb=2)])
        # A known-size raw block can finish without an end marker. Removing
        # these final range-coder bytes still emits the complete authored data.
        for payload, output, matches in ((compressed, expected, True),
                                          (compressed[:-6], expected, True),
                                          (compressed, b'wrong bytes', False)):
            with self.subTest(input_bytes=len(payload), matches=matches), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'lzma.input').write_bytes(payload)
                (root / 'lzma.output').write_bytes(output)
                (root / 'lzma.json').write_text(json.dumps(dict(codec='lzma', captured=True,
                    input_bytes=len(payload), output_bytes=len(output))))
                result = validate(root)
                self.assertEqual(result['all_passed'], matches, result)
                self.assertEqual(result['jobs'][0]['matches'], matches)

    def test_corrupt_and_oversized_raw_streams_fail_without_unbounded_expansion(self):
        filters = [dict(id=lzma.FILTER_LZMA1, dict_size=65536, lc=3, lp=0, pb=2)]
        oversized = lzma.compress(b'x' * (4 * 1024 * 1024 + 1),
                                   format=lzma.FORMAT_RAW, filters=filters)
        for compressed in (b'', b'\x00' * 4, b'\xff' * 32, oversized):
            with self.subTest(compressed_bytes=len(compressed)), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'lzma.input').write_bytes(compressed)
                (root / 'lzma.output').write_bytes(b'x')
                (root / 'lzma.json').write_text(json.dumps(dict(codec='lzma', captured=True,
                    input_bytes=len(compressed), output_bytes=1)))
                result = validate(root)
                self.assertFalse(result['all_passed'])
                self.assertIn('error', result['jobs'][0])


if __name__ == '__main__':
    unittest.main()
