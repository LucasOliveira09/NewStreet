"""Generate original SPU test programs for the native PIC lowering contract."""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/ps3recomp/tools'))
from spu_disasm import disassemble_spu
from spu_lifter import SPULifter, compute_bi_r0_jumps, compute_link_returns
from build_spu_workloads import debase_includes


def ri16(op, value, rt):
    return (op << 23) | ((value & 0xffff) << 7) | rt


def ri10(op, value, ra, rt):
    return (op << 24) | ((value & 0x3ff) << 14) | (ra << 7) | rt


def rr(op, ra, rt):
    return (op << 21) | (ra << 7) | rt


def store(path, text):
    data = text.encode('utf-8')
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def main():
    output = ROOT / 'private/generated/spu_pic_fixture'
    output.mkdir(parents=True, exist_ok=True)
    programs = [
        ('main', 0x100, 0x200, [(0x130, 0x144), (0x144, 0x154),
         (0x154, 0x158), (0x158, 0x160), (0x160, 0x168),
         (0x168, 0x174), (0x174, 0x17c), (0x180, 0x188),
         (0x190, 0x198), (0x1a0, 0x1a8)], {
            0x130: ri16(0x66, 1, 10),             # brsl r10, .+4
            0x134: ri16(0x67, (0x1d0-0x134)//4, 4), # lqr r4, relative data
            0x138: ri16(0x47, (0x1e0-0x138)//4, 4), # stqr r4, relative output
            0x13c: ri16(0x61, 0x3000//4, 5),      # lqa r5, absolute data
            0x140: ri16(0x41, 0x3010//4, 5),      # stqa r5, absolute output
            0x144: ri16(0x81, 1, 6),              # il r6, 1
            0x148: ri16(0x40, (0x154-0x148)//4, 6), # brz: not taken
            0x14c: ri16(0x42, (0x154-0x14c)//4, 6), # brnz: taken
            0x150: ri16(0x81, -1, 7),             # must be skipped
            0x154: ri16(0x66, (0x180-0x154)//4, 75), # brsl non-r0 link
            0x158: ri10(0x04, 0, 75, 11),         # preserve physical link
            0x15c: ri16(0x66, 1, 74),             # another PC getter
            0x160: rr(0x1a9, 30, 76),            # bisl r76, internal callback
            0x164: ri10(0x04, 0, 76, 12),
            0x168: rr(0x1a9, 31, 73),            # bisl r73, OTHER PIC program
            0x16c: ri10(0x04, 0, 73, 13),
            0x170: rr(0x1ab, 29, 72),            # bisled: both event paths
            0x174: ri16(0x81, 42, 3),
            0x178: rr(0x1a8, 0, 0),              # bi r0: real outer return
            0x180: ri10(0x1c, 41, 6, 7),          # ai r7, r6, 41
            0x184: rr(0x1a8, 75, 0),
            0x190: ri16(0x81, 99, 9),
            0x194: ri16(0x64, (0x174-0x194)//4, 0), # br to final return
            0x1a0: ri10(0x1c, 1, 7, 8),
            0x1a4: rr(0x1a8, 76, 0),
        }),
        ('other', 0x600, 0x100, [(0x630, 0x640)], {
            0x630: ri16(0x66, 1, 20),
            0x634: ri16(0x67, (0x6c0-0x634)//4, 21),
            0x638: ri10(0x04, 0, 21, 14),
            0x63c: rr(0x1a8, 73, 0),              # caller's cross-image link
        }),
    ]
    arrays = ['#pragma once', '#include <cstdint>']
    for name, base, size, bounds, words in programs:
        blob = bytearray(size)
        struct.pack_into('>I', blob, 28, 0x80000000)
        for address, word in words.items():
            struct.pack_into('>I', blob, address-base, word)
        insns = disassemble_spu(bytes(blob), base)
        lifter = SPULifter(prefix=f'fifa_pic_fixture_{name}_', relocatable_pic=True)
        lifter.func_starts = {s for s, _ in bounds}
        lifter.bi_r0_jump = compute_bi_r0_jumps(insns, bounds)
        lifter.link_return = compute_link_returns(insns, bounds)
        for start, end in bounds:
            lifter.lift_function(insns, start, end)
        missing = (lifter.call_targets | lifter.branch_targets) - lifter.func_starts
        if lifter.unsupported or missing:
            raise RuntimeError(f'{name}: unsupported={lifter.unsupported}, missing={missing}')
        folder = output / name
        folder.mkdir(exist_ok=True)
        for filename, text in [('spu_recomp.h', lifter.emit_header()),
                               ('spu_recomp.c', lifter.emit_source('spu_recomp.h'))]:
            # Apply the same include normalization as the real AOT pipeline.
            temporary = folder / ('normalized-' + filename)
            temporary.write_text(text, encoding='utf-8')
            debase_includes(str(temporary))
            store(folder / filename, temporary.read_text(encoding='utf-8'))
            temporary.unlink()
        arrays.append(f'static const uint8_t fixture_{name}[] = {{' +
                      ','.join(str(b) for b in blob) + '};')
    store(output / 'images.h', '\n'.join(arrays) + '\n')


if __name__ == '__main__':
    main()
