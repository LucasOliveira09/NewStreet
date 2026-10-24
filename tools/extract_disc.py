"""Extract the PS3_GAME tree, verify hashes, and preserve the source ISO."""
import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from iso9660 import IsoImage
from udf_image import UdfImage

ROOT = Path(__file__).resolve().parents[1]


def extract(iso_path, destination, filesystem='udf'):
    destination = destination.resolve()
    if not destination.is_relative_to((ROOT / 'private').resolve()):
        raise ValueError('Game data destination must stay inside project private/')
    destination.mkdir(parents=True, exist_ok=True)
    manifest, total, started = [], 0, time.monotonic()
    with iso_path.open('rb') as source:
        iso = UdfImage(source) if filesystem == 'udf' else IsoImage(source)
        game = next(e for e in iso.children(iso.root) if e.name == 'PS3_GAME' and e.directory)
        for path, entry in iso.files(game, 'PS3_GAME/'):
            output = destination / path
            output.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            if output.exists():
                with output.open('rb') as existing:
                    for chunk in iso.chunks(entry):
                        digest.update(chunk)
                        if existing.read(len(chunk)) != chunk:
                            raise ValueError(f'Existing file differs from ISO: {output}')
                    if existing.read(1):
                        raise ValueError(f'Existing file has extra data: {output}')
            else:
                with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as target:
                    temporary = Path(target.name)
                    try:
                        for chunk in iso.chunks(entry):
                            target.write(chunk)
                            digest.update(chunk)
                    except BaseException:
                        target.close()
                        temporary.unlink(missing_ok=True)
                        raise
                try:
                    os.replace(temporary, output)
                finally:
                    temporary.unlink(missing_ok=True)
            total += entry.size
            manifest.append(dict(path=path, size=entry.size, extents=len(entry.extents), sha256=digest.hexdigest()))
            print(f'{len(manifest):4d} {total / 1048576:8.1f} MiB  {path}', flush=True)
    (destination / 'extraction-manifest.json').write_text(json.dumps({
        'source': str(iso_path.resolve()), 'filesystem': filesystem, 'files': manifest, 'bytes': total,
        'seconds': round(time.monotonic() - started, 2)}, indent=2), encoding='utf-8')
    print(f'Extracted/verified {len(manifest)} files; {total} bytes', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'private/disc')
    parser.add_argument('--filesystem', choices=['udf', 'iso9660'], default='udf',
                        help='UDF preserves PS3 filenames; ISO9660 is an explicit diagnostic fallback')
    args = parser.parse_args()
    extract(args.iso, args.output, args.filesystem)
