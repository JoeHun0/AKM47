"""Blender (background): put the AK-47 model into the AKM-74S frame and render overlay pictures.
Usage: blender.exe -b -P tools\\blender_align.py -- <out_dir> [scale] [dx_cm] [dz_cm]
Frame = the game's weapon frame as Blender imports UE FBX: meters, origin = bone jnt_offset,
+X = muzzle, +Z = up. Reference = the AKM-74S part meshes exported from the Zone Kit (model_src/ref).
The AK-47 is scaled by `scale` (meters per model unit), its bore axis put on the AKM-74S bore axis
(Muzzle socket: z = 4.996 cm, y = 0) and its trigger centre on the AKM-74S trigger centre, then moved by
dx/dz (cm) for fine tuning. Writes side.png / top.png (reference red, AK-47 green, both see-through)."""
import sys, os, math
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]
SCALE = float(args[1]) if len(args) > 1 else 0.88 / 1.9168     # real AKM length / model length
DX = float(args[2]) / 100 if len(args) > 2 else 0.0
DZ = float(args[3]) / 100 if len(args) > 3 else 0.0
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'model_src')
os.makedirs(OUT, exist_ok=True)

BORE_Z = 0.04996                       # Muzzle socket height above jnt_offset
REF_TRIGGER_BONE = Vector((0.04570, 0, 0.02210))
REF_PARTS = {  # part mesh -> bone it hangs on (bone heads from SK_AK74.fbx, relative to jnt_offset)
    'SM_wpn_ak74_SM_offset': (0, 0, 0), 'SM_wpn_ak74_SM_trigger': (0.04570, 0, 0.02210),
    'SM_wpn_ak74_SM_selector_plate': (0.02260, 0, 0.04270), 'SM_wpn_ak74_SM_shutter': (0.19520, 0, 0.05890),
    'SM_wpn_ak74_SM_magazine_tab': (0.09640, 0, -0.00110), 'SM_ak_mag_full': (0.15720, 0, -0.04010),
}

bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]

def mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    return m

red, green = mat('ref', (1, 0.1, 0.1, 0.45)), mat('new', (0.1, 1, 0.2, 0.45))

# reference AKM-74S, each part moved onto its bone
for part, head in REF_PARTS.items():
    for o in imp(os.path.join(SRC, 'ref', part + '.fbx')):
        if o.type != 'MESH' or o.name.startswith('UCX_'):
            bpy.data.objects.remove(o)
            continue
        o.location += Vector(head)
        o.data.materials.clear(); o.data.materials.append(red)

# AK-47
new = [o for o in imp(os.path.join(SRC, 'AKM.fbx')) if o.type == 'MESH']
def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector((min(p[i] for p in pts) for i in range(3))), Vector((max(p[i] for p in pts) for i in range(3))))
barrel = [o for o in new if o.name.startswith('r_barrel_low')]
trig = [o for o in new if o.name.startswith('bm_trigger_low')]
blo, bhi = bbox(barrel); bore_model = (blo + bhi) / 2
tlo, thi = bbox(trig); trig_model = (tlo + thi) / 2
ref_trig = [o for o in bpy.data.objects if o.name.startswith('SM_wpn_ak74_SM_trigger')]
rlo, rhi = bbox(ref_trig); trig_ref = (rlo + rhi) / 2
# model -> game: p' = (p - origin) * S + target
origin = Vector((trig_model.x, bore_model.y, bore_model.z))
target = Vector((trig_ref.x + DX, 0.0, BORE_Z + DZ))
root = bpy.data.objects.new('AK47_root', None)
bpy.context.scene.collection.objects.link(root)
for o in new:
    o.parent = root
    o.data.materials.clear(); o.data.materials.append(green)
for o in new:
    o.location = (o.location - origin)
root.scale = (SCALE,) * 3
root.location = target
bpy.context.view_layer.update()
nlo, nhi = bbox(new)
print(f'AK47 placed: scale={SCALE:.4f} bbox min={tuple(round(v*100,2) for v in nlo)} max={tuple(round(v*100,2) for v in nhi)} cm')
print(f'  muzzle end x={nhi.x*100:.2f} cm (AKM-74S Muzzle socket 65.70, SPSocket 57.34)')
for n in ('r_barrelEnd_low', 'bm_magazine_low', 'bl_grip_low', 'l_stockWood_low', 'r_flap_low', 'm_safetyswitch_low', 'bm_trigger_low'):
    lo, hi = bbox([o for o in new if o.name.startswith(n)])
    print(f'  {n:22} min={tuple(round(v*100,2) for v in lo)} max={tuple(round(v*100,2) for v in hi)}')

# render: workbench, orthographic, flat colours, see-through
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = 0.5
sc.render.resolution_x, sc.render.resolution_y = 2400, 900
sc.world = bpy.data.worlds.new('w'); sc.world.color = (1, 1, 1)
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 1.0
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
for name, loc, rot in (('side', (0.17, -2, 0.0), (math.radians(90), 0, 0)),
                       ('top', (0.17, 0, 2), (0, 0, 0))):
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
print('rendered to', OUT)
