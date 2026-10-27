"""Apply only reviewed, versioned changes on the locked upstream checkout."""
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_applied_series(sdk, expected, patches):
    """Check the final patch-series state even when a later patch edits an
    earlier patch's context and makes its individual reverse-check impossible.
    """
    paths = set()
    for patch in patches:
        for line in patch.read_text().splitlines():
            if line.startswith('diff --git a/'):
                paths.add(line.split()[2][2:])

    temp_root = ROOT / 'private/analysis'
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='patch-series-', dir=temp_root) as name:
        worktree = Path(name) / 'sdk'
        subprocess.run(['git', '-C', str(sdk), 'worktree', 'add', '--detach', '--quiet',
                        str(worktree), expected], check=True)
        try:
            for patch in patches:
                subprocess.run(['git', '-C', str(worktree), 'apply', str(patch)], check=True)
            for relative in paths:
                actual = sdk / relative
                wanted = worktree / relative
                if actual.exists() != wanted.exists():
                    return False
                # Git for Windows may materialize identical patched text with
                # CRLF on one side and LF on the temporary worktree.
                if actual.exists() and actual.read_text() != wanted.read_text():
                    return False
            return True
        finally:
            subprocess.run(['git', '-C', str(sdk), 'worktree', 'remove', '--force',
                            str(worktree)], check=True)


def apply():
    sdk = ROOT / 'vendor/ps3recomp'
    expected = json.loads((ROOT / 'toolchain.lock.json').read_text())['ps3recomp']['commit']
    actual = subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected:
        raise RuntimeError('SDK revision differs from the lock; review patches before applying')
    patches = sorted((ROOT / 'patches').glob('*.patch'))
    for patch in patches:
        command = ['git', '-C', str(sdk), 'apply']
        check = subprocess.run(command + ['--check', str(patch)], capture_output=True)
        if check.returncode == 0:
            subprocess.run(command + [str(patch)], check=True)
            print('Applied', patch.name)
        elif subprocess.run(command + ['--reverse', '--check', str(patch)],
                            capture_output=True).returncode == 0:
            print('Already applied', patch.name)
        else:
            if verify_applied_series(sdk, expected, patches):
                print('Verified complete patch series already applied')
                return
            raise RuntimeError(f'Patch conflict: {patch.name}: {check.stderr.decode(errors="replace")}')


if __name__ == '__main__':
    apply()
