"""Blender (background): cut the AK-47 model into the game's AKM-74S part layout and export one FBX per part.
Usage: blender.exe -b -P tools\\blender_export_parts.py -- <out_dir>
Same placement as blender_align.py (checked by overlay renders 2026-10-05: matches the AKM-74S with no
tweaks). Each part is exported with its origin on the bone it hangs on (WeaponStaticMeshParts /
magazine attach socket), in the frame Blender gets when importing the game's FBX (meters, +X muzzle,
+Z up, right side = -Y); Blender's default FBX export turns that back into the game's frame.
Model: "AK-47" by Lokeig, CC BY-NC 4.0 (see CREDITS.txt)."""
import sys, os
import bpy
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--') + 1:][0]
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'model_src', 'AKM.fbx')
os.makedirs(OUT, exist_ok=True)

SCALE = 0.88 / 1.9168              # real AKM length / model length (m per model unit)
BORE_Z = 0.04996                   # AKM-74S Muzzle socket height above jnt_offset
REF_TRIGGER_X = 0.0449             # AKM-74S trigger mesh centre x (bone 4.57 cm + mesh centre -0.08 cm)
BONES = {'jnt_offset': (0, 0, 0), 'jnt_trigger': (0.04570, 0, 0.02210), 'jnt_selector_plate': (0.02260, 0, 0.04270),
         'jnt_shutter': (0.19520, 0, 0.05890), 'jnt_magazine_tab': (0.09640, 0, -0.00110),
         'jnt_magazine': (0.15720, 0, -0.04010)}
PARTS = {  # exported mesh -> (bone, AK-47 objects by name prefix); body = everything not listed
    'SM_AKM47_Trigger': ('jnt_trigger', ['bm_trigger_low']),
    'SM_AKM47_Selector': ('jnt_selector_plate', ['m_safetyswitch_low']),
    # bolt carrier = u_dustcoverHolder_low (seen through the ejection port, despite its name) + the charging
    # handle r_flap_low on its front; both move with jnt_shutter (in game the carrier stood still, 2026-10-05)
    'SM_AKM47_Shutter': ('jnt_shutter', ['r_flap_low', 'u_dustcoverHolder_low']),
    # no magazine release: bm_magazinePart3 sits 3 cm above the AKM-74S tab (part of the mag well) -> body
    'SM_AKM47_Mag': ('jnt_magazine', ['bm_magazine_low', 'bm_magazineBottom_low']),
}
BODY = 'SM_AKM47_Body'
WORLD = 'SM_AKM47'                  # whole gun without magazine, for lying in the world (like SM_AK74)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
assert len(objs) == 65, len(objs)

def bbox(os_):
    pts = [o.matrix_world @ Vector(c) for o in os_ for c in o.bound_box]
    return (Vector((min(p[i] for p in pts) for i in range(3))), Vector((max(p[i] for p in pts) for i in range(3))))
def named(prefix):
    found = [o for o in objs if o.name.startswith(prefix)]
    assert len(found) == 1, (prefix, [o.name for o in found])
    return found[0]

blo, bhi = bbox([named('r_barrel_low')]); bore = (blo + bhi) / 2
tlo, thi = bbox([named('bm_trigger_low')]); trig = (tlo + thi) / 2
origin = Vector((trig.x, bore.y, bore.z))
target = Vector((REF_TRIGGER_X, 0, BORE_Z))

# bake placement into the mesh data, objects end up at identity transforms
for o in objs:
    mw = o.matrix_world.copy()
    o.data.transform(mw)
    o.matrix_world.identity()
    for v in o.data.vertices:
        v.co = (v.co - origin) * SCALE + target
    o.data.update()

# Front sight post: the model has only the round drum at the post's base inside the front sight hood, no
# post (in game 2026-10-05 the hood looked empty when aiming). Add a thin steel post on the drum, its tip
# just below the hood ears (ears: |y| >= 4.1 mm, top 9.78 cm). The model's own sight heights are kept:
# moving them to the AKM-74S sight line (0.8 build) put the gun in a worse aiming position (user).
POST_X, POST_R, POST_Z0, POST_Z1 = 0.5575, 0.0012, 0.0845, 0.0962   # m, game frame (drum x 55.30-56.20, top 8.57 cm)
drum = named('r_barrelAimCylinder_low')
uv_mean = [sum(d.uv[i] for d in drum.data.uv_layers[0].data) / len(drum.data.uv_layers[0].data) for i in (0, 1)]
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=POST_R, depth=POST_Z1 - POST_Z0,
                                    location=(POST_X, 0.0, (POST_Z0 + POST_Z1) / 2))
post = bpy.context.active_object
post.name = post.data.name = 'f_frontSightPost'
post.data.transform(post.matrix_world); post.matrix_world.identity()
uvl = post.data.uv_layers[0]
uvl.name = drum.data.uv_layers[0].name
for d in uvl.data:
    d.uv = uv_mean                       # same dark steel as the drum
post.data.materials.append(drum.data.materials[0])
objs.append(post)

# Front sight onto the AKM-74S aim point: SK_AK74 socket AimSocket = (56.57, +0.26, 9.83) cm from jnt_offset
# (UE y, + = right). Our post tip was at y 0, z 9.62 -> in game the front sight sat a little left and low
# when aiming (2026-10-05). Shift post + drum fully and the hood above the barrel (blended in from z 6.2 to
# 7.68 cm so its base stays on the barrel). Rear sight untouched (moving it made aiming worse in 0.8).
FS_DY, FS_DZ = -0.0026, 0.0021                    # Blender y (right = -y), z; metres
def fs_shift(o, z_from=None, z_full=None):
    for v in o.data.vertices:
        f = 1.0 if z_from is None else min(1.0, max(0.0, (v.co.z - z_from) / (z_full - z_from)))
        v.co.y += FS_DY * f; v.co.z += FS_DZ * f
    o.data.update()
fs_shift(post); fs_shift(drum); fs_shift(named('r_barrelAim_low'), 0.062, 0.0768)

def join_copy(sources, name, head):
    """Duplicate the sources, join them into one object named `name`, origin moved to `head`."""
    bpy.ops.object.select_all(action='DESELECT')
    dups = []
    for s in sources:
        d = s.copy(); d.data = s.data.copy()
        bpy.context.scene.collection.objects.link(d)
        dups.append(d)
    for d in dups:
        d.select_set(True)
    bpy.context.view_layer.objects.active = dups[0]
    if len(dups) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = j.data.name = name
    for v in j.data.vertices:
        v.co -= Vector(head)
    j.data.update()
    return j

def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                             mesh_smooth_type='FACE', use_mesh_modifiers=False, add_leaf_bones=False,
                             bake_anim=False, path_mode='STRIP')

used = set()
report = []
for name, (bone, prefixes) in PARTS.items():
    src = [named(p) for p in prefixes]
    used.update(src)
    j = join_copy(src, name, BONES[bone])
    export(j, os.path.join(OUT, name + '.fbx'))
    lo, hi = bbox([j])
    report.append((name, bone, len(j.data.polygons), lo, hi))
body_src = [o for o in objs if o not in used]
j = join_copy(body_src, BODY, BONES['jnt_offset'])
export(j, os.path.join(OUT, BODY + '.fbx'))
lo, hi = bbox([j]); report.append((BODY, 'jnt_offset', len(j.data.polygons), lo, hi))
# Full magazine = our magazine + the top two rounds of the AKM-74S full magazine (SM_ak_mag_full, material slot
# 1 = MI_amm_calibers_01; each round is a case + bullet island). The AK-47 model has no cartridges; in game the
# AKM-74S live-round part (jnt_bullet) floated inside our receiver, so it was dropped and the round now comes
# with the magazine like on the AKM-74S (2026-10-05). Both magazines hang on jnt_magazine, so the vanilla
# rounds only need ROUND_SHIFT to sit on our (lower, slightly shorter) magazine top.
import bmesh
ROUND_SHIFT = Vector((-0.005, 0.0, -0.0073))   # 0.7 cm further back than the rear-edge match: tips just past the front
ROUND_TOP_MIN_Z = 0.0800                           # islands of the top two rounds reach above this (vanilla)
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=os.path.join(os.path.dirname(HERE), 'model_src', 'ref', 'SM_ak_mag_full.fbx'))
vmag = [o for o in bpy.data.objects if o not in before and o.type == 'MESH' and not o.name.startswith('UCX')][0]
vmag.data.transform(vmag.matrix_world); vmag.matrix_world.identity()
bm = bmesh.new(); bm.from_mesh(vmag.data)
keep, seen = set(), set()
for f in bm.faces:
    if f.material_index != 1 or f.index in seen: continue
    comp, stack = [], [f]
    while stack:
        g = stack.pop()
        if g.index in seen: continue
        seen.add(g.index); comp.append(g)
        stack += [h for e in g.edges for h in e.link_faces if h.material_index == 1 and h.index not in seen]
    if max(v.co.z for g in comp for v in g.verts) > ROUND_TOP_MIN_Z:
        keep.update(g.index for g in comp)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
for v in bm.verts: v.co += ROUND_SHIFT
bm.to_mesh(vmag.data); bm.free()
vmag.data.materials.clear(); vmag.data.materials.append(bpy.data.materials.new('MI_amm_calibers_01'))
for p in vmag.data.polygons: p.material_index = 0
vmag.name = vmag.data.name = 'ak74_top_rounds'
mag_full = join_copy([named('bm_magazine_low'), named('bm_magazineBottom_low')], 'SM_AKM47_MagFull', BONES['jnt_magazine'])
rounds = vmag.copy(); rounds.data = vmag.data.copy(); bpy.context.scene.collection.objects.link(rounds)
bpy.ops.object.select_all(action='DESELECT'); mag_full.select_set(True); rounds.select_set(True)
bpy.context.view_layer.objects.active = mag_full; bpy.ops.object.join()
export(mag_full, os.path.join(OUT, 'SM_AKM47_MagFull.fbx'))
lo, hi = bbox([mag_full]); report.append(('SM_AKM47_MagFull', 'jnt_magazine', len(mag_full.data.polygons), lo, hi))
print('ROUNDS kept faces', len(keep), 'materials', [m.name for m in mag_full.data.materials])

world_src = [o for o in objs if o not in (named('bm_magazine_low'), named('bm_magazineBottom_low'))]
j = join_copy(world_src, WORLD, (0, 0, 0))
export(j, os.path.join(OUT, WORLD + '.fbx'))
lo, hi = bbox([j]); report.append((WORLD, '(world)', len(j.data.polygons), lo, hi))
for name, bone, n, lo, hi in report:
    print(f'EXPORTED {name:22} on {bone:20} polys={n:6} bbox cm min={tuple(round(v*100,2) for v in lo)} max={tuple(round(v*100,2) for v in hi)}')
