import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CommonAntConstructorsTests(unittest.TestCase):
    def test_all_reviewed_original_constructors_at_four_positions(self):
        report = json.loads((ROOT / 'reports/spu-raw-inventory.json').read_text(encoding='utf-8'))
        reviewed = {item['source_ea']: item for item in report['images']
                    if 'common_crt_review' in item}
        config = json.loads((ROOT / 'spu_overlays.json').read_text(encoding='utf-8'))
        cases = [item for item in config['overlays']
                 if item.get('constructor_profile') == 'ant_common_v1']
        self.assertEqual(len(cases), report['common_ant_count'])
        self.assertEqual({item['source_ea'] for item in cases}, set(reviewed))
        for item in cases:
            with self.subTest(module=item['name']):
                original = reviewed[item['source_ea']]
                shape = original['common_crt_review']
                self.assertEqual(item['sha256'], original['sha256'])
                self.assertEqual(int(item['code_end'], 0), shape['code_end'])
                self.assertEqual(list(map(lambda value: int(value, 0), item['extra_entries'])),
                                 shape['constructors'])
                image = ROOT / 'private/generated/spu_overlays' / item['name'] / 'image.bin'
                self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), item['sha256'])
                arguments = [item['source_ea'], item['size'], item['code_end'],
                             *item['extra_entries'], '0x8000']
                result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
                    '--test-spu-ant-family-constructors', str(image), *arguments],
                    capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
                    original_constructors=12, positions=4, code_preserved=True,
                    relocated_data_consistent=True, ai_algorithm_validated=False))


if __name__ == '__main__':
    unittest.main()
