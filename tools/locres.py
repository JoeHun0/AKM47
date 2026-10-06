"""Minimal UE .locres reader: prints key = value for keys matching a regex.

Handles every locres version seen in Stalker 2 mods:
  legacy (no magic, strings inline), v1 Compact, v2 Optimized_CRC32, v3 CityHash64 (vanilla).
"""
import struct, sys, re, json, os

MAGIC = bytes.fromhex('0e147475674a03fc4a15909dc3377f1b')

def fstr(b, o):
    (n,) = struct.unpack_from('<i', b, o); o += 4
    if n < 0:
        s = b[o:o - 2 * n - 2].decode('utf-16-le', 'replace'); o += -2 * n
    else:
        s = b[o:o + max(n - 1, 0)].decode('utf-8', 'replace'); o += max(n, 0)
    return s, o

def read_legacy(b):
    o = 0
    (nns,) = struct.unpack_from('<I', b, o); o += 4
    out = {}
    for _ in range(nns):
        ns, o = fstr(b, o)
        (nk,) = struct.unpack_from('<I', b, o); o += 4
        for _ in range(nk):
            key, o = fstr(b, o)
            o += 4  # source hash
            val, o = fstr(b, o)
            out[key] = val
    return out

def read(path):
    b = open(path, 'rb').read()
    if b[:16] != MAGIC:
        return read_legacy(b)
    o = 16
    ver = b[o]; o += 1
    (stroff,) = struct.unpack_from('<q', b, o); o += 8
    if ver >= 2:
        o += 4  # entries count
    # strings
    so = stroff
    (cnt,) = struct.unpack_from('<i', b, so); so += 4
    strings = []
    for _ in range(cnt):
        s, so = fstr(b, so)
        if ver >= 2:
            so += 4  # ref count
        strings.append(s)
    (nns,) = struct.unpack_from('<I', b, o); o += 4
    out = {}
    for _ in range(nns):
        if ver >= 2:
            o += 4
        ns, o = fstr(b, o)
        (nk,) = struct.unpack_from('<I', b, o); o += 4
        for _ in range(nk):
            if ver >= 2:
                o += 4
            key, o = fstr(b, o)
            o += 4  # source hash
            (idx,) = struct.unpack_from('<i', b, o); o += 4
            out[key] = strings[idx] if 0 <= idx < len(strings) else None
    return out

if __name__ == '__main__':
    d = read(sys.argv[1])
    pat = re.compile(sys.argv[2])
    for k, v in sorted(d.items()):
        if pat.search(k):
            print(f'{k} = {v}')
