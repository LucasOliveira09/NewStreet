"""Compare actual recompiled game functions against an independent abs oracle.

These tests establish integer return values only, not full CPU conformance,
game startup, graphics, or compatibility with other game revisions.
"""
import random
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "private/build/probe/fifa_function_probe.exe"
MASK64 = (1 << 64) - 1


class NativeProbeTests(unittest.TestCase):
    def check_function(self, address, bits):
        rng = random.Random(30882 + bits)
        values = [0, 1, -1, 7, -7, (1 << (bits - 1)) - 1,
                  -(1 << (bits - 1)), -(1 << (bits - 1)) + 1,
                  (1 << bits) - 1, (1 << bits) + 1]
        values += [rng.getrandbits(64) for _ in range(10000)]
        inputs = [value & MASK64 for value in values]
        result = subprocess.run(
            [str(RUNNER), address],
            input="\n".join(f"{value:x}" for value in inputs) + "\n",
            text=True, capture_output=True, timeout=30, check=True)
        outputs = [int(line, 16) for line in result.stdout.splitlines()]
        self.assertEqual(len(outputs), len(inputs))
        for value, actual in zip(inputs, outputs):
            signed = value & ((1 << bits) - 1)
            if signed >= (1 << (bits - 1)):
                signed -= 1 << bits
            # PPC wraparound leaves signed MIN as MIN, unlike Python abs.
            expected = (signed if signed == -(1 << (bits - 1)) else abs(signed)) & MASK64
            self.assertEqual(actual, expected, f"{address}: input={value:#x}")
        print(f"{address}: {len(inputs)} integer return values passed")

    def test_real_game_abs32(self):
        self.check_function("23d4c", 32)

    def test_real_game_abs64(self):
        self.check_function("261f0", 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
