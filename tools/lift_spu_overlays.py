"""Translate identified raw SPU overlays from the locked PPU ELF, without JIT."""
import hashlib
import json
import shutil
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


def expand_overlays(items):
    """Compile only explicitly admitted PIC positions, before execution."""
    for item in items:
        yield item
        original_base = int(item['ls_base'], 0)
        seen = {original_base}
        for value in item.get('additional_ls_bases', []):
            base = int(value, 0)
            if base in seen or base & 15 or not 0 <= base < 0x40000:
                raise ValueError('Duplicate, unaligned or invalid PIC base')
            seen.add(base)
            delta = base - original_base
            variant = dict(item)
            variant.pop('additional_ls_bases')
            variant.update(name=f'{item["name"]}_ls{base:x}', variant_of=item['name'])
            for key in ('ls_base', 'entry', 'code_start', 'code_end'):
                variant[key] = hex(int(item[key], 0) + delta)
            variant['extra_entries'] = [hex(int(entry, 0) + delta)
                                        for entry in item.get('extra_entries', [])]
            yield variant


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
        for item in expand_overlays(config['overlays']):
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
                raise RuntimeError(f'Incomplete native overlay {name}: unsupported={diagnostics["unsupported"]}, '
                                   f'missing_direct_targets={[hex(a) for a in sorted(missing)]}, '
                                   f'entry_present={entry in starts}')
            if any(not code_start <= s < e <= code_end for s, e in diagnostics['functions']):
                raise RuntimeError('Generated code outside verified bounds: ' + name)
            for filename in ('spu_recomp.h', 'spu_recomp.c'):
                debase_includes(str(folder / filename))
            image_id = 0x20000000 | int(item['sha256'][:7], 16)
            if 'variant_of' in item:
                identity = f'{item["sha256"]}:{base:x}'.encode('ascii')
                image_id = 0x30000000 | int(hashlib.sha256(identity).hexdigest()[:7], 16)
            if image_id in image_ids:
                raise RuntimeError('Ambiguous raw overlay image id: ' + name)
            image_ids.add(image_id)
            fingerprint = fnv1a64(blob)
            symbol = prefix + 'spu_recomp_register'
            declarations.append(f'extern void {symbol}(void);')
            observe = ''
            if 'io_layout' in item:
                codec = {'zlib': 0, 'refpack': 1}[item['io_layout']]
                native = prefix + f'spu_func_{entry:08X}'
                wrapper = prefix + 'observed_entry'
                declarations.append(f'extern void {native}(spu_context*);\n'
                                    f'static void {wrapper}(spu_context* ctx) {{ fifa_observe_spu_job(ctx, {native}, {codec}); }}')
                observe = f'spu_register_function(0x{entry:X}u, {wrapper}); '
            registration.append(f'    spu_begin_image({image_id}); {observe}{symbol}();\n'
                                f'    spu_overlay_register_region_checked(0x{ea:X}u, {size}u, 0x{base:X}u, {code_start-base}u, {code_end-code_start}u, {image_id}, 0x{fingerprint:016X}ULL);')
            sources.append(destination / name / 'spu_recomp.c')
            inventory['overlays'].append(dict(**item, image_id=image_id, fingerprint=f'{fingerprint:016X}',
                                               functions=len(starts), unsupported=diagnostics['unsupported'],
                                               missing_direct_targets=len(missing)))
        registry = ('#include "spu_workload.h"\nextern void spu_begin_image(int);\n'
                    'extern void spu_register_function(uint32_t,spu_lifted_entry_fn);\n'
                    'extern void fifa_observe_spu_job(spu_context*,spu_lifted_entry_fn,int);\n'
                    'extern void spu_overlay_register_region_checked(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,int,uint64_t);\n' +
                    '\n'.join(declarations) + '\nvoid fifa_spu_register_overlays(void) {\n' +
                    '\n'.join(registration) + '\n    spu_begin_image(0);\n}\n')
        (stage / 'overlays.c').write_text(registry)
        sources.append(destination / 'overlays.c')
        (stage / 'sources.cmake').write_text('set(FIFA_SPU_OVERLAY_SOURCES\n' +
            ''.join(f'  [==[{p.as_posix()}]==]\n' for p in sources) + ')\n')
        (stage / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
        # Preserve timestamps only after freshly regenerating and comparing the
        # complete bytes. One added overlay must not recompile unchanged jobs.
        if destination.exists():
            for path in stage.rglob('*'):
                previous = destination / path.relative_to(stage)
                if path.is_file() and previous.is_file() and path.read_bytes() == previous.read_bytes():
                    shutil.copystat(previous, path)
        publish(stage, destination)
    print(json.dumps(inventory, indent=2))


if __name__ == '__main__':
    main()
