# Building AKM-47

This repository contains the configuration source, localization text, and build/editor scripts. It is not a complete, standalone Zone Kit project. Model assets, textures, extracted game references, and packaged downloads remain outside Git.

## Configuration build

Use Python 3. Supply decoded vanilla game data from your own installation in `tools/` under these names:

- `vanilla_CharacterWeaponSettingsPrototypes.txt`
- `vanilla_ItemGeneratorPrototypes.txt`
- `vanilla_ItemPrototypes.txt`
- `vanilla_NPCPrototypes.txt`
- `vanilla_ObjPrototypes.txt`
- `vanilla_StashPrototypes.txt`
- `vanilla_TradePrototypes.txt`
- `vanilla_UpgradePrototypes.txt`
- `vanilla_WeaponAttributesPrototypes.txt`
- `vanilla_WeaponGeneralSetupPrototypes.txt`

The decoder and config parser are in `tools/cfgbin_decode.py` and `tools/cfgtree.py`. Extracted vanilla files are intentionally ignored by Git.

From the repository root:

```powershell
py tools/make_akm47.py
```

This writes production configs to `zonekit/Content/GameLite/GameData/` and a local `zzz_AKM47_P/` directory. The generator checks expected vanilla values; investigate a failed assertion before adapting it to a newer game version.

```powershell
py tools/make_akm47.py --test
```

The test build goes to `zzz_AKM47_TEST_P/` and increases spawn/loot availability. Do not distribute it as the production mod.

## Full mod and packaging

The complete mod also requires the official Zone Kit, the credited AK-47 model, converted textures and meshes, icons, localization asset, and animation collection edits. See `CREDITS.txt` for attribution and the model source. The Blender and `ue_*.py` scripts record the asset workflow, but several contain author-machine paths; review and adjust those paths before running them. They are not a one-command portable build.

Copy production `zonekit/Content/GameLite` into the AKM47 Zone Kit mod, prepare/import the required assets and English/Ukrainian text, then run **Package Mod** in Zone Kit.

Review `STAGED` and `REPAK` in `tools/make_release.py` for your installation, then run with a new version:

```powershell
py tools/make_release.py <version>
```

The packaging script checks the six staged containers and compares packaged configuration files with production source. It refuses to overwrite an existing release ZIP. Packaged downloads belong in GitHub Releases, outside the source history.

## Repository scope

Included: production configs, Python and shell tools, icon camera settings, localization, README, and credits.

Local only: extracted vanilla data, game/model reference assets, model exports, archives, release packages, debug output, session notes, and test build directories. The root `.gitignore` uses an explicit inclusion list; update it deliberately when adding a new source directory.

This repository does not grant a new blanket license. Existing third-party attribution and license terms remain documented in `CREDITS.txt`.
