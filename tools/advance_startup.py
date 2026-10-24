"""Run native startup and lift observed missing targets; never fake a handler.

Stops on ISA/HLE gaps, crashes, repeated targets or an execution timeout so those
require an actual implementation/debugging step. Each attempt retains its logs.
"""
import argparse
import json
import subprocess
from pathlib import Path
from run_native import run_native

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=4)
    parser.add_argument('--limit', type=int, default=512)
    parser.add_argument('--timeout', type=int, default=20)
    args = parser.parse_args()
    attempts = []
    observed = set()
    for _ in range(args.steps):
        run = run_native('startup', args.timeout, direct=True)
        code, logs = run['exit_code'], run['logs']
        blocks = [event['data'] for event in run['events'] if event['type'] == 'fifa-block']
        event = blocks[-1] if blocks else None
        attempt = dict(exit_code=code, block=event, logs=logs)
        attempts.append(attempt)
        print(json.dumps(attempt), flush=True)
        if code != 90 or not event or event['kind'] not in ('indirect', 'unlifted', 'continuation'):
            break
        address = event['value']
        if address in observed:
            print('Repeated target: inspect function boundaries and dispatch before retrying.', flush=True)
            break
        observed.add(address)
        build_log = ROOT / logs / 'build.log'
        with build_log.open('wb') as output:
            command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                       '-File', str(ROOT / 'tools/build.ps1'), '-Target', 'Game',
                       '-StartupLimit', str(args.limit), '-AddFunction', hex(address)]
            result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            print('Build failed; inspect', build_log, flush=True)
            break
    report = ROOT / 'private/analysis/startup-attempts.json'
    report.write_text(json.dumps(attempts, indent=2) + '\n')


if __name__ == '__main__':
    main()
