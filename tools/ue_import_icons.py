"""Zone Kit (editor Python, Select Mod = AKM47): import the AKM-47 icon PNGs (rendered by tools/icons/make_icons.sh)
as UI textures with the same settings as the AKM-74S icons (model_src/ref/icons/icons_report.txt):
UserInterface2D compression, TEXTUREGROUP_UI, sRGB, no mipmaps (upgrade images: mips from texture group),
never stream, no virtual texture. Run:
    exec(open(r'C:\\Users\\KotnyekJM\\Documents\\stalker 2 mods\\AKM47\\tools\\ue_import_icons.py').read())
Writes model_export/icons/ue_import_icons_report.txt."""
import os
import unreal

SRC = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\model_export\icons'
DEST = '/AKM47/UI/Icons'
ICONS = ['T_inv_w_akm47_body', 'T_inv_w_akm47_defaultmag', 'T_inv_w_akm47_body_upgrade',
         'T_inv_w_akm47_defaultmag_upgrade', 'T_pda_statistic_weapon_akm47']
EAL = unreal.EditorAssetLibrary
log = []

tasks = []
for name in ICONS:
    t = unreal.AssetImportTask()
    t.filename = os.path.join(SRC, name + '.png')
    t.destination_path = DEST
    t.automated = True
    t.replace_existing = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

for name in ICONS:
    tex = unreal.load_asset(f'{DEST}/{name}')
    if not tex:
        log.append(f'MISSING {name}'); continue
    pda = name.startswith('T_pda')
    tex.set_editor_property('compression_settings',
                            unreal.TextureCompressionSettings.TC_DEFAULT if pda else unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('srgb', True)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP if name.endswith('_upgrade')
                            else unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('never_stream', True)
    tex.set_editor_property('virtual_texture_streaming', False)
    EAL.save_loaded_asset(tex)
    log.append(f'TEX {tex.get_path_name()} {tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()} '
               f'comp={tex.get_editor_property("compression_settings")} vt={tex.get_editor_property("virtual_texture_streaming")}')

with open(os.path.join(SRC, 'ue_import_icons_report.txt'), 'w') as f:
    f.write('\n'.join(log) + '\n')
print('AKM47 ICON IMPORT DONE', len(log), 'lines -> model_export/icons/ue_import_icons_report.txt')
