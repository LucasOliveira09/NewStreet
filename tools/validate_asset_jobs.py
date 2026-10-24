"""Compare captured native job output with independent host decompression.

RefPack bitstream reference: OpenSAGE's clean-room RefPackStream implementation
https://github.com/OpenSAGE/OpenSAGE/blob/master/src/OpenSage.FileFormats.RefPack/RefPackStream.cs
This diagnostic decoder never supplies data to the game or replaces guest code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zlib


def refpack_decode(data, limit=4 * 1024 * 1024):
    if len(data) < 5 or data[0] & 0x3e != 0x10 or data[1] != 0xfb:
        raise ValueError('Invalid RefPack header')
    width = 4 if data[0] & 0x80 else 3
    pos = 2 + (width if data[0] & 1 else 0)
    if pos + width > len(data):
        raise ValueError('Truncated RefPack size')
    size = int.from_bytes(data[pos:pos + width], 'big')
    pos += width
    if size > limit:
        raise ValueError('RefPack output exceeds diagnostic limit')
    output = bytearray()

    def take(count):
        nonlocal pos
        if pos + count > len(data):
            raise ValueError('Truncated RefPack command')
        part = data[pos:pos + count]
        pos += count
        return part

    while True:
        control, = take(1)
        stop = False
        if control < 0x80:
            second, = take(1)
            literal, count = control & 3, ((control >> 2) & 7) + 3
            distance = ((control & 0x60) << 3) + second + 1
        elif control < 0xc0:
            second, third = take(2)
            literal, count = second >> 6, (control & 0x3f) + 4
            distance = ((second & 0x3f) << 8) + third + 1
        elif control < 0xe0:
            second, third, fourth = take(3)
            literal, count = control & 3, ((control & 12) << 6) + fourth + 5
            distance = ((control & 16) << 12) + (second << 8) + third + 1
        else:
            literal = (control & 3) if control >= 0xfc else ((control & 31) + 1) * 4
            count, distance, stop = 0, 0, control >= 0xfc
        if len(output) + literal + count > size:
            raise ValueError('RefPack command exceeds declared output')
        output.extend(take(literal))
        if count and not 0 < distance <= len(output):
            raise ValueError('Invalid RefPack lookback')
        for _ in range(count):
            output.append(output[-distance])
        if stop:
            break
    if len(output) != size:
        raise ValueError('RefPack output size mismatch')
    return bytes(output)


def validate(folder):
    results = []
    metadata_incomplete = set()
    for meta in sorted(folder.glob('*.json')):
        item = dict(job=meta.stem, codec=None, matches=False)
        try:
            job = json.loads(meta.read_text(encoding='utf-8'))
            if not isinstance(job, dict) or job.get('codec') not in ('refpack', 'zlib'):
                raise ValueError('Missing or invalid job codec')
            if any(key not in job for key in ('captured', 'input_bytes', 'output_bytes')):
                raise ValueError('Incomplete job metadata')
        except (ValueError, OSError) as error:
            item['error'] = 'Invalid or interrupted metadata: ' + str(error)
            metadata_incomplete.add(meta.stem)
            results.append(item)
            continue
        item['codec'] = job['codec']
        try:
            if not job['captured']:
                raise ValueError('Native output was not captured')
            compressed = meta.with_suffix('.input').read_bytes()
            actual = meta.with_suffix('.output').read_bytes()
            if len(compressed) != job['input_bytes'] or len(actual) != job['output_bytes']:
                raise ValueError('Capture length differs from job metadata')
            if job['codec'] == 'refpack':
                expected = refpack_decode(compressed)
            else:
                # AssetStream feeds a raw DEFLATE block (no zlib/gzip wrapper).
                stream = zlib.decompressobj(-15)
                expected = stream.decompress(compressed, 4 * 1024 * 1024 + 1)
                if not stream.eof or len(expected) > 4 * 1024 * 1024:
                    raise ValueError('Incomplete or oversized DEFLATE stream')
            item.update(input_bytes=len(compressed), output_bytes=len(actual),
                        expected_bytes=len(expected), matches=actual == expected,
                        sha256=hashlib.sha256(actual).hexdigest())
            if actual != expected:
                item['first_difference'] = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                                                min(len(actual), len(expected)))
        except (ValueError, OSError, zlib.error) as error:
            item['error'] = str(error)
        results.append(item)
    completed = {j['job'] for j in results}
    incomplete = sorted(metadata_incomplete | {
        path.stem for path in folder.glob('*.input') if path.stem not in completed})
    return dict(jobs=results, total=len(results), passed=sum(j['matches'] for j in results),
                capture_limit_per_codec=32, exhaustive=False,
                incomplete=incomplete,
                all_passed=bool(results) and all(j['matches'] for j in results) and not incomplete)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = validate(args.folder)
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    raise SystemExit(0 if report['all_passed'] else 1)
