"""Check the original game's translated digital/pressure setter, not full CPU conformance."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalInputBitsetTests(unittest.TestCase):
    def test_original_game_input_setter_matches_bit_and_byte_oracles(self):
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                                 '--test-fifa-input-bitset'], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]),
                         dict(original_function='0x1434db8', cases=384,
                              digital_bits=True, pressure=True, bounds=True))


if __name__ == '__main__':
    unittest.main()
