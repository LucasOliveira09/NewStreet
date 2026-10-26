"""Inventory locked raw SPU images and review a bounded common ANT CRT family.

Produces metadata, never changes the admitted manifest or emits game bytes.
The CRT reference is the already reviewed, hash-locked original VBR image.
Matching initialization does not validate a plugin's animation algorithms.
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


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def inspect_common_ant(blob, reference):
    require(len(blob) >= 0xd8 and len(reference) >= 0xd8, 'Truncated CRT')
    header = struct.unpack_from('>12I', blob)
    require(header[4:8] == (0x30, len(blob), 0x50, 0x80000000) and
            header[10:] == (1, 0x55011055), 'Unsupported raw PIC header')
    variable = {0x54, 0x58, 0x7c, 0x80, 0xbc}
    for offset in range(0x30, 0xd8, 4):
        require(offset in variable or blob[offset:offset + 4] == reference[offset:offset + 4],
                f'CRT differs at 0x{offset:x}')
    instructions = {ins.addr: ins for ins in disassemble_spu(blob[:0xd8], 0)}

    def ila(offset, register):
        ins = instructions[offset]
        require(ins.mnemonic == 'ila' and ins.operands.startswith(f'$r{register}, '),
                f'Unexpected address construction at 0x{offset:x}')
        return int(ins.operands.split(', ')[1], 0)

    require(ila(0x54, 8) == len(blob) and ila(0x58, 9) == len(blob) + 0x50,
            'Unexpected BSS range')
    table = ila(0x7c, 80)
    require(table % 4 == 0 and 0xd8 <= table <= len(blob) - 16 and
            ila(0x80, 81) == table + 12, 'Constructor table bounds')
    entries = list(struct.unpack_from('>3I', blob, table))
    require(all(entry % 4 == 0 for entry in entries) and
            0xd8 <= entries[0] < entries[1] < entries[2] < table,
            'Constructor entries/order')
    require(struct.unpack_from('>I', blob, table + 12)[0] == 0, 'Constructor terminator')
    end = entries[-1] + 16
    require(table - end in (0, 8) and not any(blob[end:table]), 'Code/data padding')
    tail = disassemble_spu(blob[entries[-1]:end], entries[-1])
    require([ins.mnemonic for ins in tail] == ['il', 'ila', 'br', 'lnop'] and
            tail[0].operands == '$r3, 1' and tail[1].operands == '$r4, 0xFFFF',
            'Final constructor tail differs')
    require(0xd8 <= int(tail[2].operands, 0) < end, 'Tail branch outside code')
    call = instructions[0xbc]
    require(call.mnemonic == 'brsl' and call.operands.startswith('$r0, ') and
            0xd8 <= int(call.operands.split(', ')[1], 0) < end,
            'Main call outside code')
    return dict(code_end=end, constructors=entries, table=table,
                bss_start=len(blob), bss_end=len(blob) + 0x50)


def scan_segment(data, guest_base):
    records = []
    position = data.find(b'\x55\x01\x10\x55')
    while position >= 0:
        start = position - 44
        position = data.find(b'\x55\x01\x10\x55', position + 4)
        if start < 0 or (guest_base + start) % 16:
            continue
        header = data[start:start + 48]
        if len(header) != 48:
            continue
        words = struct.unpack('>12I', header)
        size = words[5]
        label = start + size
        if not 48 <= size <= 0x40000 or label + 32 >= len(data):
            continue
        if data[label:label + 12] != b'BuiltElfName':
            continue
        prefix = disassemble_spu(header[:16], 0)
        if not all(ins.mnemonic == 'ila' and ins.operands.startswith('$r2,') for ins in prefix):
            continue
        name_end = data.find(b'\0', label + 32, min(label + 32 + 512, len(data)))
        if name_end < 0:
            continue
        name = data[label + 32:name_end].decode('ascii', 'replace')
        records.append(dict(source_ea=hex(guest_base + start), bytes=size,
            name=name.replace('/', '\\').rsplit('\\', 1)[-1],
            sha256=hashlib.sha256(data[start:label]).hexdigest(),
            entry=hex(words[4]), bss_bytes=words[6], flags=hex(words[7]),
            ant_common_path='\\antcommonplugins\\' in name.replace('/', '\\').lower()))
    return records


def review_images(records, read, reference):
    # Directory labels are evidence about provenance, not executable admission.
    # Every image must independently satisfy the same checked CRT structure.
    for item in records:
        item.pop('common_crt_review', None)
        item.pop('common_crt_rejection', None)
        try:
            item['common_crt_review'] = inspect_common_ant(
                read(int(item['source_ea'], 0), item['bytes']), reference)
        except ValueError as error:
            item['common_crt_rejection'] = str(error)


def inventory():
    config = json.loads((ROOT / 'spu_overlays.json').read_text(encoding='utf-8'))
    source = ROOT / 'private/FIFAZF.elf'
    require(hashlib.sha256(source.read_bytes()).hexdigest() == config['elf_sha256'],
            'Source ELF differs from locked manifest')
    elf = ELFFile(str(source)); elf.load()
    segments = [(segment.p_vaddr, elf.get_segment_data(i))
                for i, segment in enumerate(elf.program_headers) if segment.p_type == PT_LOAD]

    def read(ea, size):
        for base, data in segments:
            if base <= ea and ea + size <= base + len(data):
                return data[ea - base:ea - base + size]
        raise ValueError('Image outside file-backed PT_LOAD')

    anchor = next(item for item in config['overlays'] if item['name'] == 'ant_vbrcodec_clipnode')
    reference = read(int(anchor['source_ea'], 0), int(anchor['size'], 0))
    require(hashlib.sha256(reference).hexdigest() == anchor['sha256'], 'CRT reference differs')
    records = [item for base, data in segments for item in scan_segment(data, base)]
    require(len({item['source_ea'] for item in records}) == len(records), 'Duplicate raw image address')
    review_images(records, read, reference)
    return dict(generator='fifa_spu_raw_inventory', elf_sha256=config['elf_sha256'],
                crt_reference_sha256=anchor['sha256'], images=records,
                raw_image_count=len(records),
                common_ant_count=sum('common_crt_review' in item for item in records),
                automatic_admission=False, algorithm_validation=False,
                inventory_exhaustive=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'reports/spu-raw-inventory.json')
    args = parser.parse_args()
    target = args.out.resolve()
    require(target.suffix == '.json' and any(target.is_relative_to(directory.resolve())
        for directory in [ROOT / 'reports', ROOT / 'private/analysis']), 'Unsafe report path')
    report = inventory()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('raw_image_count', 'common_ant_count',
                                                  'automatic_admission', 'algorithm_validation')}))
