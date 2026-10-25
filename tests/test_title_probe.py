import argparse
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from run_title_probe import capture_identity, parse_region, TitleGate


def bitmap(rows, top_down=False):
    width, height = len(rows[0]), len(rows)
    stride = (width * 3 + 3) & ~3
    pixels = b''.join(bytes(sum(row, ())) + b'\0' * (stride - width * 3)
                      for row in (rows if top_down else list(reversed(rows))))
    return (struct.pack('<2sIHHI', b'BM', 54 + len(pixels), 0, 0, 54) +
            struct.pack('<IiiHHIIiiII', 40, width, -height if top_down else height,
                        1, 24, 0, len(pixels), 0, 0, 0, 0) + pixels)


class TitleCaptureIdentityTests(unittest.TestCase):
    def test_delayed_input_requires_current_title_to_remain_visible(self):
        gate = TitleGate({'title'}, 5)
        self.assertFalse(gate.observe('other', 10))
        self.assertFalse(gate.observe('title', 11))
        self.assertFalse(gate.observe('title', 15.9))
        self.assertFalse(gate.observe('other', 16))
        self.assertFalse(gate.observe('title', 20))
        self.assertFalse(gate.observe('title', 24.9))
        self.assertTrue(gate.observe('title', 25))
        self.assertTrue(TitleGate({'title'}, 0).observe('title', 1))

    def test_stable_region_matches_when_prompt_elsewhere_blinks(self):
        reference = bitmap([[(1, 2, 3), (4, 5, 6)], [(7, 8, 9), (10, 11, 12)]])
        blink = bitmap([[(1, 2, 3), (4, 5, 6)], [(0, 0, 0), (255, 255, 255)]])
        self.assertNotEqual(capture_identity(reference), capture_identity(blink))
        self.assertEqual(capture_identity(reference, (0, 0, 2, 1)),
                         capture_identity(blink, (0, 0, 2, 1)))
        changed_title = bitmap([[(0, 0, 0), (4, 5, 6)], [(7, 8, 9), (10, 11, 12)]])
        self.assertNotEqual(capture_identity(reference, (0, 0, 2, 1)),
                            capture_identity(changed_title, (0, 0, 2, 1)))

    def test_top_down_and_bottom_up_pixel_order_match(self):
        rows = [[(1, 2, 3), (4, 5, 6)], [(7, 8, 9), (10, 11, 12)]]
        self.assertEqual(capture_identity(bitmap(rows), (1, 0, 1, 2)),
                         capture_identity(bitmap(rows, True), (1, 0, 1, 2)))

    def test_incomplete_or_invalid_regions_cannot_authorize_input(self):
        image = bitmap([[(1, 2, 3)]])
        for blob, region in [(image[:-1], (0, 0, 1, 1)), (b'BM', (0, 0, 1, 1)),
                             (image, (1, 0, 1, 1)), (image, (0, 0, 0, 1))]:
            with self.subTest(region=region), self.assertRaises(ValueError):
                capture_identity(blob, region)
        self.assertEqual(parse_region('70,70,720,100'), (70, 70, 720, 100))
        for value in ['0,0,0,1', '-1,0,1,1', '1,2,3', 'x,0,1,1']:
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                parse_region(value)


if __name__ == '__main__':
    unittest.main()
