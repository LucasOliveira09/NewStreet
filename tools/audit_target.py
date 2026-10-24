"""Audit source export-name coverage; matches never mean functional support."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/ps3recomp/tools'))
import gen_hle_nids as gen
from nid_database import get_default_db


def main():
    exports = {}
    for module in gen.discover_all():
        for source in (ROOT / 'vendor/ps3recomp/libs').rglob(module + '.c'):
            for nid, name in gen.scan(str(source)):
                exports[nid] = name
    imports = json.loads((ROOT / 'private/analysis/fifazf/FIFAZF.imports.json').read_text())
    db = get_default_db()
    groups = {}
    for item in imports:
        group = groups.setdefault(item['library'], dict(total=0, matched_name=0, unmatched=[]))
        group['total'] += 1
        nid = int(item['nid'], 16)
        if nid in exports:
            group['matched_name'] += 1
        else:
            resolved = db.lookup_nid(nid)
            group['unmatched'].append({'nid': item['nid'], 'name': resolved[1] if resolved else None})
    report = {
        'method': 'Compare imported NIDs against export-name NIDs computed by the upstream scanner. '
                  'A match does not prove implementation, linkage, correctness or game compatibility; '
                  'unmatched entries may require aliases or other registration paths.',
        'elf_sha256': hashlib.sha256((ROOT / 'private/FIFAZF.elf').read_bytes()).hexdigest(),
        'ps3recomp_revision': json.loads((ROOT / 'toolchain.lock.json').read_text())['ps3recomp']['commit'],
        'total_imports': len(imports),
        'matched_name_nids': sum(g['matched_name'] for g in groups.values()),
        'libraries': groups,
    }
    (ROOT / 'reports/import-coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Import names: {report['matched_name_nids']}/{report['total_imports']} matched")


if __name__ == '__main__':
    main()
