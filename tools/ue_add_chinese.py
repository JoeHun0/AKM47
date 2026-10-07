"""Add the contributed Simplified Chinese strings to AKM47_Text in Zone Kit.

Select AKM47, then run this file in the editor Python console. Existing languages
are preserved. Re-running is safe. Refresh Mod TextTool and Package Mod afterwards.
"""
import json
from pathlib import Path
import re
import unreal

ROOT = Path(r'C:\Users\KotnyekJM\Documents\stalker 2 mods\AKM47')
REPORT = ROOT / 'tools' / 'ue_add_chinese_report.txt'
ASSET = '/AKM47/AKM47_Text.AKM47_Text'
log = []


def run():
    texts = json.loads((ROOT / 'text' / 'AKM47_zh-Hans.json').read_text(encoding='utf-8'))
    expected = set(re.findall(r'^sid_\w+$', (ROOT / 'text' / 'AKM47_text.txt').read_text(encoding='utf-8'), re.M))
    if set(texts) != expected or not all(isinstance(t, str) and t.strip() for t in texts.values()):
        raise ValueError('Chinese translation must cover exactly the source SIDs with nonempty strings')
    # Resolve by the editor enum name; never assume its numeric value.
    names = [n for n in dir(unreal.LocalizationLanguage) if 'CHINESE' in n.upper()]
    log.append(f'Chinese language enum names: {names}')
    simplified = [n for n in names if 'SIMPL' in n.upper()]
    if len(simplified) != 1:
        raise ValueError(f'Cannot uniquely identify Simplified Chinese: {names}')
    language = getattr(unreal.LocalizationLanguage, simplified[0])
    asset = unreal.EditorAssetLibrary.load_asset(ASSET)
    if asset is None:
        raise RuntimeError('Select the AKM47 mod before running this script: text asset is not mounted')
    entries = asset.get_editor_property('LocalizedTexts')
    index = {str(e.get_editor_property('sid')): i for i, e in enumerate(entries)}
    if len(index) != len(entries) or not set(texts) <= set(index):
        raise ValueError('Text asset has duplicate or missing SIDs; no changes made')
    before = {sid: dict(entries[i].get_editor_property('LanguagesToLocalizedStrings')) for sid, i in index.items()}
    changed = [sid for sid in texts if before[sid].get(language) != texts[sid]]
    if changed:
        with unreal.ScopedEditorTransaction('AKM-47: add Simplified Chinese translation'):
            asset.modify()
            for sid in changed:
                entry = entries[index[sid]]
                strings = entry.get_editor_property('LanguagesToLocalizedStrings')
                strings[language] = texts[sid]
                entry.set_editor_property('LanguagesToLocalizedStrings', strings)
                entries[index[sid]] = entry
            asset.set_editor_property('LocalizedTexts', entries)
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
            raise RuntimeError('Saving the localization asset failed')
    after = {str(e.get_editor_property('sid')): dict(e.get_editor_property('LanguagesToLocalizedStrings'))
             for e in asset.get_editor_property('LocalizedTexts')}
    for sid, values in before.items():
        for lang, value in values.items():
            if sid not in texts or lang != language:
                assert after[sid][lang] == value, f'Existing translation changed: {sid}, {lang}'
    assert all(after[sid][language] == value for sid, value in texts.items())
    log.append(f'SUCCESS: verified all {len(texts)} Chinese translations; updated {len(changed)} entries.')
    log.append('Existing languages preserved. Next: Refresh Mod TextTool, then Package Mod.')


try:
    run()
except Exception:
    import traceback
    log.append('ERROR: ' + traceback.format_exc())
    raise
finally:
    REPORT.write_text('\n'.join(log) + '\n', encoding='utf-8')
    print('\n'.join(log))
