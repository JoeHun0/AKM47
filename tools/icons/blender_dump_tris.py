"""Blender (background): dump triangles of gun part sets (in the rig frame: metres, +X muzzle, +Z up,
right side = -Y) to an .npz for the icon camera fit / renders.
Usage: blender -b -P blender_dump_tris.py -- ak74 <out.npz>   |   ... -- akm47 <out.npz>"""
import sys, os, bpy, bmesh
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
which, out = args[0], args[1]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(ROOT, 'model_src', 'ref'); EXP = os.path.join(ROOT, 'model_export')
B = {'jnt_offset': (0, 0, 0), 'jnt_trigger': (0.04570, 0, 0.02210), 'jnt_selector_plate': (0.02260, 0, 0.04270),
     'jnt_shutter': (0.19520, 0, 0.05890), 'jnt_magazine_tab': (0.09640, 0, -0.00110),
     'jnt_magazine': (0.15720, 0, -0.04010), 'jnt_ring': (-0.0624, -0.013, 0.0292)}
SETS = {
    'ak74': {'body': [('SM_wpn_ak74_SM_offset', 'jnt_offset'), ('SM_wpn_ak74_SM_trigger', 'jnt_trigger'),
                      ('SM_wpn_ak74_SM_selector_plate', 'jnt_selector_plate'), ('SM_wpn_ak74_SM_shutter', 'jnt_shutter'),
                      ('SM_wpn_ak74_SM_magazine_tab', 'jnt_magazine_tab'), ('SM_wpn_ak74_SM_ring', 'jnt_ring')],
             'mag': [('SM_ak_mag_full', 'jnt_magazine')]},
    'akm47': {'body': [('SM_AKM47_Body', 'jnt_offset'), ('SM_AKM47_Trigger', 'jnt_trigger'),
                       ('SM_AKM47_Selector', 'jnt_selector_plate'), ('SM_AKM47_Shutter', 'jnt_shutter')],
              'mag': [('SM_AKM47_MagFull', 'jnt_magazine')]},
}
bpy.ops.wm.read_factory_settings(use_empty=True)
data = {}
for setname, parts in SETS[which].items():
    tris = []
    for fname, bone in parts:
        folder = REF if which == 'ak74' else EXP
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(folder, fname + '.fbx'))
        for o in [o for o in bpy.data.objects if o not in before and o.type == 'MESH' and not o.name.startswith('UCX')]:
            bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces)
            for f in bm.faces:
                tris.append([list(o.matrix_world @ v.co + Vector(B[bone])) for v in f.verts])
            bm.free()
    data[setname] = np.array(tris, dtype=np.float32)
    print('SET', which, setname, data[setname].shape)
np.savez(out, **data)
