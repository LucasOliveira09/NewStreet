"""Read-only UDF bridge view, including UDF 2.50 metadata partitions.

Structural parsers: pinned pycdlib 1.22.0 (LGPL-2.1-only).
Partition mapping follows ECMA-167 / UDF 2.50 section 2.2.10; reference:
https://github.com/firecore/libudfread/blob/master/src/udfread.c
The high-level pycdlib reader assumes FSD and metadata use physical partition 0,
which is not true for this disc. Unsupported allocation forms fail explicitly.
"""
import struct
from pycdlib import udf
from iso9660 import BLOCK, Entry, IsoImage


class UdfImage(IsoImage):
    def __init__(self, source):
        self.source = source
        source.seek(0, 2)
        self.size = source.tell()
        anchor = udf.parse_anchor(self.read(256 * BLOCK, BLOCK), 256)
        if anchor is None or anchor.main_vd.extent_length > 1024 * 1024:
            raise ValueError('Missing or unsupported UDF anchor')
        ad = anchor.main_vd
        desc = udf.parse_udf_vol_descs(self.read(ad.extent_location * BLOCK, ad.extent_length),
                                       ad.extent_location, BLOCK)
        if len(desc.logical_volumes) != 1:
            raise ValueError('Expected one UDF logical volume')
        volume = desc.logical_volumes[0]
        physical = {p.part_num: ((p.part_start_location * BLOCK, p.part_length * BLOCK),)
                    for p in desc.partitions}
        self.maps = {}
        for i, part in enumerate(volume.partition_maps):
            if isinstance(part, udf.UDFType1PartitionMap):
                self.maps[i] = physical[part.part_num]
        for i, part in enumerate(volume.partition_maps):
            if isinstance(part, udf.UDFType2PartitionMap):
                raw = part.record()
                if raw[5:28].rstrip(b'\0') != b'*UDF Metadata Partition':
                    raise ValueError('Unsupported UDF type 2 partition')
                number, location = struct.unpack_from('<HI', raw, 38)
                base, length = physical[number][0]
                if location * BLOCK + BLOCK > length:
                    raise ValueError('Metadata file outside physical partition')
                entry = self._entry_at(base + location * BLOCK, location, None,
                                       physical[number])
                self.maps[i] = entry.extents
        ad = volume.logical_volume_contents_use
        if not BLOCK <= ad.extent_length <= 2 * BLOCK:
            raise ValueError('Unsupported UDF file set size')
        data = self._read_map(ad.part_ref_num, ad.log_block_num * BLOCK, ad.extent_length)
        fsd, _ = udf.parse_file_set(data, ad.log_block_num, BLOCK)
        self.root = self._entry(fsd.root_dir_icb)

    @staticmethod
    def _slice(extents, offset, size):
        if offset < 0 or size < 0:
            raise ValueError('Negative UDF range')
        result = []
        for start, length in extents:
            if offset >= length:
                offset -= length
                continue
            count = min(size, length - offset)
            if count:
                result.append((start + offset, count))
                size -= count
            offset = 0
            if not size:
                break
        if size:
            raise ValueError('UDF extent outside partition')
        return tuple(result)

    def _read_map(self, partition, offset, size):
        return b''.join(self.read(a, n) for a, n in self._slice(self.maps[partition], offset, size))

    def _entry(self, ad):
        spans = self._slice(self.maps[ad.part_ref_num], ad.log_block_num * BLOCK, BLOCK)
        if len(spans) != 1:
            raise ValueError('Split UDF file entry unsupported')
        return self._entry_at(spans[0][0], ad.log_block_num, ad.part_ref_num)

    def _entry_at(self, address, block, partition, inherited=None):
        data = self.read(address, BLOCK)
        fe = udf.parse_file_entry(data, address // BLOCK, block, None)
        if fe is None or fe.icb_tag.file_type not in (4, 5, 250, 251):
            raise ValueError('Unsupported UDF file entry type')
        tag = int.from_bytes(data[:2], 'little')
        attr = 168 if tag == 261 else 208
        ea_size, ad_size = struct.unpack_from('<II', data, attr)
        start = attr + 8 + ea_size
        if start + ad_size > len(data):
            raise ValueError('UDF allocation descriptors outside file entry')
        allocation = fe.icb_tag.flags & 7
        if allocation == 3:
            extents = ((address + start, ad_size),)
        elif allocation in (0, 1):
            stride = 8 if allocation == 0 else 16
            if ad_size % stride:
                raise ValueError('Truncated UDF allocation descriptor')
            extents = []
            for pos in range(start, start + ad_size, stride):
                size, location = struct.unpack_from('<II', data, pos)
                if size >> 30:
                    raise ValueError('Sparse or continuation UDF allocation unsupported')
                ref = partition if allocation == 0 else struct.unpack_from('<H', data, pos + 8)[0]
                mapping = inherited if inherited is not None and allocation == 0 else self.maps[ref]
                extents.extend(self._slice(mapping, location * BLOCK, size))
        else:
            raise ValueError('Extended UDF allocation unsupported')
        extents = self._slice(extents, 0, fe.get_data_length())
        return Entry('', extents, fe.is_dir())

    def children(self, directory):
        if not directory.directory or directory.size > 4 * 1024 * 1024:
            raise ValueError('Unsupported UDF directory')
        data = b''.join(self.chunks(directory))
        entries, seen, pos = [], set(), 0
        while pos < len(data):
            if not any(data[pos:]):
                break
            # pycdlib validates the descriptor checksum and CRC. Tag location is
            # read from the descriptor: the directory can span mapped extents.
            location = struct.unpack_from('<I', data, pos + 12)[0]
            fid, consumed = udf.parse_file_ident(data[pos:], location, 0, None)
            if consumed <= 0 or pos + consumed > len(data):
                raise ValueError('Truncated UDF file identifier')
            pos += consumed
            if fid.is_parent() or fid.file_characteristics & 4:
                continue
            name = fid.fi.decode(fid.encoding)
            if not name or name in ('.', '..') or any(c in name for c in '/\\:\x00'):
                raise ValueError('Invalid UDF entry name')
            if name.casefold() in seen:
                raise ValueError('Duplicate UDF filename')
            seen.add(name.casefold())
            entry = self._entry(fid.icb)
            if entry.directory != fid.is_dir():
                raise ValueError('UDF directory type mismatch')
            entries.append(Entry(name, entry.extents, entry.directory))
        return entries

    def files(self, directory=None, prefix=''):
        pending = [(directory or self.root, prefix)]
        visited = set()
        while pending:
            node, path = pending.pop()
            if node.extents in visited or len(visited) >= 4096:
                raise ValueError('UDF directory cycle or directory limit exceeded')
            visited.add(node.extents)
            for entry in self.children(node):
                name = path + entry.name
                if entry.directory:
                    pending.append((entry, name + '/'))
                else:
                    yield name, entry
