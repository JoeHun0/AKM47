"""Which installed mods touch the entries our mod changes?

Usage: py conflict_scan.py <our.cfg>[,<our2.cfg>...] <extracted-mods-dir>
  <extracted-mods-dir> holds one sub-folder per mod (extract each mod's relevant cfgs there).
  Optional <extracted-mods-dir>/map.tsv lines "folder<TAB>display name<TAB>count" give nicer names.
Reports per mod: REPLACES (full definition), PATCHES ({bpatch}), INHERITS (refkey to ours),
USES (references our entry as a sub-list / quest item generator).
"""
import os, re, sys
OURS = sys.argv[1].split(',')
ROOT = sys.argv[2]
names = {}
map_file = os.path.join(ROOT, 'map.tsv')
if os.path.exists(map_file):
    for line in open(map_file, encoding='utf-8-sig'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) >= 2:
            names[parts[0]] = parts[1].split('\\')[0]
ours = set()
for p in OURS:
    ours |= set(re.findall(r'^(\S+) : struct\.begin', open(p, encoding='utf-8').read(), re.M))
pat_top = re.compile(r'^(\S+) : struct\.begin(.*)$')
report = {}
for d in sorted(os.listdir(ROOT)):
    full = os.path.join(ROOT, d)
    if not os.path.isdir(full):
        continue
    for dp, _, files in os.walk(full):
        for fn in files:
            p = os.path.join(dp, fn)
            rel = p[len(full) + 1:].replace('Stalker2\\Content\\GameLite\\', '')
            text = open(p, encoding='utf-8-sig', errors='replace').read()
            for ln, line in enumerate(text.splitlines(), 1):
                m = pat_top.match(line)
                if m:
                    sid, extra = m.group(1), m.group(2)
                    rk = re.search(r'refkey=([^;}\s]+)', extra)
                    if sid in ours:
                        kind = 'PATCHES' if 'bpatch' in extra else 'REPLACES'
                        report.setdefault(d, []).append(f'{kind:<9} {sid}   [{rel}:{ln}]')
                    elif rk and rk.group(1) in ours:
                        report.setdefault(d, []).append(f'INHERITS  {sid} from {rk.group(1)}   [{rel}:{ln}]')
                for ref in re.findall(r'(?:ItemGeneratorPrototypeSID|ItemGeneratorSID)\s*=\s*(\S+)', line):
                    if ref in ours:
                        report.setdefault(d, []).append(f'USES      {ref}   [{rel}:{ln}]')
for d, rows in report.items():
    print(f'== {names.get(d, d)}  ({len(rows)} hits)')
    for r in sorted(set(rows))[:40]:
        print('   ', r)
if not report:
    print('no mod touches any entry our mod replaces')
print('ours checked:', len(ours))
