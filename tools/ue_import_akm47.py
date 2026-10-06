"""Zone Kit (Unreal editor Python): import the AKM-47 model into the AKM47 mod.
Run in the editor's Python console:
    exec(open(r'C:\\Users\\KotnyekJM\\Documents\\stalker 2 mods\\AKM47\\tools\\ue_import_akm47.py').read())
- textures T_AKM47_D / _N / _RMA (virtual texture streaming on, like the game's weapon textures)
- material MI_AKM47 = child of the AKM-74S material MI_ar_ak74_2ID, only the three *_VT textures swapped
- static meshes SM_AKM47_Body/_Trigger/_Selector/_Shutter/_Mag + SM_AKM47 (world, with collision)
Writes model_export/ue_import_report.txt (asset paths, mesh bounds in cm, material slots).
Model: "AK-47" by Lokeig, CC BY-NC 4.0 (CREDITS.txt)."""
import os
import unreal

SRC = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\model_export'
DEST = '/AKM47/Weapons/AKM47'
PARENT_MI = '/Game/_Stalker_2/weapons/sturm_riffle/st_ak74/materials/MI_ar_ak74_2ID'
MESHES = ['SM_AKM47_Body', 'SM_AKM47_Trigger', 'SM_AKM47_Selector', 'SM_AKM47_Shutter', 'SM_AKM47_Mag',
          'SM_AKM47_MagFull', 'SM_AKM47']
# full magazine: its cartridges (slot from Blender material 'MI_amm_calibers_01...') get the game's ammo material,
# taken from the AKM-74S full magazine's slot 1
AMMO_MAT = unreal.load_asset('/Game/_Stalker_2/weapons/sturm_riffle/st_ak74/SM_ak_mag_full').get_material(1)
TEXTURES = {'T_AKM47_D': 'Diffuse_VT', 'T_AKM47_N': 'Normal_VT', 'T_AKM47_RMA': 'RMAE_VT'}
ML = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
log = []

def task(filename, options=None):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(SRC, filename)
    t.destination_path = DEST
    t.automated = True
    t.replace_existing = True
    t.save = True
    if options:
        t.options = options
    return t

# ---- textures
tasks = [task(n + '.png') for n in TEXTURES]
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for name in TEXTURES:
    tex = unreal.load_asset(f'{DEST}/{name}')
    assert tex, name
    if name.endswith('_N'):
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('srgb', False)
    elif name.endswith('_RMA'):
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property('srgb', False)
    tex.set_editor_property('virtual_texture_streaming', True)
    EAL.save_loaded_asset(tex)
    log.append(f'TEXTURE {tex.get_path_name()} srgb={tex.get_editor_property("srgb")} '
               f'vt={tex.get_editor_property("virtual_texture_streaming")}')

# ---- material instance
mi_path = f'{DEST}/MI_AKM47'
mi = unreal.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else None
if not mi:
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'MI_AKM47', DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
ML.set_material_instance_parent(mi, unreal.load_asset(PARENT_MI))
for name, param in TEXTURES.items():
    ok = ML.set_material_instance_texture_parameter_value(mi, param, unreal.load_asset(f'{DEST}/{name}'))
    log.append(f'MI {param} = {name}: {ok}')
ML.update_material_instance(mi)
EAL.save_loaded_asset(mi)
log.append(f'MATERIAL {mi.get_path_name()} parent={mi.get_editor_property("parent").get_path_name()}')

# ---- static meshes
for name in MESHES:
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', False)
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.set_editor_property('import_animations', False)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    sd = ui.get_editor_property('static_mesh_import_data')
    sd.set_editor_property('combine_meshes', True)
    sd.set_editor_property('auto_generate_collision', name == 'SM_AKM47')
    sd.set_editor_property('convert_scene', True)
    sd.set_editor_property('import_uniform_scale', 1.0)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task(name + '.fbx', ui)])
    sm = unreal.load_asset(f'{DEST}/{name}')
    assert sm, name
    for i, slot in enumerate(sm.get_editor_property('static_materials')):
        is_ammo = str(slot.get_editor_property('material_slot_name')).startswith('MI_amm_calibers')
        sm.set_material(i, AMMO_MAT if is_ammo else mi)
        if is_ammo:
            log.append(f'AMMO SLOT {name}[{i}] = {AMMO_MAT.get_path_name() if AMMO_MAT else None}')
    EAL.save_loaded_asset(sm)
    b = sm.get_bounding_box()
    log.append(f'MESH {sm.get_path_name()} slots={len(sm.get_editor_property("static_materials"))} '
               f'min=({b.min.x:.2f},{b.min.y:.2f},{b.min.z:.2f}) max=({b.max.x:.2f},{b.max.y:.2f},{b.max.z:.2f})')

# ---- world mesh sockets: a weapon lying in the world hangs its attachments (magazine, scope...) on
# sockets of its world static mesh. Copy them from the AKM-74S world mesh SM_AK74 (same frame, the models
# line up). Without them the magazine was misplaced on the ground (in game 2026-10-05).
# The StaticMesh 'sockets' list is protected in Python (Zone Kit 2026-10-05), so sockets are found with
# get_sockets_by_tag('') (all untagged ones) plus find_socket() over every socket/bone name the AK74 uses.
src = unreal.load_asset('/Game/_Stalker_2/weapons/sturm_riffle/st_ak74/SM_AK74')
dst = unreal.load_asset(f'{DEST}/SM_AKM47')
NAMES = ['jnt_offset', 'jnt_trigger', 'jnt_selector_plate', 'jnt_shutter', 'jnt_magazine_tab', 'jnt_magazine',
         'jnt_magazine1', 'jnt_bullet', 'jnt_bullet_shell', 'jnt_ring', 'jnt_wpn_ak74', 'jnt_offsetSocket', 'Muzzle',
         'MuzzleFOV', 'GLaunchSocket', 'SilencerMuzzle', 'AutMuzzle', 'X4ScopeSocket', 'RU_X4Scope_1',
         'SilencerMuzzleSocket', 'AutMuzzleSocket', 'AttachmentPositionSocket', 'ShellShutterFOV',
         'AimShellShutterFOV', 'SocketOffset', 'ShellShutter', 'SinMuzzleSocket', 'MagEjectSocket', 'SPSocket',
         'AimSocket', 'GLaunchMuzzleFOV', 'X4ScopeMuzzle', 'SVDM_Scope', 'X4ScopeShells', 'AK9SilencerMuzzleSocket',
         'TopRailSocket', 'AK9ColimScopeSocket', 'Gun_Sotnyk_ColimScope', 'ColimScopeSocket2', 'RU_ColimScope_2',
         'ColimScope2Muzzle', 'MagazineSocket', 'ScopeSocket', 'SilencerSocket', 'Magazine', 'Scope', 'Silencer']
def all_sockets(mesh):
    found = {str(s.get_editor_property('socket_name')): s for s in mesh.get_sockets_by_tag('')}
    for n in NAMES:
        s = mesh.find_socket(n)
        if s:
            found[n] = s
    return found
for s in all_sockets(dst).values():
    dst.remove_socket(s)
src_sockets = all_sockets(src)
for name, s in src_sockets.items():
    n = unreal.StaticMeshSocket(outer=dst)
    for prop in ('socket_name', 'relative_location', 'relative_rotation', 'relative_scale', 'tag'):
        n.set_editor_property(prop, s.get_editor_property(prop))
    dst.add_socket(n)
    log.append(f'SOCKET {name} {s.get_editor_property("relative_location")} tag={s.get_editor_property("tag")!r}')
EAL.save_loaded_asset(dst)
log.append(f'SOCKETS copied: {len(all_sockets(dst))} of {len(src_sockets)} found on SM_AK74')

with open(os.path.join(SRC, 'ue_import_report.txt'), 'w') as f:
    f.write('\n'.join(log) + '\n')
print('AKM47 IMPORT DONE', len(log), 'lines -> model_export/ue_import_report.txt')
