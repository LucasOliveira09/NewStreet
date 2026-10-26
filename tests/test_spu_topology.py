"""Verify original static initialization before admitting the topology job."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OriginalTopologyConstructorsTests(unittest.TestCase):
    def test_original_constructor_sequence_returns_without_modifying_code(self):
        self.check_original_constructors('aififa_topologycache', '--test-spu-topology-constructors',
            '06cb06e15272bef85f694bb916226be58677518355088bb38c2d55ddbfa254b7', 7)

    def test_original_railtracks_constructors_return_without_modifying_code(self):
        self.check_original_constructors('railtracks_movetotarget', '--test-spu-railtracks-constructors',
            'f0d60bc73fa56d84a06dc6085e2308b6d502a416d5b27a7997fb76d2bb62cf8b', 4)

    def test_original_secondary_ant_constructors_return_without_modifying_code(self):
        self.check_original_constructors('ant_kernel_secondary', '--test-spu-ant-secondary-constructors',
            '18664f851235de1b95b6fc827b73bfc18b9714425043fdcbf416a029373a94e4', 2)

    def test_original_vbr_clip_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_vbrcodec_clipnode', '--test-spu-ant-vbr-constructors',
            'e10fdf3acb9f374397a13bd37f843cf866891f8c7432a5fb9b545b3a13af65d2')

    def test_original_default_pose_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_defaultposenode_dofset', '--test-spu-ant-pose-constructors',
            'd4ab78e9f9c3c0fc453b18fb06cdbadd47481cec4e9a4d0da6c0ffb36b1f2504')

    def test_original_clear_activity_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_clearactivitymasknode_exec', '--test-spu-ant-clear-constructors',
            '5ebd1592be5f06df6d2176da36b700bb75511693b853b3051ac16332d8f685ba')

    def test_original_set_dof_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_setdofsetnode_exec', '--test-spu-ant-setdof-constructors',
            'c7c203e58e7e0005165cd965445d4c56aa2d07aecc9e3ac31d2bacfa9dcd858f')

    def test_original_trajectory_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_deltatrajectoryplugin', '--test-spu-ant-trajectory-constructors',
            'f0eed6604a62a7f6fc8745b17cd79ebf53f2556c1ece802da7e0c80d0ca1afa6')

    def test_original_scratch_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_scratchmemclear_exec', '--test-spu-ant-scratch-constructors',
            '86b9892f5273873cac6129197232cde4c34474992d3ee34d3981aa673e7ef36d')

    def test_original_globalpose_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_posetoglobalplugin', '--test-spu-ant-globalpose-constructors',
            '1e8f997d11c7d9f333236c9381ea8ad1145a275e31b470c40b870584bce15b2d')

    def test_original_singledof_constructors_relocate_at_four_positions(self):
        self.check_pic_constructors('ant_setdofnode_exec', '--test-spu-ant-singledof-constructors',
            'c83ad4290fd1d28dfa254ddb69ccca36bda3df8a8216fda318591dee82114cdf')

    def check_pic_constructors(self, module, command, sha256):
        image = ROOT / 'private/generated/spu_overlays' / module / 'image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), sha256)
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
            command, str(image)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=12, positions=4, code_preserved=True,
            relocated_data_consistent=True, ai_algorithm_validated=False))

    def check_original_constructors(self, module, command, sha256, count):
        image = ROOT / 'private/generated/spu_overlays' / module / 'image.bin'
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), sha256)
        result = subprocess.run([str(ROOT / 'private/build/fifazf_full/fifa_boot.exe'),
            command, str(image)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), dict(
            original_constructors=count, code_preserved=True, ai_algorithm_validated=False))
