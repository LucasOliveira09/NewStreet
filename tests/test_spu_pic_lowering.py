import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/ps3recomp/tools'))
from spu_disasm import disassemble_spu
from spu_lifter import SPULifter


class PicLoweringAdmissionTests(unittest.TestCase):
    def test_initial_pic_mode_rejects_absolute_control_flow(self):
        for opcode, mnemonic in [(0x60, 'bra'), (0x62, 'brasl')]:
            with self.subTest(mnemonic=mnemonic):
                word = (opcode << 23) | ((0x180 // 4) << 7)
                insns = disassemble_spu(word.to_bytes(4, 'big'), 0x100)
                self.assertEqual(insns[0].mnemonic, mnemonic)
                with self.assertRaisesRegex(ValueError, 'Absolute branch'):
                    SPULifter(relocatable_pic=True).lift_function(insns, 0x100, 0x104)


if __name__ == '__main__':
    unittest.main()
