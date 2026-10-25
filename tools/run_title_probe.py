"""Run a native boot and queue one Start only after an exact reviewed title capture.

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, help='Unused private analysis label')
    parser.add_argument('--title-reference', action='append', required=True, type=Path,
                        help='Previously reviewed title BMP; repeat for blink variants')
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--title-region', type=parse_region,
                        help='Stable reviewed region x,y,width,height; omit for whole-image matching')
    args = parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9_-]{0,60}', args.label) or not 10 <= args.timeout <= 600:
        parser.error('Use a safe lowercase label and a timeout from 10 to 600 seconds')
    references = set()
    for path in args.title_reference:
        data = path.read_bytes()
        if not data.startswith(b'BM'):
            parser.error('Title references must be reviewed backend BMP captures')
        try:
            references.add(capture_identity(data, args.title_region))
        except ValueError as error:
            parser.error(str(error))
    analysis = ROOT / 'private/analysis'
    paths = {key: analysis / f'{args.label}-{suffix}' for key, suffix in {
        'frames': 'frames', 'pad': 'pad.txt', 'audio': 'audio.f32le',
        'result': 'run.json', 'input': 'title-input.json'}.items()}
    if any(path.exists() for path in paths.values()):
        parser.error('Choose an unused label; existing diagnostics will not be overwritten')
    paths['frames'].mkdir(parents=True)
    paths['pad'].write_text('', encoding='ascii')
    os.environ.update(FIFA_SPU_ENTRY_TRACE='1', RSX_CAP='3001:120:120',
        RSX_CAP_DIR=str(paths['frames']), AUDIO_WAV=str(paths['audio']), PAD_FILE=str(paths['pad']))
    os.environ.setdefault('FIFA_WATCHDOG_AFTER_MS', str(min(args.timeout * 500, 300000)))
    os.environ.setdefault('SPU_PCSAMPLE', '15')
    os.environ.setdefault('SPU_PCSAMPLE_DUMP_AFTER', str(min(args.timeout // 2, 300)))
    stop = threading.Event()
    driver = {'status': 'title_not_seen'}

    def drive():
        checked = {}
        while not stop.wait(0.2):
            for capture in sorted(paths['frames'].glob('*/backbuffer.bmp')):
                try:
                    stat = capture.stat()
                    stamp = (stat.st_size, stat.st_mtime_ns)
                    if checked.get(capture) == stamp:
                        continue
                    data = capture.read_bytes()
                    identity = capture_identity(data, args.title_region)
                    checked[capture] = stamp
                    if identity not in references:
                        continue
                    paths['pad'].write_text('0x0008 40', encoding='ascii')
                    driver.update(status='start_queued_after_exact_title_match',
                        capture=str(capture.relative_to(ROOT)), sha256=hashlib.sha256(data).hexdigest(),
                        matching_region=args.title_region, match_sha256=identity[-1],
                        time_ns=time.time_ns(), mask='0x0008', reports=40)
                    try:
                        paths['input'].write_text(json.dumps(driver, indent=2) + '\n', encoding='utf-8')
                    except OSError as error:
                        driver['metadata_error'] = str(error)
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
