"""Decode Stalker 2 .cfg.bin into text cfg (best effort)."""
import struct, sys
sys.setrecursionlimit(100000)
p, outp = sys.argv[1], sys.argv[2]
b = open(p, 'rb').read()
ver, nstr, unk = struct.unpack_from('<III', b, 0)
off = 12
strs = []
for i in range(nstr):
    (n,) = struct.unpack_from('<i', b, off); off += 4
    if n < 0:
        strs.append(b[off:off-2*n-2].decode('utf-16-le', 'replace')); off += -2 * n
    else:
        strs.append(b[off:off+n-1].decode('utf-8', 'replace')); off += n

def S(i):
    return '' if i == 0 else strs[i-1]

o = off + 9
(rootcnt,) = struct.unpack_from('<I', b, o); o += 4
out = []
stats = {'xs': {}, 'fs': {}}

def node(depth):
    global o
    k, k2, v, x = struct.unpack_from('<IIII', b, o); o += 16
    f = b[o]; o += 1
    refs = []
    if f & 1:
        for _ in range(2):
            (n,) = struct.unpack_from('<i', b, o); o += 4
            refs.append(b[o:o+max(n-1, 0)].decode('utf-8', 'replace')); o += max(n, 0)
    (cnt,) = struct.unpack_from('<I', b, o); o += 4
    stats['xs'][x] = stats['xs'].get(x, 0) + 1
    stats['fs'][f] = stats['fs'].get(f, 0) + 1
    ind = '   ' * depth
    extra = ''
    if k2 != k:
        extra += f' {{k2={S(k2)}}}'
    if x:
        extra += f' {{x={x}:{S(x)}}}'
    if refs:
        extra += f' {{refkey={refs[0]}' + (f'; refurl={refs[1]}' if refs[1] else '') + '}'
    if f & ~1:
        extra += f' {{f={f}}}'
    if cnt or (v == 0 and f):
        out.append(f"{ind}{S(k)} : struct.begin{extra}" + (f" // val={S(v)}" if v else ''))
        for _ in range(cnt):
            node(depth + 1)
        out.append(f"{ind}struct.end")
    else:
        out.append(f"{ind}{S(k)} = {S(v)}{extra}")

try:
    for _ in range(rootcnt):
        node(0)
except Exception as e:
    print('FAILED at', hex(o), e)
    print('\n'.join(out[-40:]))
    for i in range(o - 120, o + 80, 21):
        print(hex(i), b[i:i+21].hex(' '))
open(outp, 'w', encoding='utf-8').write('\n'.join(out))
print('consumed to', hex(o), 'of', hex(len(b)), 'lines', len(out))
print('x values (top):', sorted(stats['xs'].items(), key=lambda t: -t[1])[:10])
print('f values:', stats['fs'])
