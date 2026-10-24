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
        for boundary in ('hle', 'syscall', 'indirect', 'unlifted'):
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
                self.assertNotIn('faking CELL_OK', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
