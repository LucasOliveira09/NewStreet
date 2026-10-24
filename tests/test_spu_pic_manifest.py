import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from lift_spu_overlays import expand_overlays, validate_pic_header


class PicManifestTests(unittest.TestCase):
    def test_pic_manifest_produces_one_canonical_image_without_changing_historical_bases(self):
        item = dict(name='fixture', ls_base='0x100', entry='0x130',
                    code_start='0x130', code_end='0x180',
                    additional_ls_bases=['0x900', '0x1800'], relocatable_pic=True)
        generated = list(expand_overlays([item]))
        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0]['ls_base'], '0x100')
        self.assertNotIn('additional_ls_bases', generated[0])
        self.assertEqual(item['additional_ls_bases'], ['0x900', '0x1800'])

    def test_pic_manifest_flag_is_explicitly_boolean(self):
        for flag in ('false', 1, None):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                list(expand_overlays([dict(name='fixture', ls_base='0x100', relocatable_pic=flag)]))

    def test_pic_header_must_declare_supported_pic_mode_and_relative_entry(self):
        blob = bytearray(48)
        blob[16:20] = (0x30).to_bytes(4, 'big')
        blob[28:32] = (0x80000000).to_bytes(4, 'big')
        blob[40:44] = (1).to_bytes(4, 'big')
        validate_pic_header(bytes(blob), 0x30)
        malformed = [bytes(blob[:32])]
        for offset, value in [(28, 0), (28, 0x80000001), (40, 0), (16, 0x40)]:
            changed = bytearray(blob)
            changed[offset:offset+4] = value.to_bytes(4, 'big')
            malformed.append(bytes(changed))
        for data in malformed:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_pic_header(data, 0x30)


if __name__ == '__main__':
    unittest.main()
