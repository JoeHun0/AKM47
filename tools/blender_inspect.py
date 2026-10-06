"""Blender (background) helper: import an FBX and report what's in it.
Usage: blender.exe -b -P tools\\blender_inspect.py -- <file.fbx> [<file2.fbx> ...]
Prints objects with type, parent, world bounding box (in meters), and armature bones."""
import sys
import bpy
from mathutils import Vector

files = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in files:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    print(f'\n===== {f}: {len(new)} objects')
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    rows = []
    for o in new:
        if o.type == 'MESH':
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            mn = Vector((min(p[i] for p in pts) for i in range(3)))
            mx = Vector((max(p[i] for p in pts) for i in range(3)))
            lo = Vector((min(lo[i], mn[i]) for i in range(3)))
            hi = Vector((max(hi[i], mx[i]) for i in range(3)))
            rows.append((o.name, len(o.data.polygons), mn, mx, o.parent.name if o.parent else '-'))
        elif o.type == 'ARMATURE':
            print(f'ARMATURE {o.name}: {len(o.data.bones)} bones')
            for b in o.data.bones:
                h = o.matrix_world @ b.head_local
                print(f'   bone {b.name:40} parent={b.parent.name if b.parent else "-":30} head=({h.x:.4f},{h.y:.4f},{h.z:.4f})')
        else:
            print(f'{o.type} {o.name}')
    print(f'TOTAL bbox min={tuple(round(v, 4) for v in lo)} max={tuple(round(v, 4) for v in hi)} '
          f'size={tuple(round(hi[i] - lo[i], 4) for i in range(3))}')
    for name, polys, mn, mx, par in sorted(rows, key=lambda r: r[2][1]):
        c = (mn + mx) / 2
        print(f'  {name:36} polys={polys:6} center=({c.x:.4f},{c.y:.4f},{c.z:.4f}) '
              f'size=({mx.x - mn.x:.4f},{mx.y - mn.y:.4f},{mx.z - mn.z:.4f}) parent={par}')
