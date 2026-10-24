"""Synthetic disc records prove multi-extent handling before real asset extraction."""
import io
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from iso9660 import IsoImage

BLOCK = 2048


def record(name, sector, length, flags=0):
    row = bytearray(33 + len(name) + (len(name) % 2 == 0))
    row[0] = len(row)
    struct.pack_into('<I', row, 2, sector)
    struct.pack_into('>I', row, 6, sector)
    struct.pack_into('<I', row, 10, length)
    struct.pack_into('>I', row, 14, length)
    row[25], row[32] = flags, len(name)
    row[33:33 + len(name)] = name
    return row


def image(rows):
    disc = bytearray(25 * BLOCK)
    pvd = memoryview(disc)[16 * BLOCK:17 * BLOCK]
    pvd[:7] = b'\x01CD001\x01'
    pvd[128:132] = struct.pack('<H', BLOCK) + struct.pack('>H', BLOCK)
    root = record(b'\x00', 20, BLOCK, 2)
    pvd[156:156 + len(root)] = root
    directory = b''.join(rows)
    disc[20 * BLOCK:20 * BLOCK + len(directory)] = directory
    disc[22 * BLOCK:22 * BLOCK + 6] = b'hello '
    disc[23 * BLOCK:23 * BLOCK + 5] = b'world'
    return io.BytesIO(disc)


class IsoTests(unittest.TestCase):
    def test_file_extents_are_joined_in_directory_order(self):
        source = image([record(b'BIG.DAT;1', 22, 6, 0x80), record(b'BIG.DAT;1', 23, 5)])
        original = source.getvalue()
        iso = IsoImage(source)
        entry, = iso.children(iso.root)
        self.assertEqual(entry.size, 11)
        self.assertEqual(b''.join(iso.chunks(entry, 4)), b'hello world')
        self.assertEqual(source.getvalue(), original)

    def test_duplicate_without_continuation_is_rejected(self):
        iso = IsoImage(image([record(b'A;1', 22, 6), record(b'A;1', 23, 5)]))
        with self.assertRaisesRegex(ValueError, 'extent'):
            iso.children(iso.root)

    def test_extent_outside_image_is_rejected(self):
        iso = IsoImage(image([record(b'A;1', 24, 3 * BLOCK)]))
        with self.assertRaisesRegex(ValueError, 'outside'):
            iso.children(iso.root)

    def test_path_components_cannot_escape_destination(self):
        iso = IsoImage(image([record(b'../A;1', 22, 6)]))
        with self.assertRaisesRegex(ValueError, 'name'):
            iso.children(iso.root)

    def test_mismatched_endian_record_is_rejected(self):
        row = record(b'A;1', 22, 6)
        row[17] = 7
        iso = IsoImage(image([row]))
        with self.assertRaisesRegex(ValueError, 'endian'):
            iso.children(iso.root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
