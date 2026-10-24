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
        for base in range(0, state['pc'], 16):
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
                    matches.append((ea + pos, data[pos:pos + len(ls) - base]))
                    pos = data.find(header, pos + 1)
                    if len(matches) > 1:
                        break
            item = dict(snapshot=str(metadata.relative_to(ROOT)), pc=hex(state['pc']),
                        ls_base=hex(base), header_words=[hex(n) for n in struct.unpack('>12I', header)],
                        source_header_matches=len(matches), automatically_admitted=False)
            if len(matches) == 1:
                ea, data = matches[0]
                item['source_ea'] = hex(ea)
                label = data.find(b'BuiltElfName', 48)
                if label >= 0:
                    blob = data[:label]
                    decoded = disassemble_spu(blob, base)
                    differences = [i for i, (a, b) in enumerate(zip(blob, ls[base:])) if a != b]
                    name = data[label + 32:label + 112].split(b'\0')[0].decode('ascii', errors='replace')
                    item.update(label_size_hint=hex(label), label=name,
                                source_sha256=hashlib.sha256(blob).hexdigest(),
                                snapshot_byte_differences=len(differences),
                                first_differences=[hex(base + i) for i in differences[:8]],
                                last_returns=[dict(pc=hex(i.addr), register=i.operands) for i in decoded
                                              if i.mnemonic == 'bi'][-6:],
                                first_unknown_words=[hex(i.addr) for i in decoded if i.mnemonic == '.word'][:6])
            result.append(item)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps(identify(args.run.resolve()), indent=2))
