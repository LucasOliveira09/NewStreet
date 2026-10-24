"""Exercise the actual runtime's four unsupported-call boundaries."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'private/build/boot/fifa_boot.exe'


class BootDiagnosticsTests(unittest.TestCase):
    def test_raw_spu_exit_stops_nested_execution_before_any_later_side_effect(self):
        result = subprocess.run([str(BOOT), '--test-spu-termination', 'exit'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         dict(halted=True, continued=False, stop_code=0x102, mailbox=23))

    def test_raw_spu_zero_branch_and_unsupported_stop_cannot_complete_silently(self):
        for mode, kind in [('zero', 'spu-indirect'), ('fatal', 'spu-stop'), ('fault', 'spu-fault')]:
            with self.subTest(mode=mode):
                result = subprocess.run([str(BOOT), '--test-spu-termination', mode],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                        if line.startswith('[fifa-block] ')))
                self.assertEqual(event['kind'], kind)

    def test_native_spu_cannot_select_another_program_by_shared_entry_address(self):
        result = subprocess.run([str(BOOT), '--test-spu-image-mismatch'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 90, result.stderr)
        event = json.loads(next(line.removeprefix('[fifa-block] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-block] ')))
        self.assertEqual(event['kind'], 'spu-program')
        self.assertEqual(event['value'], 0x10000)
        self.assertNotIn('RUNNING lifted image', result.stderr)

    def test_spu_groups_keep_sparse_numbers_arguments_and_local_store_isolated(self):
        result = subprocess.run([str(BOOT), '--test-spu-groups'], capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(groups=3, threads=4,
            isolated=True, copied_arguments=True, invalid_requests_rejected=True))

    def test_hle_callback_enters_guest_code_with_64bit_arguments_and_thread_identity(self):
        result = subprocess.run([str(BOOT), '--test-callback'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event['argument_sum'], 0x100000024)
        self.assertEqual(event['identity'], 77)
        self.assertEqual(event['toc'], 0x6789)
        self.assertTrue(event['caller_restored'])

    def test_prx_exports_keep_library_nid_kind_and_guest_context(self):
        result = subprocess.run([str(BOOT), '--test-prx'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event['register_result'], 0)
        self.assertEqual(event['function'], 0x12000)
        self.assertEqual(event['variable'], 0x15000)
        self.assertEqual(event['other_library'], 0)
        self.assertEqual(event['call_result'], 42)
        self.assertEqual(event['restored_toc'], 0xABCDE)
        self.assertEqual(event['bad_header_result'], 0x80010002)
        self.assertEqual(event['after_bad_header'], 0x12000)

    def test_native_crash_keeps_exception_diagnostics(self):
        result = subprocess.run([str(BOOT), '--test-native-crash'], capture_output=True,
                                text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        event = json.loads(next(line.removeprefix('[fifa-crash] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-crash] ')))
        self.assertEqual(event['exception'], 0xE0464946)
        self.assertGreater(event['host_rip'], 0)

    def test_native_child_receives_exact_arguments_and_propagates_exit_code(self):
        with tempfile.TemporaryDirectory(prefix='fifa child ') as folder:
            script = Path(folder) / 'capture args.py'
            script.write_text('import sys,json\nprint(json.dumps(sys.argv[1:]))\nsys.exit(37)\n')
            env = os.environ.copy()
            env.update(FIFA_NEXT_EXE=sys.executable, FIFA_NEXT_ELF=str(script))
            result = subprocess.run([str(BOOT), '--test-spawn-child'], capture_output=True,
                                    text=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 37, result.stderr)
        self.assertIn('[fifa-native-child]', result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            'C:/disc with spaces/', '--boot-path', '/dev_bdvd/PS3_GAME/USRDIR/fifazf.self',
            '--guest-arg', 'hello world', '--guest-arg', 'quote"slash\\',
            '--guest-arg', 'a;b', '--guest-arg', ''])

    def test_guest_arguments_do_not_depend_on_a_semicolon_separator(self):
        arguments = ['hello world', 'a;b', '', 'quote"slash\\']
        command = [str(BOOT), '--test-argv', 'unused', '--boot-path', '/dev_bdvd/fifazf.self']
        for value in arguments:
            command += ['--guest-arg', value]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ['/dev_bdvd/fifazf.self'] + arguments)

    def test_spawn_request_preserves_guest_32bit_pointer_arrays(self):
        result = subprocess.run([str(BOOT), '--test-spawn'], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 92, result.stderr)
        event = json.loads(next(line.removeprefix('[fifa-spawn] ') for line in result.stderr.splitlines()
                                if line.startswith('[fifa-spawn] ')))
        self.assertEqual(event['path'], '/dev_bdvd/PS3_GAME/USRDIR/fifazf.self')
        self.assertEqual(event['argv'], ['hello world', 'quote"slash\\'])
        self.assertEqual(event['envp'], ['TEST=1'])
        self.assertEqual(event['priority'], 1001)

    def test_missing_runtime_work_cannot_report_success(self):
        for boundary in ('hle', 'syscall', 'indirect', 'unlifted', 'callback', 'callback-ct', 'spu-workload', 'spu-indirect'):
            with self.subTest(boundary=boundary):
                result = subprocess.run([str(BOOT), '--test-missing', boundary],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 90, result.stderr)
                lines = [line for line in result.stderr.splitlines()
                         if line.startswith('[fifa-block] ')]
                self.assertEqual(len(lines), 1, result.stderr)
                event = json.loads(lines[0].removeprefix('[fifa-block] '))
                self.assertEqual(event['kind'], boundary)
                self.assertEqual(event['guest_lr'], 0x12345678)
                self.assertEqual(event['arguments'][0], 0x1122334455667788)
                self.assertNotIn('faking CELL_OK', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
