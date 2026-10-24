"""Read the ISO9660 view and copy the two inspected executables to private/.

The original ISO is opened read-only. UDF is not used: pycdlib 1.22.0 rejected
the UDF file-set descriptor of this image during the first investigation.
Only the inspected BLUS30882 binaries are accepted; existing files must match.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTOR = 2048
EXPECTED = {
    'EBOOT.BIN': 'b8cccf020e5587c1d263513843ae2cdacac497dfb2967d94f23a51232b8a0f8a',
    'FIFAZF.SELF': 'a7a1c01365c7383f8b1434de84ad8fc33f99a8bbf36006d4ec77cda271441eb9',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    args = parser.parse_args()
    image_size = args.iso.stat().st_size
    with args.iso.open('rb') as source:
        def read_at(offset, size):
            if offset < 0 or size < 0 or offset + size > image_size or size > 64 * 1024 * 1024:
                raise ValueError('ISO read outside the image or project read limit')
            source.seek(offset)
            data = source.read(size)
            if len(data) != size:
                raise ValueError('Truncated ISO read')
            return data

        def record_range(record):
            if len(record) < 34:
                raise ValueError('Truncated ISO directory record')
            offset = int.from_bytes(record[2:6], 'little') * SECTOR
            size = int.from_bytes(record[10:14], 'little')
            return offset, size

        def listing(record):
            offset, size = record_range(record)
            if size > 4 * 1024 * 1024:
                raise ValueError('Directory exceeds project read limit')
            data = read_at(offset, size)
            result = {}
            pos = 0
            while pos < size:
                length = data[pos]
                if length == 0:
                    pos = (pos // SECTOR + 1) * SECTOR
                    continue
                row = data[pos:pos + length]
                if len(row) != length or length < 34 or 33 + row[32] > length:
                    raise ValueError('Invalid ISO directory record')
                name = row[33:33 + row[32]].decode('ascii').split(';')[0]
                if name not in ('\x00', '\x01'):
                    # ISO9660 multi-extent files repeat their directory name.
                    result.setdefault(name, []).append(row)
                pos += length
            return result

        def single_record(entries, name):
            rows = entries[name]
            if len(rows) != 1:
                raise ValueError(f'Target requires a single ISO extent: {name}')
            return rows[0]

        pvd = read_at(16 * SECTOR, SECTOR)
        if pvd[:7] != b'\x01CD001\x01':
            raise ValueError('Expected ISO9660 primary volume descriptor')
        root = listing(pvd[156:156 + pvd[156]])
        game = listing(single_record(root, 'PS3_GAME'))
        usrdir = listing(single_record(game, 'USRDIR'))
        pending = {}
        for name, digest in EXPECTED.items():
            row = single_record(usrdir, name)
            if row[25] & 2:
                raise ValueError(f'{name} is a directory')
            blob = read_at(*record_range(row))
            if hashlib.sha256(blob).hexdigest() != digest:
                raise ValueError(f'{name} differs from the inspected revision')
            pending[name] = blob
        destination = ROOT / 'private'
        destination.mkdir(exist_ok=True)
        for name, blob in pending.items():
            output = destination / name
            if output.exists():
                if hashlib.sha256(output.read_bytes()).hexdigest() != EXPECTED[name]:
                    raise ValueError(f'Refusing to replace different file: {output}')
            else:
                with output.open('xb') as target:
                    target.write(blob)
            print(f'{name}: {len(blob)} bytes verified')
        inventory = [{'name': name, 'size': sum(record_range(row)[1] for row in rows),
                      'extent_count': len(rows), 'directory': bool(rows[0][25] & 2)}
                     for name, rows in usrdir.items()]
        (ROOT / 'reports/iso-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')


if __name__ == '__main__':
    main()
