"""Run a native boot and queue a selected pad input after a reviewed capture.

An input match proves which frame authorized the button, not that the game
accepted it. Inspect the run, frames and next state before claiming navigation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import threading
import time

from run_native import ROOT, run_native


def capture_identity(data, region=None):
    """Hash a whole capture or read pixels in a stable, reviewed BMP region."""
    if region is None:
        return len(data), hashlib.sha256(data).hexdigest()
    if len(data) < 54 or data[:2] != b'BM':
        raise ValueError('Incomplete BMP capture')
    width, signed_height, planes, bits, compression = struct.unpack_from('<iiHHI', data, 18)
    offset = struct.unpack_from('<I', data, 10)[0]
    height = abs(signed_height)
    x, y, w, h = region
    stride = ((width * bits + 31) // 32) * 4
    if (width <= 0 or not height or planes != 1 or bits not in (24, 32) or compression or
            offset < 54 or len(data) < offset + stride * height or
            min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height):
        raise ValueError('Unsupported BMP or out-of-bounds title region')
    digest = hashlib.sha256()
    for row in range(y, y + h):
        physical_row = row if signed_height < 0 else height - row - 1
        start = offset + physical_row * stride + x * (bits // 8)
        digest.update(data[start:start + w * (bits // 8)])
    return width, height, bits, digest.hexdigest()


def parse_region(value):
    try:
        region = tuple(int(part) for part in value.split(','))
        if len(region) != 4 or min(region[:2]) < 0 or min(region[2:]) <= 0:
            raise ValueError()
        return region
    except ValueError:
        raise argparse.ArgumentTypeError('Use x,y,width,height with positive dimensions')


def parse_mask(value):
    try:
        mask = int(value, 0)
        if not 0 <= mask <= 0xFFFF:
            raise ValueError()
        return mask
    except ValueError:
        raise argparse.ArgumentTypeError('Use a pad mask from 0x0000 to 0xFFFF')


class TitleGate:
    def __init__(self, references, delay):
        self.references, self.delay, self.since = references, delay, None

    def observe(self, identity, now):
        if identity not in self.references:
            self.since = None
            return False
        if self.since is None:
            self.since = now
        return now - self.since >= self.delay


class CaptureSequence:
    """Admit each reviewed screen once, strictly in the requested order."""
    def __init__(self, steps):
        self.steps, self.index = steps, 0
        self.gates = [TitleGate(step['references'], step['delay']) for step in steps]

    def observe(self, data, now):
        if self.index == len(self.steps):
            return None
        step = self.steps[self.index]
        identity = capture_identity(data, step['region'])
        if not self.gates[self.index].observe(identity, now):
            return None
        self.index += 1
        return dict(index=self.index - 1, identity=identity, mask=step['mask'],
                    reports=step['reports'], region=step['region'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, help='Private analysis label')
    parser.add_argument('--title-reference', action='append', required=True, type=Path,
                        help='Previously reviewed backend BMP for the screen; repeat for visual variants')
    parser.add_argument('--title-mask', type=parse_mask, default=0x0008,
                        help='PS button mask to queue after the reference screen remains visible (default: Start, 0x0008)')
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--capture-start', type=int, default=3001,
                        help='First guest flip to capture (1..100000); use 1 to observe the opening')
    parser.add_argument('--capture-count', type=int, default=120,
                        help='Number of sampled backend frames (1..120)')
    parser.add_argument('--capture-stride', type=int, default=120,
                        help='Backend frames between captures (1..1000)')
    parser.add_argument('--hold-reports', type=int, default=40,
                        help='Valid reports for the selected input press (1..300)')
    parser.add_argument('--title-delay', type=float, default=0,
                        help='Seconds the latest capture must keep matching the title (0..20)')
    parser.add_argument('--title-region', type=parse_region,
                        help='Stable reviewed region x,y,width,height; omit for whole-image matching')
    parser.add_argument('--confirm-reference', action='append', type=Path,
                        help='Optional reviewed autosave notice BMP; authorize one Cross after Start')
    parser.add_argument('--confirm-region', type=parse_region,
                        help='Stable reviewed confirmation region; omit for whole-image matching')
    args = parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9_-]{0,60}', args.label) or not 10 <= args.timeout <= 600:
        parser.error('Use a safe lowercase label and a timeout from 10 to 600 seconds')
    if not 1 <= args.hold_reports <= 300:
        parser.error('Use --hold-reports from 1 to 300')
    if not 0 <= args.title_delay <= 20:
        parser.error('Use --title-delay from 0 to 20 seconds')
    if not 1 <= args.capture_start <= 100000:
        parser.error('Use --capture-start from 1 to 100000')
    if not 1 <= args.capture_count <= 120:
        parser.error('Use --capture-count from 1 to 120')
    if not 1 <= args.capture_stride <= 1000:
        parser.error('Use --capture-stride from 1 to 1000')
    references = set()
    for path in args.title_reference:
        data = path.read_bytes()
        if not data.startswith(b'BM'):
            parser.error('Title references must be reviewed backend BMP captures')
        try:
            references.add(capture_identity(data, args.title_region))
        except ValueError as error:
            parser.error(str(error))
    confirmations = set()
    for path in args.confirm_reference or []:
        try:
            confirmations.add(capture_identity(path.read_bytes(), args.confirm_region))
        except (OSError, ValueError) as error:
            parser.error(str(error))
    analysis = ROOT / 'private/analysis'
    paths = {key: analysis / f'{args.label}-{suffix}' for key, suffix in {
        'frames': 'frames', 'pad': 'pad.txt', 'audio': 'audio.f32le',
        'result': 'run.json', 'input': 'title-input.json'}.items()}
    if any(path.exists() for path in paths.values()):
        parser.error('Choose an unused label; existing diagnostics will not be overwritten')
    paths['frames'].mkdir(parents=True)
    paths['pad'].write_text('', encoding='ascii')
    os.environ.update(FIFA_SPU_ENTRY_TRACE='1',
        RSX_CAP=f'{args.capture_start}:{args.capture_count}:{args.capture_stride}',
        RSX_CAP_DIR=str(paths['frames']), AUDIO_WAV=str(paths['audio']), PAD_FILE=str(paths['pad']))
    os.environ.setdefault('FIFA_WATCHDOG_AFTER_MS', str(min(args.timeout * 500, 300000)))
    os.environ.setdefault('SPU_PCSAMPLE', '15')
    os.environ.setdefault('SPU_PCSAMPLE_DUMP_AFTER', str(min(args.timeout // 2, 300)))
    # Keep typing in the host window from contaminating the scripted input.
    os.environ.setdefault('PAD_NO_KEYBOARD', '1')
    stop = threading.Event()
    driver = {'status': 'title_not_seen'}

    def drive():
        checked = {}
        steps = [dict(references=references, delay=args.title_delay, region=args.title_region,
                      mask=f'0x{args.title_mask:04X}', reports=args.hold_reports)]
        if confirmations:
            steps.append(dict(references=confirmations, delay=0, region=args.confirm_region,
                              mask='0x4000', reports=40))
        sequence = CaptureSequence(steps)
        while not stop.wait(0.2):
            # A stale title capture cannot authorize an input after the screen
            # has changed. An incomplete newest frame is retried next tick.
            captures = sorted(paths['frames'].glob('*/backbuffer.bmp'),
                              key=lambda path: int(path.parent.name.removeprefix('frame_')))
            for capture in captures[-1:]:
                try:
                    stat = capture.stat()
                    stamp = (stat.st_size, stat.st_mtime_ns)
                    if checked.get(capture) == stamp:
                        continue
                    data = capture.read_bytes()
                    sha256 = hashlib.sha256(data).hexdigest()
                    action = sequence.observe(data, time.monotonic())
                    checked[capture] = stamp
                    if action is None:
                        continue
                    paths['pad'].write_text(f"{action['mask']} {action['reports']}", encoding='ascii')
                    event = dict(status=('input_queued_after_exact_screen_match' if action['index'] == 0
                                         else 'cross_queued_after_exact_confirmation_match'),
                        capture=str(capture.relative_to(ROOT)), sha256=sha256,
                        matching_region=action['region'], match_sha256=action['identity'][-1],
                        time_ns=time.time_ns(), mask=action['mask'], reports=action['reports'])
                    if action['index'] == 0:
                        driver.update(event, title_delay_seconds=args.title_delay)
                    else:
                        driver['confirmation'] = event
                    try:
                        paths['input'].write_text(json.dumps(driver, indent=2) + '\n', encoding='utf-8')
                    except OSError as error:
                        driver['metadata_error'] = str(error)
                    if sequence.index == len(steps):
                        return
                except (OSError, ValueError):
                    # A frame can still be open in the capture writer; retry.
                    continue

    thread = threading.Thread(target=drive, daemon=True)
    thread.start()
    try:
        report = run_native(timeout=args.timeout, observe_assets=True)
    finally:
        stop.set()
        thread.join(timeout=2)
        paths['input'].write_text(json.dumps(driver, indent=2) + '\n', encoding='utf-8')
    paths['result'].write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    summary = {key: report[key] for key in ('exit_code', 'elapsed_seconds', 'logs')}
    summary['title_input'] = driver
    summary['faults'] = [event for event in report['events'] if event['type'] in ('fifa-block', 'fifa-crash')]
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
