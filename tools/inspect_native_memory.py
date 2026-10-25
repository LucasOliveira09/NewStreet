"""Read bounded guest ranges in this project's running native full-game process.

Read-only process rights; no debugger attachment, guest writes or execution.
The symbol address comes from the current local PDB and PE section table.
Snapshots are best effort: guest threads continue running during the reads.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'private/build/fifazf_full/fifa_boot.exe'
PDBUTIL = ROOT / 'private/toolchain/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin/llvm-pdbutil.exe'


def parse_range(value):
    try:
        address, size = (int(part, 0) for part in value.split(':'))
        if address < 0x10000 or not 1 <= size <= 4096 or address + size > 0x100000000:
            raise ValueError()
        return address, size
    except ValueError:
        raise argparse.ArgumentTypeError('Use guest_address:size (1..4096 bytes), within guest userspace')


def symbol_rva(pe, symbol_output):
    # llvm-pdbutil dump prints symbol segment/offset in DECIMAL (section header
    # fields are hex). Confirmed against its raw S_GDATA32 record bytes.
    matches = re.findall(r'addr = (\d+):(\d+)', symbol_output)
    if len(matches) != 1 or pe[:2] != b'MZ':
        raise ValueError('Expected one vm_base data symbol and a PE image')
    segment, offset = map(int, matches[0])
    nt = struct.unpack_from('<I', pe, 0x3c)[0]
    if pe[nt:nt + 4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    machine, count = struct.unpack_from('<HH', pe, nt + 4)
    optional_size = struct.unpack_from('<H', pe, nt + 20)[0]
    if machine != 0x8664 or not 1 <= segment <= count:
        raise ValueError('Expected an x64 PE symbol section')
    section = nt + 24 + optional_size + (segment - 1) * 40
    size, rva = struct.unpack_from('<II', pe, section + 8)
    if offset + 8 > size:
        raise ValueError('vm_base symbol exceeds its PE section')
    return rva + offset


class NativeReader:
    def __init__(self, pid):
        if os.name != 'nt' or c.sizeof(c.c_void_p) != 8:
            raise OSError('This diagnostic requires Windows x64 Python')
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
        self.kernel.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
        self.handle = self.kernel.OpenProcess(0x410, False, pid)  # QUERY_INFORMATION | VM_READ only
        if not self.handle:
            raise c.WinError(c.get_last_error())
        try:
            name = c.create_unicode_buffer(32768); length = w.DWORD(len(name))
            if not self.kernel.QueryFullProcessImageNameW(self.handle, 0, name, c.byref(length)):
                raise c.WinError(c.get_last_error())
            if Path(name.value).resolve() != EXE.resolve():
                raise ValueError('PID is not this project\'s native full-game executable')
            nt = c.WinDLL('ntdll')
            nt.NtQueryInformationProcess.argtypes = [w.HANDLE, w.ULONG, c.c_void_p, w.ULONG, c.c_void_p]
            info = (c.c_uint64 * 6)()
            status = nt.NtQueryInformationProcess(self.handle, 0, info, c.sizeof(info), None)
            if status:
                raise OSError(f'ProcessBasicInformation failed: {status:#x}')
            # Windows x64 PEB ImageBaseAddress, read through the returned PEB.
            self.image_base = int.from_bytes(self.read(info[1] + 0x10, 8), 'little')
            symbols = subprocess.check_output([str(PDBUTIL), 'dump', '-globals', '-global-name=vm_base',
                                              str(EXE.with_suffix('.pdb'))], text=True)
            with EXE.open('rb') as image:
                rva = symbol_rva(image.read(65536), symbols)
            self.vm_base = int.from_bytes(self.read(self.image_base + rva, 8), 'little')
            if not self.vm_base:
                raise ValueError('Guest VM is not initialized')
        except BaseException:
            self.close()
            raise

    def read(self, address, size):
        buffer = c.create_string_buffer(size); count = c.c_size_t()
        if not self.kernel.ReadProcessMemory(self.handle, address, buffer, size, c.byref(count)):
            raise c.WinError(c.get_last_error())
        if count.value != size:
            raise OSError('Short process memory read')
        return buffer.raw

    def guest(self, address, size):
        # Reuse the same strict bounds even when called by a local analysis script.
        address, size = parse_range(f'{address}:{size}')
        return self.read(self.vm_base + address, size)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle); self.handle = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--range', required=True, action='append', type=parse_range)
    args = parser.parse_args()
    if args.pid <= 0 or len(args.range) > 16:
        parser.error('Use one positive PID and at most sixteen bounded ranges')
    reader = NativeReader(args.pid)
    try:
        result = dict(pid=args.pid, executable=str(EXE.relative_to(ROOT)), best_effort=True, ranges=[])
        for address, size in args.range:
            data = reader.guest(address, size)
            result['ranges'].append(dict(address=hex(address), bytes=size, hex=data.hex(),
                be32=[hex(struct.unpack_from('>I', data, i)[0]) for i in range(0, len(data) - 3, 4)]))
        print(json.dumps(result, indent=2))
    finally:
        reader.close()


if __name__ == '__main__':
    main()
