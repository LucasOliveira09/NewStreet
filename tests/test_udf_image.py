"""Exercise real UDF records with distinct ISO9660 names and bounded mappings."""
import io
import struct
import sys
import unittest
from pathlib import Path
import pycdlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from iso9660 import IsoImage
from udf_image import UdfImage


def disc():
    image = pycdlib.PyCdlib()
    image.new(interchange_level=3, udf='2.60')
    image.add_directory(iso_path='/PS3_GAME', udf_path='/PS3_GAME')
    payload = bytes(range(256)) * 31 + b'end'
    image.add_fp(io.BytesIO(payload), len(payload),
                 iso_path='/PS3_GAME/DATA0_BIG.SDAT;1',
                 udf_path='/PS3_GAME/data0.big.sdat')
    output = io.BytesIO()
    image.write_fp(output)
    image.close()
    return output, payload


class UdfTests(unittest.TestCase):
    def test_udf_preserves_name_and_actual_file_bytes_in_bridge_image(self):
        source, payload = disc()
        before = source.getvalue()
        reader = UdfImage(source)
        path, entry = next(reader.files())
        self.assertEqual(path, 'PS3_GAME/data0.big.sdat')
        self.assertEqual(b''.join(reader.chunks(entry, 511)), payload)
        path, iso_entry = next(IsoImage(source).files())
        self.assertEqual(path, 'PS3_GAME/DATA0_BIG.SDAT')
        self.assertEqual(entry.extents, iso_entry.extents)
        self.assertEqual(source.getvalue(), before)

    def test_metadata_mapping_can_span_extents_and_rejects_truncation(self):
        source, _ = disc()
        reader = UdfImage(source)
        # A virtual metadata partition is a file, potentially fragmented.
        reader.maps[1] = ((22, 3), (110, 5))
        self.assertEqual(reader._read_map(1, 1, 5),
                         source.getvalue()[23:25] + source.getvalue()[110:113])
        with self.assertRaisesRegex(ValueError, 'outside partition'):
            reader._read_map(1, 4, 5)
        with self.assertRaisesRegex(ValueError, 'Negative'):
            reader._read_map(1, -1, 2)

    def test_sparse_allocation_is_rejected_instead_of_reading_wrong_extent(self):
        source, _ = disc()
        reader = UdfImage(source)
        # Locate the regular file FE through the real FID and change its AD.
        game, = reader.children(reader.root)
        data = b''.join(reader.chunks(game))
        from pycdlib import udf
        pos = 0
        while pos < len(data):
            location = struct.unpack_from('<I', data, pos + 12)[0]
            fid, count = udf.parse_file_ident(data[pos:], location, 0, None)
            pos += count
            if not fid.is_parent():
                ad = fid.icb
                break
        address = reader._slice(reader.maps[ad.part_ref_num], ad.log_block_num * 2048, 2048)[0][0]
        modified = bytearray(source.getvalue())
        tag = int.from_bytes(modified[address:address + 2], 'little')
        attr = 168 if tag == 261 else 208
        start = address + attr + 8 + struct.unpack_from('<I', modified, address + attr)[0]
        length = struct.unpack_from('<I', modified, start)[0]
        struct.pack_into('<I', modified, start, length | 0x40000000)
        # Recompute descriptor CRC and checksum: corruption is semantic here.
        import binascii
        crc_length = struct.unpack_from('<H', modified, address + 10)[0]
        crc = binascii.crc_hqx(modified[address + 16:address + 16 + crc_length], 0)
        struct.pack_into('<H', modified, address + 8, crc)
        modified[address + 4] = 0
        modified[address + 4] = sum(modified[address:address + 16]) & 255
        reader.source = io.BytesIO(modified)
        with self.assertRaisesRegex(ValueError, 'Sparse'):
            reader._entry(ad)


if __name__ == '__main__':
    unittest.main()
