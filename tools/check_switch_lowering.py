"""Compile a synthetic PPC switch to x64 and verify its cases/shared epilogue.

Run from tools/build.ps1 so the Windows SDK/CRT and clang-cl are configured.
The fixture is original test assembly, independent of the private game bytes.
"""
import struct
import subprocess
from pathlib import Path
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC64, KS_MODE_BIG_ENDIAN

from lift_startup import startup_jump_tables
from ppu_disasm import disassemble_bytes
from ppu_lifter import PPULifter

ROOT = Path(__file__).resolve().parents[1]


def assemble_fixture():
    # The Windows LLVM distribution has no PPC assembler target. Keystone
    # assembles each instruction; this small fixture layout resolves its labels
    # and .long differences before passing instructions to that assembler.
    address, symbols, records, end = 0, {}, [], None
    for line in (ROOT / 'tests/switch_fixture.s').read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith(':'):
            symbols[line[:-1]] = address
        elif line.startswith('.org '):
            address = int(line.split()[1], 0)
        elif line.startswith('.size synthetic_switch,'):
            end = address
        elif line.startswith('.long ') or not line.startswith('.'):
            records.append((address, line)); address += 4
    data = bytearray(address)
    assembler = Ks(KS_ARCH_PPC, KS_MODE_PPC64 | KS_MODE_BIG_ENDIAN)
    for address, line in records:
        if line.startswith('.long '):
            left, right = line[6:].split('-')
            code = struct.pack('>I', (symbols[left] - symbols[right]) & 0xFFFFFFFF)
        else:
            for name in sorted(symbols, key=len, reverse=True):
                if line.endswith(' ' + name):
                    line = line[:-len(name)] + hex(symbols[name])
                    break
            code, _ = assembler.asm(line, addr=address, as_bytes=True)
            if len(code) != 4:
                raise RuntimeError('Fixture instruction did not encode to one PPC word')
        data[address:address + 4] = code
    return bytes(data), symbols['synthetic_switch'], end


def main():
    output = ROOT / 'private/build/switch-check'
    output.mkdir(parents=True, exist_ok=True)
    data, start, end = assemble_fixture()
    instructions = disassemble_bytes(data[start:end], start, True)
    lifter = PPULifter()
    lifter.jump_tables = startup_jump_tables(instructions, [(0, data)], 0x18000, start, end)
    if not lifter.jump_tables:
        raise RuntimeError('Synthetic computed jump was not recovered')
    lifter.lift_function(instructions, start, end)
    (output / 'ppu_recomp.h').write_text(lifter.emit_header())
    (output / 'switch.cpp').write_text(lifter.emit_source())
    (output / 'fixture.bin').write_bytes(data)
    subprocess.run(['clang-cl', '/nologo', '/EHsc', '/std:c++20', '/Od', '/w', '/DFIFA_STRICT_BOOT',
                    '/clang:-fwrapv', '/clang:-fno-strict-aliasing',
                    '/I' + str(output), '/I' + str(ROOT / 'vendor/ps3recomp/runtime/ppu'),
                    '/I' + str(ROOT / 'vendor/ps3recomp/include'),
                    str(output / 'switch.cpp'), str(ROOT / 'tests/switch_runner.cpp'),
                    '/Fe:' + str(output / 'switch_check.exe')], cwd=output, check=True)
    subprocess.run([str(output / 'switch_check.exe'), str(output / 'fixture.bin')], check=True)


if __name__ == '__main__':
    main()
