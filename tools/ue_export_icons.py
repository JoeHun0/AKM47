"""Zone Kit (editor Python): export the AKM-74S inventory icon layers + PDA statistics image as PNG, with their
texture settings, so the AKM-47 icons can be rendered to match. Run in the Python console:
    exec(open(r'C:\\Users\\KotnyekJM\\Documents\\stalker 2 mods\\AKM47\\tools\\ue_export_icons.py').read())
Writes model_src/ref/icons/*.png and model_src/ref/icons/icons_report.txt."""
import os
import unreal

OUT = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\model_src\ref\icons'
FOLDERS = ['/Game/GameLite/FPS_Game/UIRemaster/UITextures/Inventory/WeaponAndAttachments/AK74']
SINGLE = ['/Game/GameLite/FPS_Game/UIRemaster/UITextures/PDA/Stats/Weapons/T_pda_statistic_weapon_ak74',
          # a second rifle for style reference (vanilla look)
          '/Game/GameLite/FPS_Game/UIRemaster/UITextures/PDA/Stats/Weapons/T_pda_statistic_weapon_ak74_combatant']
PROPS = ('compression_settings', 'lod_group', 'srgb', 'mip_gen_settings', 'virtual_texture_streaming',
         'never_stream', 'filter', 'compression_no_alpha')
os.makedirs(OUT, exist_ok=True)
log = []

paths = list(SINGLE)
for folder in FOLDERS:
    paths += [p.split('.')[0] for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True)]

for path in paths:
    tex = unreal.load_asset(path)
    if not isinstance(tex, unreal.Texture2D):
        log.append(f'SKIP {path} ({tex.get_class().get_name() if tex else "not found"})')
        continue
    name = path.split('/')[-1]
    t = unreal.AssetExportTask()
    t.object = tex
    t.filename = os.path.join(OUT, name + '.png')
    t.automated = True
    t.replace_identical = True
    t.prompt = False
    ok = unreal.Exporter.run_asset_export_task(t)
    props = []
    for p in PROPS:
        try:
            props.append(f'{p}={tex.get_editor_property(p)}')
        except Exception:
            pass
    log.append(f'TEX {name} export={ok} size={tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()} ' + ' '.join(props))

with open(os.path.join(OUT, 'icons_report.txt'), 'w') as f:
    f.write('\n'.join(log) + '\n')
print('AKM47 ICON EXPORT DONE', len(log), 'lines -> model_src/ref/icons/icons_report.txt')
