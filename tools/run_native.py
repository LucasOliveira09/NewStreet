"""Run the native EBOOT -> FIFAZF chain and retain diagnostics for both processes.

Timeouts terminate only the process tree started by this command. No emulator or
CPU interpreter is used. Exit 90 is a missing implementation, never boot success.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_native_events(stderr):
    """Retain complete events and explicitly report interrupted diagnostics."""
    prefixes = ('[fifa-block] ', '[fifa-spawn] ', '[fifa-crash] ',
                '[fifa-spu-state] ', '[fifa-memory] ', '[fifa-spu-entry] ')
    events, errors = [], []
    for number, line in enumerate(stderr.decode('utf-8', errors='replace').splitlines(), 1):
        for prefix in prefixes:
            if not line.startswith(prefix):
                continue
            kind = prefix[1:prefix.index(']')]
            try:
                data = json.loads(line[len(prefix):])
                if not isinstance(data, dict):
                    raise ValueError('Event payload must be an object')
            except ValueError as error:
                errors.append(dict(line=number, type=kind, error=str(error), raw=line[:4096]))
            else:
                events.append(dict(type=kind, data=data))
            break
    return events, errors


def run_native(profile='full', timeout=30, direct=False, syscall_trace=False, capture=False, observe_assets=False):
    build = 'fifazf_full' if profile == 'full' else 'fifazf'
    main_exe = ROOT / 'private/build' / build / 'fifa_boot.exe'
    boot_exe = ROOT / 'private/build/boot/fifa_boot.exe'
    for path in (main_exe, boot_exe, ROOT / 'private/EBOOT.elf', ROOT / 'private/FIFAZF.elf'):
        if not path.is_file():
            raise FileNotFoundError(path)
    output = ROOT / 'private/analysis/runs' / str(time.time_ns())
    output.mkdir(parents=True)
    env = os.environ.copy()
    env.setdefault('PS3_HLE_TRACE', '200')
    env.pop('PS3_SCTRACE', None)
    (output / 'spu').mkdir()
    env['FIFA_SPU_DUMP_DIR'] = str(output / 'spu')
    (output / 'ppu').mkdir()
    env['FIFA_PPU_DUMP_DIR'] = str(output / 'ppu')
    (output / 'shaders').mkdir()
    env['RSX_FP_FAIL_DUMP_DIR'] = str(output / 'shaders')
    if observe_assets:
        (output / 'jobs').mkdir()
        env['FIFA_SPU_JOB_TRACE_DIR'] = str(output / 'jobs')
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
    # Keep diagnostics readable while the game is running. Large traces should
    # go to disk directly, rather than accumulate in communicate()'s buffers.
    with (output / 'stdout.log').open('wb') as stdout_file, (output / 'stderr.log').open('wb') as stderr_file:
        process = subprocess.Popen(command, stdout=stdout_file, stderr=stderr_file, env=env, cwd=ROOT)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # The EBOOT host waits for its native child. Kill descendants before
            # closing the parent so the child cannot survive an unattended timeout.
            cleanup = subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                     capture_output=True, timeout=10)
            (output / 'timeout-cleanup.log').write_bytes(cleanup.stdout + cleanup.stderr)
            process.wait(timeout=10)
            code = 'timeout'
    # Preserve measured process status even if later log parsing or independent
    # asset validation fails. Concurrent fatal diagnostics can be interrupted.
    elapsed = round(time.monotonic() - started, 3)
    (output / 'process-exit.json').write_text(json.dumps(dict(
        pid=process.pid, exit_code=code, elapsed_seconds=elapsed), indent=2) + '\n', encoding='utf-8')
    stderr = (output / 'stderr.log').read_bytes()
    events, parse_errors = parse_native_events(stderr)
    report = dict(profile=profile, direct=direct, exit_code=code,
                  elapsed_seconds=elapsed, logs=str(output.relative_to(ROOT)),
                  events=events, event_parse_errors=parse_errors)
    captures = []
    for manifest in sorted((output / 'rsxcap').glob('*/manifest.txt')):
        bitmap = manifest.with_name('backbuffer.bmp')
        header = manifest.read_text(encoding='utf-8').splitlines()[0]
        match = re.fullmatch(r'frame_count=(\d+) draws=(\d+) backbuffer=(\d+)x(\d+)', header)
        if match and bitmap.is_file():
            captures.append(dict(frame=int(match[1]), draws=int(match[2]),
                                 width=int(match[3]), height=int(match[4]),
                                 bitmap=str(bitmap.relative_to(ROOT)),
                                 sha256=hashlib.sha256(bitmap.read_bytes()).hexdigest()))
    # A capture is evidence for visual review, never automatic menu/gameplay success.
    report['graphics_captures'] = captures
    if observe_assets:
        from validate_asset_jobs import validate
        report['asset_jobs'] = validate(output / 'jobs')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['startup', 'full'], default='full')
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--direct', action='store_true')
    parser.add_argument('--syscall-trace', action='store_true')
    parser.add_argument('--capture', action='store_true', help='Read back the first backend frame with draw operations')
    parser.add_argument('--observe-assets', action='store_true', help='Capture completed native decompression jobs and compare independent output')
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error('timeout must be positive')
    report = run_native(args.profile, args.timeout, args.direct, args.syscall_trace, args.capture, args.observe_assets)
    print(json.dumps(report, indent=2))
    # Returning zero here only means the diagnostic run was recorded. Inspect
    # exit_code and game evidence; this tool cannot declare gameplay success.


if __name__ == '__main__':
    main()
