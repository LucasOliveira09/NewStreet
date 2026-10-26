"""Identify candidate raw SPU programs in a private strict-failure snapshot.

This produces bounded evidence for review, not a new admission or a code edit.
Header size fields are reported separately: PIC entry offsets and code/data
layout differ between modules. Source addresses come from ELF PT_LOAD mapping.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/ps3recomp/tools'))
from elf_parser import ELFFile, PT_LOAD
from spu_disasm import disassemble_spu


def image_bounds(words, base, available):
    """Return the initialized span for the two locally reviewed header layouts.

    PIC headers declare a relative file size in word 5 (also used by the raw
    inventory). Fixed-address headers instead declare LS start/end in words
    7/8; word 5 is the BSS start, not an image size.
    """
    if words[7] & 0x80000000:
        size = words[5]
        entry = words[4]
        basis = 'pic_relative_size'
    elif words[7] == base:
        size = words[8] - words[7]
        entry = words[4] - base
        basis = 'fixed_ls_end_minus_start'
    else:
        return None
    if not 48 <= size <= min(available, 0x40000 - base) or size % 4:
        return None
    if not 48 <= entry < size or entry % 4:
        return None
    return size, basis


def boundary_label(data, size):
    # The trailer begins exactly at the declared initialized-image boundary.
    # A bounded, strictly ASCII, NUL-terminated string is required in full.
    if data[size:size + 12] != b'BuiltElfName':
        return None
    start = size + 32
    end = data.find(b'\0', start, min(start + 512, len(data)))
    if end <= start:
        return None
    name = data[start:end]
    if any(byte < 32 or byte > 126 for byte in name):
        return None
    return name.decode('ascii')


def identify(run):
    config = json.loads((ROOT / 'spu_overlays.json').read_text(encoding='utf-8'))
    source = ROOT / 'private/FIFAZF.elf'
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['elf_sha256']:
        raise ValueError('ELF differs from the inspected revision')
    elf = ELFFile(str(source)); elf.load()
    segments = [(segment.p_vaddr, elf.get_segment_data(i))
                for i, segment in enumerate(elf.program_headers) if segment.p_type == PT_LOAD]
    result = []
    for metadata in sorted((run / 'spu').glob('*.json')):
        state = json.loads(metadata.read_text(encoding='utf-8'))
        ls = metadata.with_suffix('.ls').read_bytes()
        if len(ls) != 0x40000 or not 0 <= state['pc'] < len(ls):
            raise ValueError('Invalid SPU snapshot bounds')
        # A DMA failure happens in the loader, before it jumps to the new code.
        # The loaded module can therefore be above the current PC.
        for base in range(0, len(ls) - 47, 16):
            header = ls[base:base + 48]
            if len(header) != 48 or header[44:] != b'\x55\x01\x10\x55':
                continue
            instructions = disassemble_spu(header[:16], base)
            if any(i.mnemonic != 'ila' or not i.operands.startswith('$r2,') for i in instructions):
                continue
            matches = []
            for ea, data in segments:
                pos = data.find(header)
                while pos >= 0:
                    # Include a bounded external name trailer even when the
                    # initialized image ends at the last byte of local store.
                    matches.append((ea + pos, data[pos:pos + len(ls) - base + 544]))
                    pos = data.find(header, pos + 1)
                    if len(matches) > 1:
                        break
            item = dict(snapshot=str(metadata.relative_to(ROOT)), pc=hex(state['pc']),
                        ls_base=hex(base), header_words=[hex(n) for n in struct.unpack('>12I', header)],
                        source_header_matches=len(matches), automatically_admitted=False)
            if len(matches) == 1:
                ea, data = matches[0]
                item['source_ea'] = hex(ea)
                bounds = image_bounds(struct.unpack('>12I', header), base, len(data))
                if bounds is not None:
                    size, basis = bounds
                    blob = data[:size]
                    decoded = disassemble_spu(blob, base)
                    differences = [i for i, (a, b) in enumerate(zip(blob, ls[base:])) if a != b]
                    item.update(image_size=hex(size), image_end=hex(base + size),
                                image_bounds_basis=basis,
                                source_sha256=hashlib.sha256(blob).hexdigest(),
                                snapshot_byte_differences=len(differences),
                                first_differences=[hex(base + i) for i in differences[:8]],
                                last_returns=[dict(pc=hex(i.addr), register=i.operands) for i in decoded
                                              if i.mnemonic == 'bi'][-6:],
                                first_unknown_words=[hex(i.addr) for i in decoded if i.mnemonic == '.word'][:6])
                    name = boundary_label(data, size)
                    if name is not None:
                        item.update(label_size_hint=hex(size), label=name)
                else:
                    item['image_bounds_error'] = 'Unsupported or truncated initialized-image bounds'
            result.append(item)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps(identify(args.run.resolve()), indent=2))
