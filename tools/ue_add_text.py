"""Zone Kit (editor Python, Select Mod = AKM47): add the mod texts from text/AKM47_text.txt to the mod's
Localization Mod TextTool asset, so they don't have to be typed in by hand. Run:
    exec(open(r'C:\\Users\\KotnyekJM\\Documents\\stalker 2 mods\\AKM47\\tools\\ue_add_text.py').read())
Then Tools -> Refresh Mod TextTool, and open the asset to look at the new entries.

How: the asset holds an array of entries (SID + per-language strings). This editor doesn't list the asset's fields
to Python, so the script first writes a .t3d text dump of the asset and takes the field names from it. It uses the
existing entry sid_items_GunAKM47_ST_name as the template (so the language keys are exactly the ones the editor
uses) and appends every text-file SID the asset doesn't have yet, English + Ukrainian. Existing entries are never
changed. If anything looks different from that, it changes nothing and writes what it found to the report.
Undo: Ctrl+Z right after (one transaction), or delete the entries in the asset.
Writes tools/ue_add_text_report.txt and tools/ue_text_asset.t3d (the dump)."""
import re
import unreal

TEXT = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\text\AKM47_text.txt'
REPORT = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\tools\ue_add_text_report.txt'
T3D = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47\tools\ue_text_asset.t3d'
ROOT = '/AKM47'
TEMPLATE_SID = 'sid_items_GunAKM47_ST_name'
EAL = unreal.EditorAssetLibrary
log = []
T3D_NAMES = []      # property / struct field names seen in the .t3d dump (filled in run())


def snake(n):
    """UE property name -> Python name (LocalizedStrings -> localized_strings, SID -> sid)."""
    n = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', n)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', n).lower()


def props(obj):
    """(name, kind) of an object's / struct's editor properties: from the class description, or, when the editor
    doesn't list them (this asset type), by trying every name from the .t3d dump."""
    found = re.findall(r'``(\w+)`` \(([^)]*)\)', type(obj).__doc__ or '')
    if found:
        return found
    out = []
    for n in T3D_NAMES:
        for cand in (snake(n), n):
            try:
                v = obj.get_editor_property(cand)
            except Exception:
                continue
            kind = 'Array[' if isinstance(v, unreal.Array) else 'Map[' if isinstance(v, unreal.Map) else type(v).__name__
            if cand not in [o[0] for o in out]:
                out.append((cand, kind))
            break
    return out


def same_kind(template, s):
    """s as the same Python type as template (str / Text / Name)."""
    if isinstance(template, unreal.Text):
        return unreal.Text(s)
    if isinstance(template, unreal.Name):
        return unreal.Name(s)
    if isinstance(template, str):
        return s
    raise TypeError(f'unexpected text type {type(template).__name__}')


def lang_of(k):
    s = str(k).lower()
    if 'english' in s or re.search(r'(^|[^a-z])en([^a-z]|$)', s):
        return 'en'
    if 'ukrain' in s or re.search(r'(^|[^a-z])uk([^a-z]|$)', s):
        return 'uk'
    return None


def run():
    # ---- texts from the file
    texts, cur = {}, None
    for line in open(TEXT, encoding='utf-8'):
        s = line.strip()
        if re.match(r'^sid_\w+$', s):
            cur = s
            texts[cur] = {}
        elif cur and s.startswith('English:'):
            texts[cur]['en'] = s.split(':', 1)[1].strip()
        elif cur and s.startswith('Ukrainian:'):
            texts[cur]['uk'] = s.split(':', 1)[1].strip()
    bad = [k for k, v in texts.items() if set(v) != {'en', 'uk'}]
    log.append(f'text file: {len(texts)} SIDs' + (f'; MISSING a language: {bad}' if bad else ''))
    if bad:
        return

    # ---- the asset
    found = []
    for p in EAL.list_assets(ROOT, recursive=True, include_folder=False):
        d = EAL.find_asset_data(p)
        cls = str(d.asset_class_path.asset_name) if hasattr(d, 'asset_class_path') else str(d.asset_class)
        if cls == 'LocalizationModTextToolAsset':
            found.append(p)
    log.append(f'LocalizationModTextToolAsset under {ROOT}: {found}')
    if len(found) != 1:
        log.append('STOP: expected exactly one text asset (select the AKM47 mod first)')
        return
    asset = EAL.load_asset(found[0])

    # ---- .t3d dump: the real field names and how the existing entries are stored
    t = unreal.AssetExportTask()
    t.object = asset
    t.filename = T3D
    t.automated = True
    t.prompt = False
    t.replace_identical = True
    log.append(f'.t3d dump written: {unreal.Exporter.run_asset_export_task(t)} -> {T3D}')
    try:
        raw = open(T3D, 'rb').read()
        dump = raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8', errors='replace')
    except OSError:
        dump = ''
    for n in re.findall(r'(?:^|[\s(,])([A-Za-z_]\w*)(?:\(\d+\))?=', dump, re.M):
        if n not in T3D_NAMES and n not in ('Begin', 'End', 'Name', 'Class', 'Archetype'):
            T3D_NAMES.append(n)
    log.append(f'names in the dump: {T3D_NAMES}')
    log.append(f'asset properties: {props(asset)}')

    # ---- the entry array and its fields, found via the template entry
    arr_name = arr = template = sid_field = None
    for name, typ in props(asset):
        if not typ.startswith('Array['):
            continue
        value = asset.get_editor_property(name)
        for el in value:
            for fname, ftyp in props(el):
                try:
                    if str(el.get_editor_property(fname)) == TEMPLATE_SID:
                        arr_name, arr, template, sid_field = name, value, el, fname
                except Exception:
                    pass
    if template is None:
        log.append(f'STOP: no entry with SID {TEMPLATE_SID} found in any array property')
        return
    eprops = props(template)
    log.append(f'entries in {arr_name!r}: {len(arr)}; entry fields: {eprops}; SID field: {sid_field}')
    strings = [(n, t) for n, t in eprops if n != sid_field and (t.startswith('Map[') or t.startswith('Array['))]
    if len(strings) != 1:
        log.append(f'STOP: expected one map/array field for the strings, got {strings}')
        return
    str_field, str_type = strings[0]
    tmpl_strings = template.get_editor_property(str_field)
    other = [(n, str(template.get_editor_property(n))) for n, t in eprops if n not in (sid_field, str_field)]
    log.append(f'strings field: {str_field} ({str_type}); other template fields (left default): {other}')

    if str_type.startswith('Map['):
        keys = {lang_of(k): k for k in tmpl_strings.keys()}
        log.append(f'template languages: {[str(k) for k in tmpl_strings.keys()]}')
        if not {'en', 'uk'} <= set(keys):
            log.append('STOP: could not tell English and Ukrainian apart in the template keys')
            return
        val_tmpl = tmpl_strings[keys['en']]

        def make_strings(t):
            m = unreal.Map(type(keys['en']), type(val_tmpl))
            m[keys['en']] = same_kind(val_tmpl, t['en'])
            m[keys['uk']] = same_kind(val_tmpl, t['uk'])
            return m
    else:  # array of {language, text} structs
        subs = list(tmpl_strings)
        sub_props = props(subs[0]) if subs else []
        log.append(f'template string items: {len(subs)}, fields {sub_props}')
        lang_f = [n for n, t in sub_props if 'lang' in n.lower() or 'cult' in n.lower()]
        text_f = [n for n, t in sub_props if n not in lang_f]
        if len(lang_f) != 1 or len(text_f) != 1:
            log.append('STOP: unexpected string item layout')
            return
        by_lang = {lang_of(s.get_editor_property(lang_f[0])): s for s in subs}
        if not {'en', 'uk'} <= set(by_lang):
            log.append(f'STOP: template languages {[str(s.get_editor_property(lang_f[0])) for s in subs]}')
            return

        def make_strings(t):
            out = unreal.Array(type(subs[0]))
            for lang in ('en', 'uk'):
                src = by_lang[lang]
                item = type(src)()
                item.set_editor_property(lang_f[0], src.get_editor_property(lang_f[0]))
                item.set_editor_property(text_f[0], same_kind(src.get_editor_property(text_f[0]), t[lang]))
                out.append(item)
            return out

    # ---- fill entries that only hold the editor's placeholder, append the missing ones
    PLACEHOLDER = 'UNLOCALIZED MOD STRING'
    have = {str(el.get_editor_property(sid_field)): i for i, el in enumerate(arr)}
    fill = [k for k in texts if k in have and PLACEHOLDER in str(arr[have[k]].get_editor_property(str_field))]
    todo = [k for k in texts if k not in have]
    keep = sorted(k for k in texts if k in have and k not in fill)
    log.append(f'kept as they are (already have real text): {keep}')
    if not todo and not fill:
        log.append('nothing to add or fill')
        return
    sid_tmpl = template.get_editor_property(sid_field)
    with unreal.ScopedEditorTransaction('AKM-47: add mod texts'):
        for k in fill:
            el = arr[have[k]]
            el.set_editor_property(str_field, make_strings(texts[k]))
            arr[have[k]] = el
        for k in todo:
            el = type(template)()
            el.set_editor_property(sid_field, same_kind(sid_tmpl, k))
            el.set_editor_property(str_field, make_strings(texts[k]))
            arr.append(el)
        asset.set_editor_property(arr_name, arr)
    saved = EAL.save_loaded_asset(asset, only_if_is_dirty=False)
    after = {str(el.get_editor_property(sid_field)): str(el.get_editor_property(str_field))
             for el in asset.get_editor_property(arr_name)}
    still = [k for k in fill + todo if k not in after or PLACEHOLDER in after[k]]
    log.append(f'FILLED {len(fill)}: {fill}')
    log.append(f'ADDED {len(todo)}: {todo}')
    log.append(f'saved: {saved}; still missing/placeholder after save: {still}')
    log.append('Next: Tools -> Refresh Mod TextTool, open the asset and look at one new entry (English + Ukrainian).')


try:
    run()
except Exception:
    import traceback
    log.append('ERROR: ' + traceback.format_exc())
with open(REPORT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log) + '\n')
print('\n'.join(log))
