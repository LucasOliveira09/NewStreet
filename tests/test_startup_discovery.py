"""Real PPC branch decoding must survive function-boundary refinement."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from lift_startup import discover_startup


class StartupDiscoveryTests(unittest.TestCase):
    def discover(self, words, starts, roots, limit=100):
        blob = struct.pack('>' + 'I' * len(words), *words)
        return discover_startup(starts, {}, [(0x100, 0x100 + len(blob))],
                                [(0x100, blob)], [(0x100, blob)], 0, roots, limit)

    def test_later_call_splits_an_earlier_branch_and_discovers_its_new_external_target(self):
        # First pass sees bne 0x130 INSIDE [0x100,0x140). The later function
        # branches into 0x110, splitting that range. On the second pass 0x130
        # is now external to [0x100,0x110), so it needs its own emitted entry.
        words = [0x60000000] * (0x48 // 4)
        words[0:4] = [0x2c030000, 0x4082002c, 0x3860000a, 0x4e800020]
        words[4:6] = [0x3880000b, 0x4e800020]
        words[12:14] = [0x38600014, 0x4e800020]
        words[16:18] = [0x4bffffd0, 0x4e800020]
        selected, starts, _, pending, decode = self.discover(words, {0x100, 0x140}, [0x100, 0x140])
        self.assertIn(0x110, selected)
        self.assertIn(0x130, selected)
        self.assertIn(0x130, starts)
        self.assertFalse(pending)
        self.assertEqual(decode(0x100)[-1].addr + 4, 0x110)
        self.assertEqual(decode(0x130)[0].mnemonic, 'li')

    def test_self_loop_terminates_discovery_without_inventing_functions(self):
        selected, _, _, pending, _ = self.discover([0x48000000], {0x100}, [0x100])
        self.assertEqual(selected, {0x100})
        self.assertFalse(pending)

    def test_limit_leaves_unvisited_calls_explicitly_pending(self):
        selected, _, _, pending, _ = self.discover(
            [0x48000009, 0x4e800020, 0x38600014, 0x4e800020], {0x100}, [0x100], limit=1)
        self.assertEqual(selected, {0x100})
        self.assertTrue(pending)


if __name__ == '__main__':
    unittest.main(verbosity=2)
