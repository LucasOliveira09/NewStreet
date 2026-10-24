"""Translate identified raw SPU overlays from the locked PPU ELF, without JIT."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SDK_TOOLS = ROOT / 'vendor/ps3recomp/tools'
sys.path.insert(0, str(SDK_TOOLS))
from elf_parser import ELFFile, PT_LOAD
from find_spu_functions import detect_functions
from build_spu_workloads import debase_includes
from spu_program_pipeline import publish
from spu_elf import fnv1a64


def main():
    config_path = ROOT / 'spu_overlays.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    source = ROOT / 'private/FIFAZF.elf'
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['elf_sha256']:
        raise RuntimeError('Overlay configuration belongs to another ELF')
    elf = ELFFile(str(source)); elf.load()
    destination = (ROOT / 'private/generated/spu_overlays').resolve()
    if not destination.is_relative_to((ROOT / 'private').resolve()):
        raise RuntimeError('Overlay output escaped the private directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        old = json.loads((destination / 'inventory.json').read_text())
        if old.get('generator') != 'fifa_spu_overlays':
            raise RuntimeError('Refusing to replace an unowned overlay directory')
    inventory = dict(generator='fifa_spu_overlays', elf_sha256=config['elf_sha256'],
                     configuration_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(), overlays=[])
    with tempfile.TemporaryDirectory(prefix='fifa_overlays_', dir=destination.parent) as temporary:
        stage = Path(temporary) / 'output'; stage.mkdir()
        sources, declarations, registration, image_ids = [], [], [], set()
        for item in config['overlays']:
            name = item['name']
            if not re.fullmatch('[a-z][a-z0-9_]*', name):
                raise ValueError('Overlay name is not a safe C identifier')
            ea, size, base, entry, code_start, code_end = (
                int(item[key], 0) for key in ('source_ea', 'size', 'ls_base', 'entry', 'code_start', 'code_end'))
            if not 0 <= base <= code_start <= entry < code_end <= base + size <= 0x40000:
                raise ValueError('Invalid local-store/code bounds')
            blob = None
            for i, segment in enumerate(elf.program_headers):
                if segment.p_type == PT_LOAD and segment.p_vaddr <= ea and ea + size <= segment.p_vaddr + segment.p_filesz:
                    offset = ea - segment.p_vaddr
                    blob = elf.get_segment_data(i)[offset:offset + size]
                    break
            if blob is None or hashlib.sha256(blob).hexdigest() != item['sha256']:
                raise RuntimeError('Overlay source/hash mismatch: ' + name)
            folder = stage / name; folder.mkdir()
            (folder / 'image.bin').write_bytes(blob)
            bounds, _ = detect_functions(blob, base, verbose=False, raw=True)
            bounds = [(s, min(e, code_end)) for s, e in bounds if code_start <= s < code_end]
            (folder / 'functions.json').write_text(json.dumps([dict(start=s, end=e) for s, e in bounds]))
            prefix = 'fifa_' + name + '_'
            entries = sorted({entry} | {int(value, 0) for value in item.get('extra_entries', [])})
            if any(address & 3 or not code_start <= address < code_end for address in entries):
                raise ValueError('Extra overlay entry outside verified code bounds')
            command = [sys.executable, str(SDK_TOOLS / 'spu_lifter.py'), str(folder / 'image.bin'),
                       '--base', hex(base), '--functions', str(folder / 'functions.json'),
                       '--extra-funcs', ','.join(map(hex, entries)), '--code-end', hex(code_end), '--symbol-prefix', prefix,
                       '--output', str(folder), '--report', str(folder / 'lift.json')]
            result = subprocess.run(command, capture_output=True, text=True)
            (folder / 'lift.log').write_text(result.stdout + result.stderr, encoding='utf-8')
            if result.returncode:
                raise RuntimeError('Overlay lift failed: ' + name)
            diagnostics = json.loads((folder / 'lift.json').read_text())
            starts = {s for s, _ in diagnostics['functions']}
            missing = (set(diagnostics['call_targets']) | set(diagnostics['branch_targets'])) - starts
            if diagnostics['unsupported'] or missing or entry not in starts:
                raise RuntimeError('Incomplete native overlay: ' + name)
            if any(not code_start <= s < e <= code_end for s, e in diagnostics['functions']):
                raise RuntimeError('Generated code outside verified bounds: ' + name)
            for filename in ('spu_recomp.h', 'spu_recomp.c'):
                debase_includes(str(folder / filename))
            image_id = 0x20000000 | int(item['sha256'][:7], 16)
            if image_id in image_ids:
                raise RuntimeError('Ambiguous raw overlay image id: ' + name)
            image_ids.add(image_id)
            fingerprint = fnv1a64(blob)
            symbol = prefix + 'spu_recomp_register'
            declarations.append(f'extern void {symbol}(void);')
            registration.append(f'    spu_begin_image({image_id}); {symbol}();\n'
                                f'    spu_overlay_register_region_checked(0x{ea:X}u, {size}u, 0x{base:X}u, {code_start-base}u, {code_end-code_start}u, {image_id}, 0x{fingerprint:016X}ULL);')
            sources.append(destination / name / 'spu_recomp.c')
            inventory['overlays'].append(dict(**item, image_id=image_id, fingerprint=f'{fingerprint:016X}',
                                               functions=len(starts), unsupported=diagnostics['unsupported'],
                                               missing_direct_targets=len(missing)))
        registry = ('#include "spu_workload.h"\nextern void spu_begin_image(int);\n'
                    'extern void spu_overlay_register_region_checked(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,int,uint64_t);\n' +
                    '\n'.join(declarations) + '\nvoid fifa_spu_register_overlays(void) {\n' +
                    '\n'.join(registration) + '\n    spu_begin_image(0);\n}\n')
        (stage / 'overlays.c').write_text(registry)
        sources.append(destination / 'overlays.c')
        (stage / 'sources.cmake').write_text('set(FIFA_SPU_OVERLAY_SOURCES\n' +
            ''.join(f'  [==[{p.as_posix()}]==]\n' for p in sources) + ')\n')
        (stage / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
        publish(stage, destination)
    print(json.dumps(inventory, indent=2))


if __name__ == '__main__':
    main()
