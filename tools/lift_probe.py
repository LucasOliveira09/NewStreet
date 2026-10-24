"""Lift two identified leaf functions from the local BLUS30882 v1.00 ELF.

Uses the ps3recomp loader/lifter at the revision in toolchain.lock.json.
See vendor/ps3recomp/docs/PPU_RECOMP.md. No game code is distributed here.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/ps3recomp/tools"))
from elf_parser import ELFFile
from ppu_loader import read_vaddr
from ppu_disasm import disassemble_bytes
from ppu_lifter import PPULifter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    elf = ELFFile(str(args.elf))
    elf.load()
    digest = hashlib.sha256(args.elf.read_bytes()).hexdigest()
    manifest = json.loads((ROOT / "probe_manifest.json").read_text())
    if digest != manifest["elf_sha256"]:
        parser.error("ELF does not match the inspected revision; re-identify the functions first.")
    functions = json.loads((ROOT / "private/analysis/fifazf/FIFAZF.functions.json").read_text())
    lifter = PPULifter()
    evidence = []
    for address in manifest["addresses"]:
        start = int(address, 16)
        function = next(f for f in functions if int(f["start"], 16) == start)
        end = int(function["end"], 16)
        code = read_vaddr(elf, start, end - start)
        if code is None or len(code) != end - start:
            raise ValueError(f"Cannot read complete function at {address}")
        instructions = disassemble_bytes(code, start, True)
        if not instructions or instructions[-1].mnemonic != "blr":
            raise ValueError(f"Function at {address} does not end in blr")
        lifter.lift_function(instructions, start, end)
        evidence.append({"address": address, "end": hex(end),
                         "source_sha256": hashlib.sha256(code).hexdigest()})
    output = ROOT / "private/generated/probe"
    output.mkdir(parents=True, exist_ok=True)
    (output / "ppu_recomp.h").write_text(lifter.emit_header())
    (output / "ppu_recomp.c").write_text(lifter.emit_source())
    (output / "provenance.json").write_text(json.dumps(
        {"elf_sha256": digest, "functions": evidence}, indent=2))
    print(f"Lifted {len(evidence)} functions into {output}")


if __name__ == "__main__":
    main()
