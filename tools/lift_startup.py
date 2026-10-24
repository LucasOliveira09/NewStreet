"""Lift a bounded reachable subset without decoding millions of words at once.

Uses original ELF bytes, the upstream PPU instruction lifter, observed runtime
targets and OPD boundaries. Missing targets remain explicit diagnostic functions.
This is incremental discovery, not proof of complete function-boundary recovery.
"""
import argparse
import bisect
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/ps3recomp/tools'))
from elf_parser import ELFFile, PT_LOAD
from ppu_disasm import disassemble_bytes
from ppu_lifter import PPULifter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', choices=['FIFAZF'], default='FIFAZF')
    parser.add_argument('--limit', type=int, default=512)
    parser.add_argument('--all-opd', action='store_true', help='Seed every canonical OPD entry; decode ranges in bounded memory')
    parser.add_argument('--add', type=lambda value: int(value, 0), action='append', default=[])
    args = parser.parse_args()
    if not 1 <= args.limit <= 100000:
        parser.error('limit must be positive and bounded')
    source = ROOT / 'private' / f'{args.module}.elf'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    expected = json.loads((ROOT / 'probe_manifest.json').read_text())['elf_sha256']
    if digest != expected:
        parser.error('ELF differs from the inspected revision')
    analysis = ROOT / 'private/analysis' / args.module.lower()
    required_path = analysis / 'required-startup.json'
    required = json.loads(required_path.read_text()) if required_path.exists() else []
    required = sorted(set(required + args.add))
    elf = ELFFile(str(source)); elf.load()
    executable = [(s.sh_addr, s.sh_addr + s.sh_size) for s in elf.section_headers
                  if s.sh_flags & 4 and s.sh_size]
    segments = [(p.p_vaddr, elf.get_segment_data(i)) for i, p in enumerate(elf.program_headers)
                if p.p_type == PT_LOAD and p.p_flags & 1]
    records = json.loads((analysis / f'{args.module}.functions.json').read_text())
    imports = json.loads((analysis / f'{args.module}.imports.json').read_text())
    loader = json.loads((analysis / f'{args.module}.loader.json').read_text())
    stubs = {int(item['stub'], 16): int(item['nid'], 16) for item in imports}
    starts = {int(item['start'], 16) for item in records} | set(stubs)
    ordered = sorted(starts)
    selected = set()
    queue = deque([int(loader['entry_code'], 16)] + required + (ordered if args.all_opd else []))
    limit = 100000 if args.all_opd else args.limit

    def add_start(address):
        if address not in starts:
            starts.add(address)
            bisect.insort(ordered, address)

    def code_end(start):
        return next((end for begin, end in executable if begin <= start < end), None)

    def decode(start):
        end = code_end(start)
        if end is None:
            return []
        following = bisect.bisect_right(ordered, start)
        if following < len(ordered):
            end = min(end, ordered[following])
        # Keep decoding bounded. A long range is split with an explicit continuation.
        end = min(end, start + 0x10000)
        for base, blob in segments:
            if base <= start < end <= base + len(blob):
                return disassemble_bytes(blob[start - base:end - base], start, True)
        return []

    while queue and len(selected) < limit:
        start = queue.popleft()
        if start in selected or start in stubs:
            continue
        if start & 3 or code_end(start) is None:
            continue
        add_start(start); selected.add(start)
        instructions = decode(start)
        if not instructions:
            continue
        if len(selected) % 2000 == 0:
            print(f'Discovered {len(selected)} function entries; queue={len(queue)}', flush=True)
        end = instructions[-1].addr + 4
        for ins in instructions:
            if ins.mnemonic in ('bl', 'bla') or (ins.mnemonic.startswith('b') and ins.mnemonic not in ('blr','blrl','bctr','bctrl')):
                targets = re.findall(r'0x[0-9A-Fa-f]+', ins.operands)
                if targets:
                    target = int(targets[-1], 16)
                    if ins.mnemonic in ('bl','bla') or not start <= target < end:
                        if code_end(target) is not None:
                            add_start(target); queue.append(target)
        previous = None
        for ins in instructions:
            frame = ins.mnemonic in ('stdu', 'stwu') and ins.operands.replace(' ', '').startswith('r1,-')
            if (frame or (ins.mnemonic == 'mflr' and ins.operands == 'r0')) and previous:
                if previous.mnemonic in ('blr', 'rfi', 'rfid'):
                    add_start(ins.addr); queue.append(ins.addr)
            if ins.mnemonic not in ('nop', 'lnop') and not ins.mnemonic.startswith('.'):
                previous = ins
        if instructions[-1].mnemonic not in ('blr', 'b', 'ba', 'bctr', 'rfid', 'rfi'):
            if code_end(end) is not None:
                add_start(end); queue.append(end)

    # New call targets can split earlier ranges; decode again with final bounds.
    lifter = PPULifter()
    lifter.hle_stub_nids = stubs
    lifter.function_entries = starts
    lifter.code_lo = min(begin for begin, _ in executable)
    lifter.code_hi = max(end for _, end in executable)
    lifter.toc_base = int(loader['module_toc'], 16)
    for start in sorted(selected | set(stubs)):
        instructions = decode(start)
        if instructions:
            lifter.lift_function(instructions, start, instructions[-1].addr + 4)
    output = ROOT / ('private/generated/fifazf_full' if args.all_opd else 'private/generated/fifazf_startup')
    output.mkdir(parents=True, exist_ok=True)
    header = lifter.emit_header()
    external = re.findall(r'void (func_([0-9A-F]+))\(ppu_context\* ctx\); /\* external \*/', header)
    fallback = ['#include "ppu_recomp.h"']
    for name, address in external:
        fallback.append(f'void {name}(ppu_context* ctx) {{ fifa_boot_missing("unlifted", 0x{address}ULL, ctx); }}')
    lifter.write_if_changed(str(output / 'ppu_recomp.h'), header)
    lifter.write_if_changed(str(output / 'ppu_recomp_missing.cpp'), '\n'.join(fallback) + '\n')
    written = lifter.write_source_files(str(output), base='ppu_recomp', max_lines=25000)
    keep = {Path(path).resolve() for path in written}
    for previous in output.glob('ppu_recomp_[0-9]*.cpp'):
        if previous.resolve() not in keep:
            previous.unlink()
    required_path.write_text(json.dumps(required, indent=2) + '\n')
    manifest = dict(elf_sha256=digest, selected=len(selected), import_stubs=len(stubs),
                    profile='all-opd' if args.all_opd else 'startup', selection_limit_reached=bool(queue),
                    pending_direct_targets=len(external), required=required,
                    functions=[hex(f.start_addr) for f in lifter.functions])
    (output / 'startup-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({key: value for key, value in manifest.items() if key != 'functions'}, indent=2))


if __name__ == '__main__':
    main()
