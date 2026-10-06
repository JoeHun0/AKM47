"""Blender (background): render a gun icon layer with a camera fitted by fit_camera2.py.
Usage: blender -b -P blender_render_icon.py -- <ak74|akm47> <parts: body|mag|body+mag> <cam.json> <out.png>
          [--left] [--flip] [--grey] [--engine EEVEE|CYCLES|WORKBENCH] [--samples N] [--exposure E] [--holdout body]
--left: the icon shows the gun's left side (inventory icons: the fit was made on the mirrored right view).
--flip: use the mirror-ambiguous solution (-yaw, -pitch) instead.
--grey: plain grey material (geometry check). Output: RGBA PNG, transparent background, same size as the icon."""
import sys, os, json, math, bpy
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
which, parts, camf, out = argv[:4]
opt = argv[4:]
left, flip, grey = '--left' in opt, '--flip' in opt, '--grey' in opt
engine = opt[opt.index('--engine') + 1] if '--engine' in opt else 'CYCLES'
holdout = opt[opt.index('--holdout') + 1].split('+') if '--holdout' in opt else []   # parts that only hide others
samples = int(opt[opt.index('--samples') + 1]) if '--samples' in opt else 64
exposure = float(opt[opt.index('--exposure') + 1]) if '--exposure' in opt else 0.0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF, EXP = os.path.join(ROOT, 'model_src', 'ref'), os.path.join(ROOT, 'model_export')
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
cam = json.load(open(camf))
W, H = cam['size']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---- materials
def tex_material():
    m = bpy.data.materials.new('akm47'); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    def img(name, colour):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(EXP, name))
        if not colour: n.image.colorspace_settings.name = 'Non-Color'
        return n
    d, nm, rma = img('T_AKM47_D.png', True), img('T_AKM47_N.png', False), img('T_AKM47_RMA.png', False)
    nt.links.new(d.outputs['Color'], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(rma.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Red'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Green'], bsdf.inputs['Metallic'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    return m
def brass_material():
    m = bpy.data.materials.new('brass'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.55, 0.38, 0.14, 1); b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.35
    return m
greym = bpy.data.materials.new('grey'); greym.diffuse_color = (0.6, 0.6, 0.6, 1)
gunm = None if grey or which == 'ak74' else tex_material()
brassm = brass_material()

# ---- geometry
objs = []
for setname in parts.split('+') + holdout:
    for fname, bone in SETS[which][setname]:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(REF if which == 'ak74' else EXP, fname + '.fbx'))
        for o in [o for o in bpy.data.objects if o not in before]:
            if o.type != 'MESH' or o.name.startswith('UCX'):
                bpy.data.objects.remove(o); continue
            o.location += Vector(B[bone])
            for i, slot in enumerate(o.material_slots):
                name = slot.material.name if slot.material else ''
                o.material_slots[i].material = (greym if grey or which == 'ak74' else
                                                brassm if name.startswith('MI_amm') else gunm)
            o.is_holdout = setname in holdout     # e.g. the body hides the top of a magazine layer, like vanilla
            objs.append(o)

# ---- camera from the fit (see fit_camera.project: camera at -y in the rotated frame, image right = +x, up = +z)
yaw, pitch, roll = cam['yaw'], cam['pitch'], cam['roll']
if flip: yaw, pitch = -yaw, -pitch
def rot(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = Matrix(((cy, -sy, 0), (sy, cy, 0), (0, 0, 1)))
    Rx = Matrix(((1, 0, 0), (0, cp, -sp), (0, sp, cp)))
    Ry = Matrix(((cr, 0, sr), (0, 1, 0), (-sr, 0, cr)))
    return Ry @ Rx @ Rz
R = rot(yaw, pitch, roll); Rt = R.transposed()
centre = Vector(cam['centre'])
right, up, fwd = Rt @ Vector((1, 0, 0)), Rt @ Vector((0, 0, 1)), Rt @ Vector((0, 1, 0))
pos = centre - fwd * cam['d']
if left:                                    # reflect the camera through the y=0 plane, keep it right-handed
    M = lambda v: Vector((v.x, -v.y, v.z))
    pos, right, up, fwd = M(pos), -M(right), M(up), M(fwd)
    centre = M(centre)
camobj = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(camobj); sc.camera = camobj
mat = Matrix((right, up, -fwd)).transposed()
camobj.matrix_world = Matrix.Translation(pos) @ mat.to_4x4()
cd = camobj.data; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0
f_px = cam['s'] * cam['d']
cd.lens = f_px * cd.sensor_width / W
md = max(W, H)
# the optical axis lands on the fitted offset (tx, ty) - also for the left-side camera (see the reflection above)
cd.shift_x = (W / 2 - cam['tx']) / md
cd.shift_y = (cam['ty'] - H / 2) / md
cd.clip_start, cd.clip_end = max(0.01, cam['d'] - 2), cam['d'] + 2   # far cameras: keep the gun inside the clip range

# ---- lighting: soft studio light from the upper front, like the vanilla icons
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
if engine == 'WORKBENCH':
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
else:
    sc.render.engine = 'CYCLES' if engine == 'CYCLES' else 'BLENDER_EEVEE_NEXT'
    if engine == 'CYCLES':
        sc.cycles.samples = samples; sc.cycles.use_denoising = True
    world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.08, 0.08, 0.08, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    def light(name, loc, energy, size):
        l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size
        o = bpy.data.objects.new(name, l); sc.collection.objects.link(o)
        o.location = centre + Vector(loc); o.rotation_euler = (centre - o.location).to_track_quat('-Z', 'Y').to_euler()
    side = 1 if left else -1
    light('key', (0.3, side * 1.2, 1.2), 300, 1.5)
    light('fill', (-0.8, side * 1.0, 0.2), 80, 2.0)
    light('rim', (0.0, -side * 1.0, 1.0), 120, 1.0)
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('RENDERED', out, 'lens', round(cd.lens, 2), 'shift', round(cd.shift_x, 4), round(cd.shift_y, 4))
