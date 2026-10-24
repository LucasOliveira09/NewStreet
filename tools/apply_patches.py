"""Apply only reviewed, versioned changes on the locked upstream checkout."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply():
    sdk = ROOT / 'vendor/ps3recomp'
    expected = json.loads((ROOT / 'toolchain.lock.json').read_text())['ps3recomp']['commit']
    actual = subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected:
        raise RuntimeError('SDK revision differs from the lock; review patches before applying')
    for patch in sorted((ROOT / 'patches').glob('*.patch')):
        command = ['git', '-C', str(sdk), 'apply']
        check = subprocess.run(command + ['--check', str(patch)], capture_output=True)
        if check.returncode == 0:
            subprocess.run(command + [str(patch)], check=True)
            print('Applied', patch.name)
        elif subprocess.run(command + ['--reverse', '--check', str(patch)],
                            capture_output=True).returncode == 0:
            print('Already applied', patch.name)
        else:
            raise RuntimeError(f'Patch conflict: {patch.name}: {check.stderr.decode(errors="replace")}')


if __name__ == '__main__':
    apply()
