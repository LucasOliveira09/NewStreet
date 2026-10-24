"""Bounded, read-only ISO9660 reader with ordered multi-extent files.

Only the primary ISO9660 view is used. No UDF or Rock Ridge interpretation.
The on-disc extent and length fields contain matching LE/BE copies (ECMA-119).
"""
from dataclasses import dataclass

BLOCK = 2048


@dataclass(frozen=True)
class Entry:
    name: str
    extents: tuple[tuple[int, int], ...]
    directory: bool

    @property
    def size(self):
        return sum(size for _, size in self.extents)


class IsoImage:
    def __init__(self, source):
        self.source = source
        source.seek(0, 2)
        self.size = source.tell()
        pvd = self.read(16 * BLOCK, BLOCK)
        if pvd[:7] != b'\x01CD001\x01' or pvd[128:132] != b'\x00\x08\x08\x00':
            raise ValueError('Expected primary ISO9660 descriptor with 2048-byte blocks')
        row = pvd[156:156 + pvd[156]]
        self.root = Entry('', (self.extent(row),), True)

    def read(self, offset, size):
        if offset < 0 or size < 0 or offset + size > self.size:
            raise ValueError('Extent outside image')
        self.source.seek(offset)
        data = self.source.read(size)
        if len(data) != size:
            raise ValueError('Truncated ISO data')
        return data

    def extent(self, row):
        if len(row) < 34 or row[0] != len(row) or 33 + row[32] > len(row):
            raise ValueError('Invalid directory record')
        sector, length = int.from_bytes(row[2:6], 'little'), int.from_bytes(row[10:14], 'little')
        if sector != int.from_bytes(row[6:10], 'big') or length != int.from_bytes(row[14:18], 'big'):
            raise ValueError('Mismatched endian record copies')
        offset = sector * BLOCK
        if offset + length > self.size:
            raise ValueError('Extent outside image')
        return offset, length

    def children(self, directory):
        if not directory.directory or directory.size > 4 * 1024 * 1024:
            raise ValueError('Unsupported directory')
        data = b''.join(self.chunks(directory))
        entries, seen, pending = [], set(), None
        position = 0
        while position < len(data):
            length = data[position]
            if not length:
                position = (position // BLOCK + 1) * BLOCK
                continue
            if position % BLOCK + length > BLOCK:
                raise ValueError('Directory record crosses sector boundary')
            row = data[position:position + length]
            extent = self.extent(row)
            position += length
            raw_name = row[33:33 + row[32]]
            if raw_name in (b'\x00', b'\x01'):
                continue
            name = raw_name.decode('ascii').split(';')[0]
            if not name or name in ('.', '..') or any(c in name for c in '/\\:\x00'):
                raise ValueError('Invalid ISO entry name')
            is_dir, more = bool(row[25] & 2), bool(row[25] & 0x80)
            if pending:
                if pending.name != name or is_dir:
                    raise ValueError('Non-contiguous file extent chain')
                entry = Entry(name, pending.extents + (extent,), False)
            else:
                if name in seen:
                    raise ValueError('Duplicate without multi-extent continuation')
                seen.add(name)
                entry = Entry(name, (extent,), is_dir)
            if more:
                if is_dir:
                    raise ValueError('Multi-extent directory unsupported')
                pending = entry
            else:
                entries.append(entry)
                pending = None
        if pending:
            raise ValueError('Incomplete file extent chain')
        return entries

    def chunks(self, entry, chunk_size=1024 * 1024):
        if not 1 <= chunk_size <= 4 * 1024 * 1024:
            raise ValueError('Invalid transfer size')
        for offset, size in entry.extents:
            end = offset + size
            while offset < end:
                count = min(chunk_size, end - offset)
                yield self.read(offset, count)
                offset += count

    def files(self, directory=None, prefix=''):
        for entry in self.children(directory or self.root):
            path = prefix + entry.name
            if entry.directory:
                yield from self.files(entry, path + '/')
            else:
                yield path, entry
