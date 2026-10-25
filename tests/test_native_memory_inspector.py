import argparse
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_native_memory import parse_range, symbol_rva


class NativeMemoryInspectorTests(unittest.TestCase):
    def test_symbol_uses_decimal_offset_and_pe_section_rva(self):
        pe = bytearray(512); pe[:2] = b'MZ'
        struct.pack_into('<I', pe, 0x3c, 0x80); pe[0x80:0x84] = b'PE\0\0'
        struct.pack_into('<HH', pe, 0x84, 0x8664, 1)
        struct.pack_into('<H', pe, 0x94, 0x40)
        struct.pack_into('<II', pe, 0xe0, 0x4000, 0x100000)
        self.assertEqual(symbol_rva(pe, 'addr = 0001:8632'), 0x1021b8)
        for text in ('', 'addr = 0002:8632', 'addr = 0001:20000', 'addr = 1:1 addr = 1:2'):
            with self.assertRaises(ValueError):
                symbol_rva(pe, text)

    def test_ranges_remain_small_and_inside_guest_userspace(self):
        self.assertEqual(parse_range('0x10000:16'), (0x10000, 16))
        self.assertEqual(parse_range('0xfffffff0:16'), (0xfffffff0, 16))
        for value in ('0:8', '-1:8', '0x10000:0', '0x10000:4097', '0xffffffff:8', 'bad', '1:2:3'):
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_range(value)
