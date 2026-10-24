"""Run the native EBOOT -> FIFAZF chain and retain diagnostics for both processes.

Timeouts terminate only the process tree started by this command. No emulator or
CPU interpreter is used. Exit 90 is a missing implementation, never boot success.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_native(profile='full', timeout=30, direct=False, syscall_trace=False, capture=False):
    build = 'fifazf_full' if profile == 'full' else 'fifazf'
    main_exe = ROOT / 'private/build' / build / 'fifa_boot.exe'
    boot_exe = ROOT / 'private/build/boot/fifa_boot.exe'
    for path in (main_exe, boot_exe, ROOT / 'private/EBOOT.elf', ROOT / 'private/FIFAZF.elf'):
        if not path.is_file():
            raise FileNotFoundError(path)
    output = ROOT / 'private/analysis/runs' / str(time.time_ns())
    output.mkdir(parents=True)
    env = os.environ.copy()
    env['PS3_HLE_TRACE'] = '200'
    env.pop('PS3_SCTRACE', None)
    (output / 'spu').mkdir()
    env['FIFA_SPU_DUMP_DIR'] = str(output / 'spu')
    (output / 'ppu').mkdir()
    env['FIFA_PPU_DUMP_DIR'] = str(output / 'ppu')
    for mount in ('HDD0', 'HDD1'):
        key = 'PS3_' + mount + '_ROOT'
        if not env.get(key):
            storage = ROOT / 'private/userdata' / ('dev_' + mount.lower())
            storage.mkdir(parents=True, exist_ok=True)
            env[key] = str(storage)
    if syscall_trace:
        env['PS3_SCTRACE'] = '1'
    if capture:
        env.update(RSX_CAP='1:1', RSX_CAP_DIR=str(output / 'rsxcap'))
    command = [str(boot_exe), str(ROOT / 'private/EBOOT.elf'), str(ROOT / 'private/disc')]
    if direct:
        request = json.loads((ROOT / 'private/analysis/spawn-request.json').read_text())
        if request['envp'] or request['data_size']:
            raise RuntimeError('Implement environment/process-data transport before running this request')
        command = [str(main_exe), str(ROOT / 'private/FIFAZF.elf'), str(ROOT / 'private/disc'),
                   '--boot-path', request['path']]
        for value in request['argv']:
            command.extend(['--guest-arg', value])
        env.pop('FIFA_NEXT_EXE', None)
        env.pop('FIFA_NEXT_ELF', None)
    else:
        env.update(FIFA_NEXT_EXE=str(main_exe), FIFA_NEXT_ELF=str(ROOT / 'private/FIFAZF.elf'))
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=ROOT)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        code = process.returncode
    except subprocess.TimeoutExpired:
        # The EBOOT host waits for its native child. Kill descendants before
        # closing the parent so the child cannot survive an unattended timeout.
        cleanup = subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                 capture_output=True, timeout=10)
        (output / 'timeout-cleanup.log').write_bytes(cleanup.stdout + cleanup.stderr)
        stdout, stderr = process.communicate(timeout=10)
        code = 'timeout'
    (output / 'stdout.log').write_bytes(stdout)
    (output / 'stderr.log').write_bytes(stderr)
    events = []
    for line in stderr.decode('utf-8', errors='replace').splitlines():
        for prefix in ('[fifa-block] ', '[fifa-spawn] ', '[fifa-crash] ', '[fifa-spu-state] ', '[fifa-memory] '):
            if line.startswith(prefix):
                events.append({'type': prefix[1:prefix.index(']')], 'data': json.loads(line[len(prefix):])})
    report = dict(profile=profile, direct=direct, exit_code=code,
                  elapsed_seconds=round(time.monotonic() - started, 3),
                  logs=str(output.relative_to(ROOT)), events=events)
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['startup', 'full'], default='full')
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--direct', action='store_true')
    parser.add_argument('--syscall-trace', action='store_true')
    parser.add_argument('--capture', action='store_true', help='Read back the first backend frame with draw operations')
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error('timeout must be positive')
    report = run_native(args.profile, args.timeout, args.direct, args.syscall_trace, args.capture)
    print(json.dumps(report, indent=2))
    # Returning zero here only means the diagnostic run was recorded. Inspect
    # exit_code and game evidence; this tool cannot declare gameplay success.


if __name__ == '__main__':
    main()
