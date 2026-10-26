import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from inventory_spu_raw import inspect_common_ant, scan_segment, review_images


def word(blob, offset, value):
    struct.pack_into('>I', blob, offset, value)


def ila(register, value):
    return 0x42000000 | (value << 7) | register


def fixture(size=0x400, table=0x200):
    # Authored SPU metadata/code fixture, not bytes from the original title.
    blob = bytearray(size)
    for i in range(4):
        word(blob, i * 4, ila(2, i + 1))
    for offset, value in [(16, 0x30), (20, size), (24, 0x50), (28, 0x80000000),
                          (40, 1), (44, 0x55011055)]:
        word(blob, offset, value)
    for offset, register, value in [(0x54, 8, size), (0x58, 9, size + 0x50),
                                     (0x7c, 80, table), (0x80, 81, table + 12)]:
        word(blob, offset, ila(register, value))
    word(blob, 0xbc, 0x33000000 | (((0xd8 - 0xbc) // 4) << 7))
    last = table - 16
    word(blob, last, 0x40800003 | (1 << 7))
    word(blob, last + 4, ila(4, 0xffff))
    word(blob, last + 8, 0x32000000 | ((((0x150 - last - 8) // 4) & 0xffff) << 7))
    word(blob, last + 12, 0x00200000)
    struct.pack_into('>4I', blob, table, 0x100, 0x140, last, 0)
    return blob


class CommonAntReviewTests(unittest.TestCase):
    def test_structural_review_does_not_depend_on_original_build_directory_name(self):
        first, second, invalid = bytes(fixture()), bytes(fixture(0x500, 0x300)), fixture()
        word(invalid, 24, 0x70)
        blobs = {0x1000: first, 0x2000: second, 0x3000: bytes(invalid)}
        records = [dict(source_ea=hex(ea), bytes=len(blob), ant_common_path=ea == 0x1000)
                   for ea, blob in blobs.items()]
        review_images(records, lambda ea, size: blobs[ea][:size], first)
        self.assertEqual([item.get('common_crt_review') is not None for item in records],
                         [True, True, False])
        self.assertIn('common_crt_rejection', records[2])
        blobs[0x1000] = bytes(invalid)
        review_images(records, lambda ea, size: blobs[ea][:size], first)
        self.assertNotIn('common_crt_review', records[0])
        self.assertIn('common_crt_rejection', records[0])

    def test_same_crt_with_different_sizes_tables_and_main_target_is_bounded(self):
        original = fixture()
        other = fixture(0x500, 0x300)
        word(other, 0xbc, 0x33000000 | (((0xe0 - 0xbc) // 4) << 7))
        self.assertEqual(inspect_common_ant(bytes(other), bytes(original)),
                         dict(code_end=0x300, constructors=[0x100, 0x140, 0x2f0],
                              table=0x300, bss_start=0x500, bss_end=0x550))

    def test_changed_crt_header_bss_or_out_of_bounds_metadata_is_not_admitted(self):
        reference = bytes(fixture())
        mutations = [(28, 0x80000080), (24, 0x60), (40, 0), (16, 0x34),
                     (20, 0x10000), (0x30, 1), (0x54, ila(8, 0x410)),
                     (0x7c, ila(80, 0x400)), (0x80, ila(81, 0x210)),
                     (0x200, 0x101), (0x204, 0x100), (0x20c, 4),
                     (0x1f8, 0), (0xbc, 0x33000000 | (0x1000 << 7))]
        for offset, value in mutations:
            with self.subTest(offset=offset, value=value):
                blob = fixture(); word(blob, offset, value)
                with self.assertRaises(ValueError):
                    inspect_common_ant(bytes(blob), reference)

    def test_padding_between_code_and_constructor_table_is_checked(self):
        reference = bytes(fixture())
        blob = fixture()
        blob[0x1e8:0x1f8] = blob[0x1f0:0x200]
        # Moving a relative branch requires rebasing its displacement as well.
        word(blob, 0x1f0, 0x32000000 | ((((0x150 - 0x1f0) // 4) & 0xffff) << 7))
        blob[0x1f8:0x200] = bytes(8)
        word(blob, 0x208, 0x1e8)
        self.assertEqual(inspect_common_ant(bytes(blob), reference)['code_end'], 0x1f8)
        blob[0x1fc] = 1
        with self.assertRaises(ValueError):
            inspect_common_ant(bytes(blob), reference)

    def test_inventory_accepts_only_complete_headers_with_the_declared_label_position(self):
        blob = bytes(fixture())
        label = b'BuiltElfName' + bytes(20) + b'c:\\owned\\antcommonplugins\\fixture.elf\0'
        records = scan_segment(blob + label, 0x100000)
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0]['source_ea'], records[0]['name']),
                         ('0x100000', 'fixture.elf'))
        self.assertEqual(scan_segment(blob[:-1] + label, 0), [])
        self.assertEqual(scan_segment(blob + label[:-1], 0), [])
        self.assertEqual(scan_segment(bytes(1) + blob + label, 0), [])


if __name__ == '__main__':
    unittest.main()
