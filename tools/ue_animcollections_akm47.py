"""Zone Kit (editor Python): give the AKM-47's own magazine item the AKM-74S reload animations.
Reload/attach animations are listed per magazine item SID inside the AK74 animation collections, so
GunAKM47_MagDefault gets an exact copy of every GunAK74_MagDefault entry (same animations).
FIRST check out the three collections into the AKM47 mod (Content Browser: right-click -> Checkout):
  /Game/_STALKER2/Animations/Weapons/ar/AK74/AnimCollections/AnimCollection_fp_AK74
  /Game/_STALKER2/Animations/Weapons/ar/AK74/AnimCollections/AnimCollection_fp_AK74_GrenLaunch
  /Game/_STALKER2/Animations/Weapons/ar/AK74/AnimCollections/AnimCollection_tp_AK74
then run (Select Mod = AKM47):
    exec(open(r'C:\\Users\\KotnyekJM\\Documents\\stalker 2 mods\\AKM47\\tools\\ue_animcollections_akm47.py').read())
Writes model_export/ue_animcollections_report.txt."""
import os
import unreal

BASE = '/Game/_STALKER2/Animations/Weapons/ar/AK74/AnimCollections/'
COLLECTIONS = ['AnimCollection_fp_AK74', 'AnimCollection_fp_AK74_GrenLaunch', 'AnimCollection_tp_AK74']
SRC, NEW = 'GunAK74_MagDefault', 'GunAKM47_MagDefault'
REPORT = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\model_export\ue_animcollections_report.txt'
log = []

def add_copy(m, where):
    """m: a map keyed by magazine SID. Adds NEW = copy of SRC. Returns the map."""
    keys = {str(k): k for k in m.keys()}
    if SRC not in keys:
        log.append(f'  {where}: no {SRC} (keys {sorted(keys)})')
        return m, False
    m[unreal.Name(NEW)] = m[keys[SRC]]
    log.append(f'  {where}: added {NEW} (now {len(m)} entries)')
    return m, True

def try_get(obj, *names):
    for n in names:
        try:
            return n, obj.get_editor_property(n)
        except Exception:
            pass
    return None, None

# Saving a game asset that was NOT checked out first silently writes nothing (2026-10-05: save returned True,
# no file in the mod). So refuse to edit until all three copies exist inside the mod folder.
MOD_DIR = r'D:\Programs\Epic\STALKER2ZoneKit\Stalker2\Mods\AKM47\Content'
in_mod = {}
for root, _, files in os.walk(MOD_DIR):
    for f in files:
        # case-insensitive: the tp asset's real name is 'Animcollection_tp_AK74' (lower-case c)
        match = [n for n in COLLECTIONS if f.lower() == n.lower() + '.uasset']
        if match:
            in_mod[match[0]] = os.path.join(root, f)
missing = [n for n in COLLECTIONS if n not in in_mod]
if missing:
    log.append('NOT CHECKED OUT into the AKM47 mod (right-click -> Checkout first): ' + ', '.join(missing))
    COLLECTIONS = []
before = {n: os.path.getmtime(p) for n, p in in_mod.items()}

for name in COLLECTIONS:
    path = BASE + name
    asset = unreal.load_asset(path)
    log.append(f'{name}: {"loaded" if asset else "NOT FOUND"} {asset.get_class().get_name() if asset else ""}')
    if not asset:
        continue
    ia = asset.get_editor_property('internal_animations')
    changed = False
    # first person: Reloading / AttachingBySID are maps keyed by magazine SID
    for field in ('reloading', 'attaching_by_sid'):
        fname, m = try_get(ia, field)
        if m is None:
            continue
        keys = [str(k) for k in m.keys()]
        if SRC in keys:
            m, ok = add_copy(m, field)
            ia.set_editor_property(fname, m)
            changed |= ok
        elif field == 'reloading':
            # third person: Reloading / ReloadingInCover are keyed by stance, each with a MagazineReload map
            for f2 in ('reloading', 'reloading_in_cover'):
                fn2, sm = try_get(ia, f2)
                if sm is None:
                    continue
                for stance in list(sm.keys()):
                    entry = sm[stance]
                    mr = entry.get_editor_property('magazine_reload')
                    mr, ok = add_copy(mr, f'{f2}[{stance}]')
                    entry.set_editor_property('magazine_reload', mr)
                    sm[stance] = entry
                    changed |= ok
                ia.set_editor_property(fn2, sm)
    if changed:
        asset.set_editor_property('internal_animations', ia)
        ok = unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
        log.append(f'  saved: {ok}, mod file {in_mod[name]} updated: {os.path.getmtime(in_mod[name]) > before[name]}')

with open(REPORT, 'w') as f:
    f.write('\n'.join(log) + '\n')
print('AKM47 ANIMCOLLECTIONS DONE', len(log), 'lines -> model_export/ue_animcollections_report.txt')
