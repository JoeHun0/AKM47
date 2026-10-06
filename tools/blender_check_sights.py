"""Blender (background): centre-line top profile of the rear sight and front post, AKM-74S vs our body export.
Usage: blender.exe -b -P tools\blender_check_sights.py"""
import os, bpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
bpy.ops.wm.read_factory_settings(use_empty=True)
def verts(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=path)
    return [o.matrix_world @ v.co for o in bpy.data.objects if o not in before and o.type == 'MESH'
            and not o.name.startswith('UCX') for v in o.data.vertices]
for name, path in (('AKM-74S', os.path.join(ROOT, 'model_src', 'ref', 'SM_wpn_ak74_SM_offset.fbx')),
                   ('AK-47', os.path.join(ROOT, 'model_export', 'SM_AKM47_Body.fbx'))):
    pts = verts(path)
    for label, xa, xb in (('rear', 0.16, 0.27), ('front', 0.53, 0.59)):
        print(f'{name} {label}:', '  '.join(
            f'{x/1000:.1f}:{max(p.z for p in sel)*100:.2f}' for x in range(int(xa*1000), int(xb*1000), 5)
            if (sel := [p for p in pts if x/1000 <= p.x < x/1000 + 0.005 and abs(p.y) < 0.006])))
