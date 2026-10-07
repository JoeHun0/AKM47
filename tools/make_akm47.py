r"""Build the AKM-47 mod: a 7.62x39 AK for Stalker 2, made from the AKM-74S.

The game ships complete 7.62x39 ammo (A762D FMJ, A762A AP, A762E hollow-point), a 7.62x39 bullet
(P762) and caliber sound, but no gun uses them and nothing spawns the ammo. This mod adds:
  - GunAKM47_ST: the AKM-74S model, magazines and upgrades, firing 7.62x39 - hits harder,
    pierces more armor, kicks more, shorter range, a bit less accurate, jams less;
  - its own weapon setup, player/NPC attributes and damage settings (all fields written out
    explicitly, flattened from vanilla, so nothing depends on runtime refkey inheritance);
  - 7.62x39 cheaper (74 -> 30 per FMJ round) and listed as fitting the AKM-47;
  - NPCs: the AKM-47 joins the gun pool of eastern-faction stormtroopers, Experienced and up
    (appended to the vanilla lists, nothing replaced);
  - traders: 7.62x39 where 5.45x39 of the same kind is sold, the gun wherever the AKM-74S is sold (same chance, sold empty);
  - world stashes, ammo crates, caches: 7.62x39 next to 5.45x39 (FMJ low tier, AP/hollow-point rare);
  - "smart" ammo of bodies (easier difficulties) and stashes also knows 7.62x39.
Name and description come from Zone Kit mod text (sid_items_GunAKM47_ST_name/_description).

Inputs (next to this script): decoded vanilla data vanilla_*.txt, cfgtree.py.
Usage:  py tools\make_akm47.py   -> writes the same files to
   zzz_AKM47_P\Stalker2\Content\GameLite\GameData\...   (~mods pak, for quick tests: no item name)
   zonekit\Content\GameLite\GameData\...                (Zone Kit mod, with the text asset)
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cfgtree import parse, Node

GUN = 'GunAKM47_ST'
BASE = 'GunAK74_ST'
MAG, MAG_BASE = 'GunAKM47_MagDefault', 'GunAK74_MagDefault'
DISABLED_ATTACH = {'GunAK74_MagIncreased', 'GunAK_MagPaired'}   # 5.45x39 magazines; 7.62x39 versions maybe later
GDS = [os.path.join(ROOT, 'zzz_AKM47_P', 'Stalker2', 'Content', 'GameLite', 'GameData'),
       os.path.join(ROOT, 'zonekit', 'Content', 'GameLite', 'GameData')]
HEAD = ['// AKM-47 by JoeHun0 - a 7.62x39 AK made from the AKM-74S (model, magazines, upgrades)']

# ---------------------------------------------------------------- balance (vanilla AKM-74S -> AKM-47)
ITEM = {'Cost': ('10000.0', '12000.0'), 'Weight': ('3.3', '3.6'), 'BaseDurability': ('1950.0', '2100.0')}
SETUP = {  # path in the weapon setup: (vanilla, new)
    'AmmoCaliber': ('EAmmoCaliber::A545', 'EAmmoCaliber::A762'),
    'RecoilParams.RecoilRadius': ('270.0', '340.0'),                       # ~25% more kick
    'DispersionParams.FirstShotDispersionRadius': ('148.0', '160.0'),
    'WeaponJamParams.[0].JamChanceCoef': ('1.7', '1.2'),                   # the old AK just works
    'WeaponJamParams.[1].JamChanceCoef': ('1.7', '1.2'),
    'WeaponJamParams.[2].JamChanceCoef': ('1.7', '1.2'),
}
PLAYER = {
    'BaseDamage': ('23.0', '30.0'), 'ArmorPiercing': ('1.0', '1.8'),
    'EffectiveFireDistanceMin': ('3000.0', '2500.0'), 'EffectiveFireDistanceMax': ('3000.0', '2500.0'),
    'FireDistanceDropOff': ('2000.0', '1700.0'), 'DispersionRadius': ('148.0', '160.0'),
    'DurabilityDamagePerShot': ('1.2', '1.35'),
    'AccuracyUI': ('0.6', '0.55'), 'HandlingUI': ('0.43', '0.4'), 'DamageUI': ('0.23', '0.3'), 'RangeUI': ('0.38', '0.33'),
}
NPC = {'BaseDamage': ('9.5', '12.0'), 'ArmorPiercing': ('1.0', '1.8'), 'DispersionRadius': ('300.0', '320.0')}
AMMO_COST = {'A762D': ('74.0', '30.0'), 'A762A': ('148.0', '46.0'), 'A762E': ('148.0', '46.0')}
AMMO_PACK = ('50', '30')   # rounds per pack/box, like 5.45x39 (user, 2026-10-05)

# NPCs: eastern factions' stormtroopers; chance per story rank of carrying an AKM-47
FACTIONS = ['Bandit', 'Neutral', 'Duty', 'Militaries', 'Monolith', 'Noon', 'Spark', 'Varta', 'Corpus']
NPC_CHANCE = {'Experienced': 0.10, 'Veteran': 0.15, 'Master': 0.08}
ROLES = ['Stormtrooper']

# TEST build (--test): every role of those factions, every rank, 50% - half the generic NPCs should
# carry the AKM-47, the other half their usual guns; stash 7.62x39 weights x20 (LOOT_WEIGHT_X).
# Writes zzz_AKM47_TEST_P only. Not for release.
TEST = '--test' in sys.argv
if TEST:
    ROLES = ['CloseCombat', 'Recon', 'Stormtrooper', 'Heavy', 'Sniper']
    NPC_CHANCE = {'Newbie': 0.5, 'Experienced': 0.5, 'Veteran': 0.5, 'Master': 0.5}
    GDS = [os.path.join(ROOT, 'zzz_AKM47_TEST_P', 'Stalker2', 'Content', 'GameLite', 'GameData')]
    HEAD = ['// !!! AKM-47 TEST BUILD - all roles of the eastern factions, every rank, 50%; stash 7.62x39 x20. NOT FOR RELEASE !!!'] + HEAD

# traders: every 5.45x39 item in every trade list traders actually use gets a 7.62x39 twin with exactly the same
# chance and counts (user, 2026-10-05: "exactly the same way (number/rarity) as other machine gun ammo").
# Before: only T1/Soviet/T3/T4 at 0.6x the count.
TRADE_AMMO_TWIN = {'A545D': 'A762D', 'A545A': 'A762A', 'A545E': 'A762E'}
# not in the game world (checked in vanilla SpawnActorPrototypes 2026-10-05): dev trader AllTraderNPC (900 of every
# ammo, 5 of every gun; never spawned), TradeTest (no NPC uses it), RC_TraderNPC (spawned only on AITestMap)
TRADE_SKIP = {'AllAmmosGenerator', 'AllPrimaryWeaponsGenerator', 'TraderPrimaryWeaponGenerator', 'RC_TraderNPC_ItemGenerator'}
# the gun: sold exactly where and how the AKM-74S is (user, 2026-10-05: "should be same way as AKM-74S") - a twin
# of every BASE entry in the live trade lists (T1 gun list: Sidorovich, Chemical Plant, Asylum, Sultansk,
# Shevchenko, Rostok bartenders, Eger). Before: T2 gun list at 0.5.
# traders with their own fixed gun list: (list, entry, chance). User 2026-10-05: Guron (Slag Heap,
# Garbage) always has one - his stock is M860, AKM-74U, Boomstick, Three-Line Rifle, all 100%.
OWN_GUN_LISTS = [('TraderTerikon_TradeItemGenerator', '[1]', '1')]
if TEST:   # so a new game has one right away: Hamster (Zalissya) always sells it too (test builds only)
    OWN_GUN_LISTS = OWN_GUN_LISTS + [('TraderZalesie_TradeItemGenerator', '[1]', '1')]
SMART_SCALE = 0.7                                     # corpse smart loot: 7.62x39 count vs 5.45x39

strip = lambda v: re.sub(r'\s*\{.*$', '', v or '').strip()
def load(name):
    return {n.key: n for n in parse(os.path.join(HERE, f'vanilla_{name}.txt')).children}
def rnd10(x):
    return max(10, int(round(x / 10.0)) * 10)

# ---------------------------------------------------------------- flatten a vanilla entry into our own
ARRAY = re.compile(r'^\[\d+\]$')
def clean(n, top=False):
    """Copy a decoded (already flattened) entry: drop decoder notes, mark arrays {bskipref}
    so the parent's lists are replaced, not merged."""
    c = Node(n.key, n.value)
    if n.is_struct:
        c.children = [clean(k) for k in n.children]
        if c.children and all(ARRAY.match(k.key) for k in c.children) and not top:
            c.header_extra = ' {bskipref}'
    return c

def at(node, path):
    for p in path.split('.'):
        node = node.get(p)
        assert node is not None, path
    return node

def setv(entry, path, old, new):
    *parent, key = path.split('.')
    holder = at(entry, '.'.join(parent)) if parent else entry
    cur = holder.get(key)
    assert cur is not None and strip(cur.value) == old, f'{entry.key}.{path}: vanilla {cur.value if cur else None!r}, expected {old!r}'
    cur.value = new

def own(vanilla, sid, refurl, header_sid=None):
    e = clean(vanilla, top=True)
    e.key = sid
    e.header_extra = f' {{refurl={refurl};refkey={header_sid or vanilla.key}}}'
    setv(e, 'SID', vanilla.key, sid)
    return e

def replace_all(node, old, new):
    n = 0
    for c in node.children:
        if c.is_struct:
            n += replace_all(c, old, new)
        elif strip(c.value) == old:
            c.value, n = new, n + 1
    return n

# ---------------------------------------------------------------- item
items = load('ItemPrototypes')
for a in ('A762D', 'A762A', 'A762E'):
    assert strip(items[a].val('Caliber')) == 'EAmmoCaliber::A762', a
item = own(items[BASE], GUN, 'WeaponPrototypes.cfg')
item.children.insert(1, Node('LocalizationSID', GUN))
for k, (o, n) in ITEM.items():
    setv(item, k, o, n)
setv(item, 'GeneralWeaponSetup', BASE, GUN)
setv(item, 'PlayerWeaponAttributes', BASE + '_Player', GUN + '_Player')
setv(item, 'NPCWeaponAttributes', BASE + '_NPC', GUN + '_NPC')

ammo_lines = ['', '// 7.62x39: cheaper (vanilla priced it like a rare caliber), packs of 30 like 5.45x39, listed as fitting the AKM-47']
for a, (o, n) in AMMO_COST.items():
    assert strip(items[a].val('Cost')) == o, a
    assert not (items[a].get('FittingWeaponsSIDs') and items[a].get('FittingWeaponsSIDs').children), a
    assert strip(items[a].val('AmmoPackCount')) == AMMO_PACK[0], a
    ammo_lines += [f'{a} : struct.begin {{bpatch}}', f'   Cost = {n}', f'   AmmoPackCount = {AMMO_PACK[1]}',
                   '   FittingWeaponsSIDs : struct.begin', f'      [0] = {GUN}', '   struct.end', 'struct.end']

# ---------------------------------------------------------------- weapon setup
gs_all = load('WeaponGeneralSetupPrototypes')
gs = own(gs_all[BASE], GUN, '../WeaponGeneralSetupPrototypes.cfg')
for k, (o, n) in SETUP.items():
    setv(gs, k, o, n)
atp = at(gs, 'AmmoTypeProjectiles')
assert [strip(c.val('ProjectilePrototypeSID')) for c in atp.children] == ['P545'] * 3
assert [strip(c.val('AmmoType')) for c in atp.children] == ['EAmmoType::Default', 'EAmmoType::ArmorPiercing', 'EAmmoType::Expanding']
for c in atp.children:
    setv(c, 'ProjectilePrototypeSID', 'P545', 'P762')

# ---------------------------------------------------------------- upgrade tree (user OK 2026-10-05)
# Own tree instead of the AKM-74S one: ideas from real 7.62x39 AKs (AKM stamped receiver + hammer rate reducer,
# chrome-lined bore, RPK heavy barrel, AKMS under-folder, laminated stock, AK-15 grip/safety) and common gunsmith
# work. Only vanilla effects at vanilla sizes. Layout like the vanilla trees: H = column 0-2, Top/Down = row; a pair
# in one column blocks each other; the next column requires either of them. Prices ~1.5x the AKM-74S tree.
# Text: reuses a vanilla upgrade's name+description where they fit (en/uk come with the game), else our own
# sid_upgrades_GunAKM47_Upgrade_<key>_name/_description (mod text). Pictures: vanilla AK-family upgrade pictures.
UP = 'GunAKM47_Upgrade_'
UPGRADES = [  # key, part, column, row, cost, effects, requires, blocks, text from (vanilla upgrade) or None, picture from
    ('Barrel_1', 'Barrel', 0, 'Top', 500, ['DurabilityPerShotPos15Effect'], [], [], 'GunFora_Upgrade_Barrel_1', 'GunAK74_Upgrade_Barrel_1'),
    ('Barrel_2_1', 'Barrel', 1, 'Top', 1300, ['FireDistancePos15Effect', 'BulletFalloffPos10Effect'], ['Barrel_1'], ['Barrel_2_2'], None, 'GunAK74_Upgrade_Barrel_2_2'),
    ('Barrel_2_2', 'Barrel', 1, 'Down', 1200, ['ShotRecoveryPos10Effect'], ['Barrel_1'], ['Barrel_2_1'], None, 'GunDnipro_Upgrade_Barrel_1_2'),
    ('Barrel_3', 'Barrel', 2, 'Top', 2500, ['ArmorPiercingPos15Effect', 'CoverPiercingPos15Effect'], ['Barrel_2_1', 'Barrel_2_2'], [], 'GunBucket_Upgrade_Barrel_3', 'GunAK74_Upgrade_Barrel_2_1'),
    ('Handguard_1_1', 'Handguard', 0, 'Top', 500, ['MaxDispersionPos15Effect'], [], ['Handguard_1_2'], 'GunZubr_Upgrade_Barrel_2_2', 'GunAKU_Upgrade_Handguard_1_1'),
    ('Handguard_1_2', 'Handguard', 0, 'Down', 450, ['AimingTimePos10Effect'], [], ['Handguard_1_1'], 'GunIntegral_Upgrade_Body_2_2', 'GunAKU_Upgrade_Handguard_1_2'),
    ('Handguard_2', 'Handguard', 1, 'Top', 1200, ['RecoilPos10Effect'], ['Handguard_1_1', 'Handguard_1_2'], [], 'GunZubr_Upgrade_Handguard_1', 'GunAKU_Upgrade_Handguard_2_1'),
    ('Body_1', 'Body', 0, 'Top', 450, ['WeightPos20Effect'], [], [], 'GunSPSA_Upgrade_Body_2_2', 'GunAK74_Upgrade_Body_1'),
    ('Body_2_1', 'Body', 1, 'Top', 1500, ['DispersionIncreaseSpeedPos50Effect', 'RecoilPos5Effect'], ['Body_1'], ['Body_2_2'], None, 'GunAKU_Upgrade_Body_2_1'),
    ('Body_2_2', 'Body', 1, 'Down', 1200, ['DurabilityPos20Effect'], ['Body_1'], ['Body_2_1'], 'GunM701_Upgrade_Body_2_1', 'GunAKU_Upgrade_Body_2_2'),
    ('Body_3_1', 'Body', 2, 'Top', 2200, ['ShotRecoveryPos15Effect'], ['Body_2_1', 'Body_2_2'], ['Body_3_2'], None, 'GunDnipro_Upgrade_Body_1'),
    ('Body_3_2', 'Body', 2, 'Down', 2200, ['BulletFalloffPos15Effect'], ['Body_2_1', 'Body_2_2'], ['Body_3_1'], 'GunAK74_Upgrade_Body_2', 'GunAK74_Upgrade_Body_2'),
    ('Grip_1', 'PistolGrip', 0, 'Top', 450, ['AimingMovementPos15Effect'], [], [], 'GunViper_Upgrade_Body_2', 'GunGrim_Upgrade_Grip_1'),
    ('Grip_2', 'PistolGrip', 1, 'Top', 1100, ['WeaponWithdrawPos15ShowEffect', 'WeaponWithdrawPos15HideEffect'], ['Grip_1'], [], None, 'GunGrim_Upgrade_Grip_2_1'),
    ('Stock_1', 'Stock', 0, 'Top', 400, ['RecoilPos10Effect'], [], [], 'GunAK74_Upgrade_Stock_3', 'GunAK74_Upgrade_Stock_1'),
    ('Stock_2_1', 'Stock', 1, 'Top', 1200, ['IdleSwayXPos15Effect', 'IdleSwayYPos15Effect'], ['Stock_1'], ['Stock_2_2'], None, 'GunAK74_Upgrade_Stock_2'),
    ('Stock_2_2', 'Stock', 1, 'Down', 1100, ['AimingTimePos10Effect', 'WeightPos10Effect'], ['Stock_1'], ['Stock_2_1'], None, 'GunAKU_Upgrade_Stock_1_1'),
    ('Stock_3', 'Stock', 2, 'Top', 2000, ['HoldBreathPos75Effect'], ['Stock_2_1', 'Stock_2_2'], [], 'GunM16_Upgrade_Stock_1', 'GunAK74_Upgrade_Stock_3'),
]
UPGRADES_KEEP = ['GunAK74_Upgrade_Attachment_SinMuz', 'GunAK74_Upgrade_Attachment_Offset_Stock']  # vanilla add-ons
ups_all = load('UpgradePrototypes')
up_arr = lambda n, k: [strip(c.value) for c in n.get(k).children] if n.get(k) and n.get(k).is_struct else []
effect_kind = lambda e: re.sub(r'(Pos|Neg)\d+.*$', '', e)
icon_of = {}                       # effect kind -> the icon vanilla uses most for it (first effect of an upgrade)
for n in ups_all.values():
    eff = up_arr(n, 'EffectPrototypeSIDs')
    if eff and n.key.startswith('Gun') and n.val('Icon'):
        icon_of.setdefault(effect_kind(eff[0]), {}).setdefault(strip(n.val('Icon')), 0)
        icon_of[effect_kind(eff[0])][strip(n.val('Icon'))] += 1
known_effects = {strip(c.value) for n in ups_all.values() for c in (n.get('EffectPrototypeSIDs').children
                 if n.get('EffectPrototypeSIDs') and n.get('EffectPrototypeSIDs').is_struct else [])}
upg_lines, upg_new_text = [], []
for key, part, col, row, cost, eff, req, blk, text_from, pic_from in UPGRADES:
    assert all(e in known_effects for e in eff), (key, eff)
    pic = ups_all[pic_from]
    assert strip(pic.val('UpgradeTargetPart')) and pic.val('Image'), pic_from
    icons = icon_of[effect_kind(eff[0])]
    if text_from:
        assert text_from in ups_all and not text_from.startswith(UP), text_from
        name, hint = f'sid_upgrades_{text_from}_name', f'sid_upgrades_{text_from}_description'
    else:
        name, hint = f'sid_upgrades_{UP}{key}_name', f'sid_upgrades_{UP}{key}_description'
        upg_new_text.append(key)
    arrs = lambda k, vals: [f'   {k} : struct.begin'] + [f'      [{i}] = {v}' for i, v in enumerate(vals)] + ['   struct.end'] if vals else [f'   {k} = ']
    upg_lines += [f'{UP}{key} : struct.begin {{refurl=../UpgradePrototypes.cfg;refkey=[0]}}', f'   SID = {UP}{key}',
                  f'   Text = {name}', f'   Hint = {hint}', f'   Image = {strip(pic.val("Image"))}',
                  f'   Icon = {max(icons, key=icons.get)}', f'   BaseCost = {cost}', f'   HorizontalPosition = {col}',
                  f'   VerticalPosition = EUpgradeVerticalPosition::{row}', f'   UpgradeTargetPart = EUpgradeTargetPartType::{part}']
    upg_lines += arrs('EffectPrototypeSIDs', eff) + arrs('RequiredUpgradePrototypeSIDs', [UP + r for r in req])
    upg_lines += arrs('BlockingUpgradePrototypeSIDs', [UP + b for b in blk])
    # line to the previous column, as vanilla draws it: first column none, upper node down, lower node up
    upg_lines += arrs('ConnectionLines', ['EConnectionLineState::' + ('None' if col == 0 else 'Down' if row == 'Top' else 'Top')])
    upg_lines += ['   ID = 0', '   DiscountCoefficient = 0.f', '   RepairCostModifier = 0.2f', '   IsModification = false',
                  '   HiddenWihoutItem = false', '   AttachPrototypeSIDs = ', "   UpgradeSound = AkAudioEvent''",
                  "   UpgradeModificationSound = AkAudioEvent''", "   UpgradeCancelSound = AkAudioEvent''",
                  '   RequiredItemPrototypeSIDs = ', '   InterchangeableUpgradePrototypeSIDs = ', '   RequiredGlobalVariables = ',
                  '   BlockingGlobalVariables = ', '   Skills = ', 'struct.end']
    for r in req + blk:
        assert r in [u[0] for u in UPGRADES], (key, r)
# the upgrade screen needs the handguard and pistol grip sections (the AKM-74S has them, switched off)
for c in at(item, 'SectionSettings').children:
    if strip(c.val('UpgradeTargetPartType')).split('::')[-1] in ('Handguard', 'PistolGrip'):
        setv(c, 'SectionIsEnabled', 'false', 'true')
# technicians: each one has a list of the upgrades he may install (NPCPrototypes `Upgrades`, refkey copies baked),
# some get more through quest steps (AddTechnicianSkillOrUpgrade `UpgradeSIDs`). In game 2026-10-05 Diode refused
# all our upgrades ("The technician can't upgrade this item") while the vanilla flash suppressor worked. Every list
# that has the AKM-74S upgrades gets ours too (22 NPC lists - every real technician has the full AKM-74S set).
npcs = load('NPCPrototypes')
our_upg = [UP + u[0] for u in UPGRADES]
tech_lines = []
for n in npcs.values():
    ul = n.get('Upgrades')
    if not ul or not ul.is_struct:
        continue
    sids = [strip(c.val('UpgradePrototypeSID')) for c in ul.children if c.is_struct]
    if 'GunAK74_Upgrade_Barrel_1' not in sids:
        continue
    assert not set(our_upg) & set(sids), n.key
    tech_lines += [f'{n.key} : struct.begin {{bpatch}}', '   Upgrades : struct.begin {bpatch}']
    for s in our_upg:
        tech_lines += ['      [*] : struct.begin', f'         UpgradePrototypeSID = {s}', '         Enabled = true', '      struct.end']
    tech_lines += ['   struct.end', 'struct.end']
n_tech = tech_lines.count('   Upgrades : struct.begin {bpatch}')
assert n_tech >= 20, n_tech
# quest steps that add the AKM-74S upgrades to a technician (Kazkovy hub, Banzai; read from decoded vanilla
# QuestNodePrototypes 2026-10-05). Scalar-array append `[*] = value` - not yet confirmed in game.
TECH_QUEST_NODES = ['Kazkovy_Hub_AddTechnicianSkillOrUpgrade_BP_NPC_Banzai', 'Kazkovy_Hub_AddTechnicianSkillOrUpgrade_3Box',
                    'Kazkovy_Hub_AddTechnicianSkillOrUpgrade_2Box', 'Kazkovy_Hub_AddTechnicianSkillOrUpgrade_2Box_1']
quest_tech_lines = []
for q in TECH_QUEST_NODES:
    quest_tech_lines += [f'{q} : struct.begin {{bpatch}}', '   UpgradeSIDs : struct.begin {bpatch}']
    quest_tech_lines += [f'      [*] = {s}' for s in our_upg] + ['   struct.end', 'struct.end']
up_list = at(gs, 'UpgradePrototypeSIDs')
assert [strip(c.value) for c in up_list.children][:1] == ['GunAK74_Upgrade_Attachment_SinMuz'] and len(up_list.children) == 10
up_list.children = [Node(f'[{i}]', sid) for i, sid in enumerate(UPGRADES_KEEP + [UP + u[0] for u in UPGRADES])]

# ---------------------------------------------------------------- attributes and damage settings
attr = load('WeaponAttributesPrototypes')
pa = own(attr[BASE + '_Player'], GUN + '_Player', 'PlayerWeaponAttributesPrototypes.cfg')
assert replace_all(pa, BASE + '_Player', GUN + '_Player') == 1           # DefaultWeaponSettingsSID
na = own(attr[BASE + '_NPC'], GUN + '_NPC', 'NPCWeaponAttributesPrototypes.cfg')
assert replace_all(na, BASE + '_NPC', GUN + '_NPC') == 5                  # CharacterWeaponSettingsSID per rank
assert replace_all(na, BASE + '_Player', GUN + '_Player') == 1

sets = load('CharacterWeaponSettingsPrototypes')
ps = own(sets[BASE + '_Player'], GUN + '_Player', 'PlayerWeaponSettingsPrototypes.cfg')
for k, (o, n) in PLAYER.items():
    setv(ps, k, o, n)
ns = own(sets[BASE + '_NPC'], GUN + '_NPC', 'NPCWeaponSettingsPrototypes.cfg')
for k, (o, n) in NPC.items():
    setv(ns, k, o, n)

# ---------------------------------------------------------------- NPC loadouts
# The AKM-47 joins the GUN POOL of the generic eastern-faction loadouts (user 2026-10-05: patch the loadouts,
# don't replace them - fewer conflicts): every WeaponPrimary entry of a rank in NPC_CHANCE gets the AKM-47
# appended to its PossibleItems ({bpatch} [n] {bpatch} PossibleItems {bpatch} [*], the pattern that works for
# trader lists). The pick inside an entry is by Weight, so the weight is set to give NPC_CHANCE of that rank:
# w = p * (sum of the entry's vanilla weights) / (1 - p). Durability/ammo copied from the entry's first gun.
# (Earlier, appending a whole new WeaponPrimary entry never showed up; the ObjPrototypes wrapper that replaced
# whole loadouts worked (TEST_5) but clashes with other NPC mods - removed.)
gen = {n.val('SID'): n for n in parse(os.path.join(HERE, 'vanilla_ItemGeneratorPrototypes.txt')).children if n.val('SID')}
category = lambda e: strip(e.val('Category')).split('::')[-1]
objs = {n.key: n for n in parse(os.path.join(HERE, 'vanilla_ObjPrototypes.txt')).children}
targets = [f'GeneralNPC_{f}_{r}_ItemGenerator' for f in FACTIONS for r in ROLES
           if f'GeneralNPC_{f}_{r}_ItemGenerator' in gen]
# only loadouts that generic characters (GeneralNPCObjPrototypes.cfg) use; quest characters get their gear from quests
used = {strip(o.val('ItemGeneratorPrototypeSID')) for k, o in objs.items()
        if k.startswith('GeneralNPC_') and 'GeneralNPCObjPrototypes.cfg' in o.header_extra}
targets = [t for t in targets if t in used]
npc_pool = {}
for t in targets:
    for e in gen[t].get('ItemGenerator').children:
        if not e.is_struct or category(e) != 'WeaponPrimary':
            continue
        rank = strip(e.val('PlayerRank')).split('::')[-1]
        p = NPC_CHANCE.get(rank, 0)
        if not p:
            continue
        pool = e.get('PossibleItems').children
        assert pool and all(i.val('Weight') for i in pool), (t, e.key)
        assert GUN not in [strip(i.val('ItemPrototypeSID')) for i in pool], (t, e.key)
        total = sum(float(strip(i.val('Weight'))) for i in pool)
        w = max(1, round(p * total / (1 - p)))
        first = pool[0]
        npc_pool.setdefault((t, e.key), []).append([('ItemPrototypeSID', GUN), ('Weight', str(w))]
            + [(k, strip(first.val(k))) for k in ('MinDurability', 'MaxDurability', 'AmmoMinCount', 'AmmoMaxCount') if first.val(k)])
assert npc_pool, 'no NPC pool found'

def append_lines(patches):
    """{(generator, entry key): [item fields...]} -> {bpatch} appends to each entry's PossibleItems."""
    out = []
    for (lst, key), adds in patches.items():
        out += [f'{lst} : struct.begin {{bpatch}}', '   ItemGenerator : struct.begin {bpatch}',
                f'      {key} : struct.begin {{bpatch}}', '         PossibleItems : struct.begin {bpatch}']
        for kv in adds:
            out.append('            [*] : struct.begin')
            out += [f'               {k} = {v}' for k, v in kv]
            out.append('            struct.end')
        out += ['         struct.end', '      struct.end', '   struct.end', 'struct.end']
    return out
npc_lines = append_lines(npc_pool)

# ---------------------------------------------------------------- traders
def first_entry(sid, cat):
    e = gen[sid].get('ItemGenerator').children[0]
    assert e.key == '[0]' and category(e) == cat and strip(e.val('bAllowSameCategoryGeneration')) == 'true', sid
    return e
trade = {}
# lists traders use: named in TradePrototypes, plus everything those reach through SubItemGenerator entries
def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)
trade_used, todo = set(), [strip(n.value) for n in walk(parse(os.path.join(HERE, 'vanilla_TradePrototypes.txt')))
                           if n.key == 'ItemGeneratorPrototypeSID' and not n.is_struct]
while todo:
    sid = todo.pop()
    if sid in trade_used or sid not in gen or sid in TRADE_SKIP:
        continue
    trade_used.add(sid)
    todo += [strip(n.value) for n in walk(gen[sid]) if n.key == 'ItemGeneratorPrototypeSID' and not n.is_struct]
for lst in sorted(trade_used):
    for e in gen[lst].get('ItemGenerator').children:
        if not e.is_struct or category(e) != 'Ammo':
            continue
        pool = e.get('PossibleItems').children
        have = [strip(i.val('ItemPrototypeSID')) for i in pool]
        for i in pool:
            ours = TRADE_AMMO_TWIN.get(strip(i.val('ItemPrototypeSID')))
            if not ours:
                continue
            assert not set(have) & set(TRADE_AMMO_TWIN.values()), (lst, e.key, have)
            trade.setdefault((lst, e.key), []).append([('ItemPrototypeSID', ours)]
                + [(c.key, strip(c.value)) for c in i.children if not c.is_struct and c.key != 'ItemPrototypeSID'])
assert len(trade) >= 6, trade.keys()
# bUnloadedWeapon: traders sell it empty, like vanilla's own use for Skif's pistol (user, 2026-10-05:
# it came with a full 7.62x39 magazine, which also raised the price)
n_gun = 0
for lst in sorted(trade_used):
    for e in gen[lst].get('ItemGenerator').children:
        pool = e.get('PossibleItems').children if e.is_struct and e.get('PossibleItems') else []
        have = [strip(i.val('ItemPrototypeSID')) for i in pool]
        assert GUN not in have, (lst, e.key)
        for i in pool:
            if strip(i.val('ItemPrototypeSID')) != BASE:
                continue
            n_gun += 1
            trade.setdefault((lst, e.key), []).append([('ItemPrototypeSID', GUN)]
                + [(c.key, strip(c.value)) for c in i.children
                   if not c.is_struct and c.key not in ('ItemPrototypeSID', 'bUnloadedWeapon')]
                + [('bUnloadedWeapon', 'true')])
assert ('Trader_T1_Guns_ItemGenerator', '[0]') in trade and n_gun >= 1, n_gun
for lst, key, ch in OWN_GUN_LISTS:
    e = gen[lst].get('ItemGenerator').get(key)
    assert e is not None and category(e) == 'WeaponPrimary' and strip(e.val('bAllowSameCategoryGeneration')) == 'true', lst
    assert GUN not in [strip(i.val('ItemPrototypeSID')) for i in e.get('PossibleItems').children], lst
    trade.setdefault((lst, key), []).append([('ItemPrototypeSID', GUN), ('Chance', ch), ('MinDurability', '1'),
                                             ('MaxDurability', '1'), ('bUnloadedWeapon', 'true')])
test_gen_lines = []
if TEST:
    # TEST: Guron (Slag Heap, Garbage) sells every attachment the AKM-74S takes (user, 2026-10-05) plus VOG grenades;
    # the disabled 5.45 magazines too, to see that they no longer fit. Own list, hooked into his sub-list entry [0]
    # (append to an existing entry). No spare standard magazine: like vanilla default mags it has no inventory picture
    # (showed as a blank slot in game).
    TEST_GEN = 'AKM47_TEST_Attachments_ItemGenerator'
    att = [strip(c.val('AttachPrototypeSID')) for c in at(gs_all[BASE], 'CompatibleAttachments').children]
    att = [a for a in att if a not in ('AK74_DefaultMuz', MAG_BASE)]
    assert set(DISABLED_ATTACH) <= set(att), att
    test_gen_lines = [f'{TEST_GEN} : struct.begin {{refurl=../ItemGeneratorPrototypes.cfg;refkey=[0]}}', f'   SID = {TEST_GEN}',
                      '   ItemGenerator : struct.begin']
    for i, (cat, its) in enumerate((('Attach', [(a, 2 if a == MAG else 1) for a in att]), ('Ammo', [('AVOG', 10)]))):
        test_gen_lines += [f'      [{i}] : struct.begin', f'         Category = EItemGenerationCategory::{cat}',
                           '         PlayerRank = ERank::Newbie, ERank::Experienced, ERank::Veteran, ERank::Master',
                           '         bAllowSameCategoryGeneration = true', '         PossibleItems : struct.begin']
        for j, (sid, n) in enumerate(its):
            test_gen_lines += [f'            [{j}] : struct.begin', f'               ItemPrototypeSID = {sid}', '               Chance = 1',
                               f'               MinCount = {n}', f'               MaxCount = {n}', '            struct.end']
        test_gen_lines += ['         struct.end', '      struct.end']
    test_gen_lines += ['   struct.end', 'struct.end', '']
    e = gen['TraderTerikon_TradeItemGenerator'].get('ItemGenerator').get('[0]')
    assert category(e) == 'SubItemGenerator', e
    trade.setdefault(('TraderTerikon_TradeItemGenerator', '[0]'), []).append([('ItemGeneratorPrototypeSID', TEST_GEN), ('Chance', '1')])
trade_lines = test_gen_lines + append_lines(trade)

# ---------------------------------------------------------------- world stashes and ammo crates
# 7.62x39 joins every random-loot ammo entry that has 5.45x39 (user, 2026-10-05: "regular in some low tier while
# specials higher tier"): FMJ next to 5.45 FMJ (medium stashes, Soviet ammo crates, caches), AP next to 5.45 AP
# (rare stashes, caches), hollow-point added to the rare Veteran/Master entries. Same weight as the 5.45 item,
# counts x LOOT_SCALE. Stash_Medium/Expensive_<Rank> are refkey copies of the tiers, baked at build time, so they
# get the same patch (patching the parent alone leaves copies unchanged - confirmed in game for loadouts).
LOOT_SCALE = 0.7
RANKS = ['Newbie', 'Experienced', 'Veteran', 'Master']
LOOT_LOW = (['GamePass_Stash_ItemGenerator_Common_Var1'] + [f'Stash_Medium_{r}' for r in RANKS]
            + [f'GamePass_Stash_ItemGenerator_PrimaryAmmo_{t}' for t in ('Cheap', 'Common', 'Rare')]
            + ['DestructibleStash_AmmoSNG', 'CommonCacheAmmoGenerator'])
LOOT_RARE = ['GamePass_Stash_ItemGenerator_Rare', 'CNPPGamePass_Stash_ItemGenerator_Rare'] + [f'Stash_Expensive_{r}' for r in RANKS]
LOOT_RULES = [(LOOT_LOW, 'A545D', 'A762D', None, None),            # (lists, like, ours, only ranks, weight)
              (LOOT_RARE + ['CommonCacheAmmoGenerator'], 'A545A', 'A762A', None, None),
              (LOOT_RARE, 'A545A', 'A762E', ('Veteran', 'Master'), '1')]
LOOT_WEIGHT_X = 20 if TEST else 1        # TEST: 7.62x39 in nearly every stash that rolls rifle ammo
scaled = lambda item, k, f: str(max(1, round(int(strip(item.val(k))) * f)))
loot = {}
for lists, like, ours, ranks, wt in LOOT_RULES:
    for lst in lists:
        hits = 0
        for e in gen[lst].get('ItemGenerator').children:
            if not e.is_struct or category(e) != 'Ammo':
                continue
            if ranks and strip(e.val('PlayerRank')).split('::')[-1] not in ranks:
                continue
            pool = e.get('PossibleItems').children
            src = [i for i in pool if strip(i.val('ItemPrototypeSID')) == like]
            if not src:
                continue
            assert len(src) == 1, (lst, e.key)
            assert ours not in [strip(i.val('ItemPrototypeSID')) for i in pool], (lst, e.key)
            s, hits = src[0], hits + 1
            w = float(wt or strip(s.val('Weight'))) * LOOT_WEIGHT_X
            loot.setdefault((lst, e.key), []).append([('ItemPrototypeSID', ours), ('Weight', f'{w:g}')]
                + [(k, scaled(s, k, LOOT_SCALE)) for k in ('MinCount', 'MaxCount')])
        assert hits, (lst, like)
loot_lines = append_lines(loot)

# ---------------------------------------------------------------- "smart" ammo: bodies and stashes
# NPC_Ammo_Smart = bodies (easier difficulties); Stash_Ammo_Smart_* = the smart part of world stashes (ammo for
# the guns you carry). Ranks that already have a 7.62x39 (EAmmoCaliber::A762) entry hand out 7.62x54R in vanilla
# (A762SniperD 2-3 times, meant as FMJ/AP/HP) - never mattered with no 7.62x39 gun; fixed to A762D/A/E. Ranks
# without one get a copy of their 5.45x39 entry (A545x -> A762x, counts x SMART_SCALE).
stash = load('StashPrototypes')
SMART = ['NPC_Ammo_Smart', 'Stash_Ammo_Smart_Cheap', 'Stash_Ammo_Smart_CommonRare']
smart_lines, smart_report = [], []
for sp in SMART:
    smart_lines += [f'{sp} : struct.begin {{bpatch}}', '   ItemGenerators : struct.begin {bpatch}']
    for r in stash[sp].get('ItemGenerators').children:
        slp = r.get('SmartLootParams')
        pw = slp.get('PrimaryWeaponParams') if slp else None
        cals = {strip(p.val('PriorityCaliber')): p for p in (pw.children if pw else [])}
        rank = strip(r.val('Rank')).split('::')[-1]
        head = [f'      {r.key} : struct.begin {{bpatch}}', '         SmartLootParams : struct.begin {bpatch}',
                '            PrimaryWeaponParams : struct.begin {bpatch}']
        tail = ['            struct.end', '         struct.end', '      struct.end']
        if 'EAmmoCaliber::A762' in cals:
            p = cals['EAmmoCaliber::A762']
            it = at(p, 'Items').children
            assert 2 <= len(it) <= 3 and all(strip(i.val('ItemPrototypeSID')) == 'A762SniperD' for i in it), (sp, r.key)
            body = [f'               {p.key} : struct.begin {{bpatch}}', '                  Items : struct.begin {bpatch}']
            for i, sid in zip(it, ('A762D', 'A762A', 'A762E')):
                body += [f'                     {i.key} : struct.begin {{bpatch}}',
                         f'                        ItemPrototypeSID = {sid}', '                     struct.end']
            smart_lines += head + body + ['                  struct.end', '               struct.end'] + tail
            smart_report.append(f'{sp} {rank}: fixed to ' + '/'.join(('A762D', 'A762A', 'A762E')[:len(it)]))
        elif 'EAmmoCaliber::A545' in cals:
            s = cals['EAmmoCaliber::A545']
            it = at(s, 'Items').children
            sids = [strip(i.val('ItemPrototypeSID')) for i in it]
            assert all(x in ('A545D', 'A545A', 'A545E') for x in sids), (sp, r.key, sids)
            body = ['               [*] : struct.begin', '                  PriorityCaliber = EAmmoCaliber::A762']
            body += [f'                  {k} = {strip(s.val(k))}' for k in ('MainWeaponAmmoCount', 'MinSpawnChance', 'MaxSpawnChance')]
            body.append('                  Items : struct.begin')
            for i, sid in zip(it, sids):
                body += [f'                     {i.key} : struct.begin', f'                        ItemPrototypeSID = A762{sid[-1]}']
                body += [f'                        {k} = {scaled(i, k, SMART_SCALE)}' for k in ('MinCount', 'MaxCount')]
                body += [f'                        Weight = {strip(i.val("Weight"))}', '                     struct.end']
            smart_lines += head + body + ['                  struct.end', '               struct.end'] + tail
            smart_report.append(f'{sp} {rank}: added ' + '/'.join('A762' + x[-1] for x in sids))
    smart_lines += ['   struct.end', 'struct.end']

# ---------------------------------------------------------------- write
def lines_of(*nodes):
    out = []
    for n in nodes:
        n.write(out)
    return out
files = {
    ('ItemPrototypes', 'z_AKM47.cfg'): HEAD + ['// The gun (stats in WeaponData). Name/description: mod text sid_items_GunAKM47_ST_*']
        + lines_of(item) + ammo_lines,
    ('WeaponData', 'WeaponGeneralSetupPrototypes', 'z_AKM47.cfg'): HEAD + ['// 7.62x39, more recoil, less accurate, jams less']
        + lines_of(gs),
    ('WeaponData', 'WeaponAttributesPrototypes', 'z_AKM47.cfg'): HEAD + lines_of(pa, na),
    ('UpgradePrototypes', 'z_AKM47.cfg'): HEAD + ['// the AKM-47 upgrade tree (own text for: ' + ', '.join(upg_new_text) + ')']
        + upg_lines,
    ('NPCPrototypes', 'z_AKM47.cfg'): HEAD + ['// technicians may install the AKM-47 upgrades: every list with the AKM-74S upgrades gets ours too']
        + tech_lines,
    ('QuestNodePrototypes', 'z_AKM47.cfg'): HEAD + ['// quest steps that teach a technician the AKM-74S upgrades also teach the AKM-47 ones']
        + quest_tech_lines,
    ('WeaponData', 'CharacterWeaponSettingsPrototypes', 'z_AKM47.cfg'): HEAD
        + [f'// player: damage 23 -> 30, armor piercing 1.0 -> 1.8, range 3000 -> 2500; NPC damage 9.5 -> 12']
        + lines_of(ps, ns),
    ('ItemGeneratorPrototypes', 'z_AKM47.cfg'): HEAD
        + ['// NPCs: the AKM-47 joins the gun pool of generic eastern-faction loadouts (appended, nothing replaced),',
           f'// weight per entry for a chance by rank of {NPC_CHANCE}', '']
        + npc_lines
        + ['', '// traders: 7.62x39 next to 5.45x39 of the same kind, the AKM-47 wherever the AKM-74S is sold'] + trade_lines
        + ['', '// world stashes, ammo crates, caches: 7.62x39 next to 5.45x39 - FMJ in medium stashes/crates/caches,',
           f'// AP and (Veteran/Master) hollow-point in rare stashes; same weight, {LOOT_SCALE}x the count'] + loot_lines,
    ('StashPrototypes', 'z_AKM47.cfg'): HEAD + ['// "smart" ammo of bodies (easier difficulties) and world stashes also gives 7.62x39 for the AKM-47']
        + smart_lines,
}

# ---------------------------------------------------------------- new 3D model (Zone Kit version only)
# The AKM-74S is built from static meshes on the bones of the SK_AK74 dummy (GS WeaponStaticMeshParts)
# plus a magazine attach item on jnt_magazine. Our AK-47 parts are imported into the Zone Kit mod
# (tools/blender_export_parts.py + tools/ue_import_akm47.py), so only the Zone Kit build can point at
# them; the ~mods/TEST paks keep the AKM-74S look (they can't carry 3D assets).
# Model: "AK-47" by Lokeig, CC BY-NC 4.0 (CREDITS.txt).
import copy
ASSETS = '/AKM47/Weapons/AKM47'
sm_path = lambda n: f"StaticMesh'{ASSETS}/{n}.{n}'"
# Part per AKM-74S slot, IN THE VANILLA ORDER. The game merges this array with the inherited GunAK74_ST one
# BY INDEX (despite {bskipref}): a shorter list left the AKM-74S parts of the remaining slots in place - in game
# 2026-10-05 the AKM-74S bolt carrier/charging handle showed next to ours ("2 cocking handles"). So all 8 slots
# are filled. Slots with no AK-47 part (magazine_tab, ring) get a second copy of our trigger on jnt_trigger: the
# same mesh at the same spot, so nothing extra is visible. None = keep the AKM-74S part.
# jnt_bullet: the AKM-74S live round floated inside our receiver (visible once the bolt carrier moved, in game
# 2026-10-05); the round now comes with our full magazine mesh, so that slot is a filler too.
MODEL_PARTS = {'jnt_bullet': ('jnt_trigger', 'SM_AKM47_Trigger'), 'jnt_bullet_shell': (None, None),
               'jnt_magazine_tab': ('jnt_trigger', 'SM_AKM47_Trigger'), 'jnt_offset': (None, 'SM_AKM47_Body'),
               'jnt_ring': ('jnt_trigger', 'SM_AKM47_Trigger'), 'jnt_selector_plate': (None, 'SM_AKM47_Selector'),
               'jnt_shutter': (None, 'SM_AKM47_Shutter'), 'jnt_trigger': (None, 'SM_AKM47_Trigger')}
MESH_WORLD, MESH_MAG_FULL, MESH_MAG_EMPTY = 'GunAKM47_StaticMesh', 'GunAKM47_MagDefaultFull', 'GunAKM47_MagDefaultEmpty'

# Icons rendered from our model with cameras fitted to the AKM-74S icons (tools/icons/, Zone Kit import
# tools/ue_import_icons.py). Layers stack: body + magazine layer (+ vanilla AK74 attachment layers, which line up
# because the rig and cameras are the same). The upgrade screen's *_upgrade images aren't referenced in any cfg -
# assumed to be found by name next to the base icon.
ICONS = '/AKM47/UI/Icons'
tex_path = lambda n: f"Texture2D'{ICONS}/{n}.{n}'"
VAN_UI = '/Game/GameLite/FPS_Game/UIRemaster/UITextures'
van_tex = lambda folder, n: f"Texture2D'{VAN_UI}/{folder}/{n}.{n}'"

def model_files():
    m_item, m_gs = copy.deepcopy(item), copy.deepcopy(gs)
    setv(m_item, 'MeshInWorldPrototypeSID', 'GunAK74_StaticMesh', MESH_WORLD)
    setv(m_item, 'Icon', van_tex('Inventory/WeaponAndAttachments/AK74', 'T_inv_w_ak74_body'), tex_path('T_inv_w_akm47_body'))
    setv(m_item, 'StatisticIconImagePath', van_tex('PDA/Stats/Weapons', 'T_pda_statistic_weapon_ak74'),
         tex_path('T_pda_statistic_weapon_akm47'))
    # upgrade screen: the stock orb sat on the lower edge of our (taller, wooden) stock; raise it to the middle.
    # SectionSettings positions are offsets on the upgrade picture, negative Top = up (in game 2026-10-05).
    stock = [c for c in at(m_item, 'SectionSettings').children if strip(c.val('UpgradeTargetPartType')) == 'EUpgradeTargetPartType::Stock'][0]
    setv(stock, 'TopPosition', '-68.977211', '-114.0')
    # handguard orb: the AKM-74S spot crowds the body orb on our picture; move it to the middle of the lower
    # handguard. Estimate: offsets fitted to the stock-orb check (~1.69 px of the 1940x800 _upgrade picture per
    # unit from its centre) - check in game.
    hg = [c for c in at(m_item, 'SectionSettings').children if strip(c.val('UpgradeTargetPartType')) == 'EUpgradeTargetPartType::Handguard'][0]
    setv(hg, 'LeftPosition', '8.022902', '80.0')
    setv(hg, 'TopPosition', '-54.683498', '-40.0')
    # Screenshot (75), 2026-10-07: grip orb (1261, 540) floats beside the grip.
    # Stock/handguard offsets match 1 screen pixel per unit at 1920x1080;
    # move it to the grip centre near (1220, 512). Confirmed in game, 2026-10-07.
    grip = [c for c in at(m_item, 'SectionSettings').children if strip(c.val('UpgradeTargetPartType')) == 'EUpgradeTargetPartType::PistolGrip'][0]
    setv(grip, 'LeftPosition', '-206.023209', '-247.0')
    setv(grip, 'TopPosition', '15.830881', '-12.0')
    # weapon setup: our parts on the bones (magazine_tab and ring: no part on the AK-47 model)
    parts = at(m_gs, 'WeaponStaticMeshParts')
    old = {strip(c.val('SocketName')): c for c in parts.children}
    assert set(old) == {'jnt_bullet', 'jnt_bullet_shell', 'jnt_magazine_tab', 'jnt_offset', 'jnt_ring',
                        'jnt_selector_plate', 'jnt_shutter', 'jnt_trigger'}, sorted(old)
    for c in parts.children:                      # keep the vanilla order and count (merged by index in game)
        socket, mesh = MODEL_PARTS[strip(c.val('SocketName'))]
        if socket:
            c.get('SocketName').value = socket
        if mesh:
            c.get('MeshPath').value = sm_path(mesh)
    # magazine: our own magazine ITEM with the AK-47 magazine model. Reload animations are listed per
    # magazine item in the AKM-74S animation collections, so the Zone Kit mod also carries edited copies of
    # AnimCollection_fp_AK74 / _fp_AK74_GrenLaunch / _tp_AK74 with GunAKM47_MagDefault added as a copy of
    # GunAK74_MagDefault (tools/ue_animcollections_akm47.py). Without that, R could not reload (0.7, in game).
    # No AKM-74S muzzle brake: the AK-47 body has its own compensator.
    for path in ('CompatibleAttachments', 'PreinstalledAttachmentsItemPrototypeSIDs', 'WeaponReloadTimePerAttachment'):
        lst = at(m_gs, path)
        keep = []
        for c in lst.children:
            sid = strip(c.val('AttachPrototypeSID') or c.val('AttachSID'))
            if sid == 'AK74_DefaultMuz':
                continue
            if sid == MAG_BASE:
                c.get('AttachPrototypeSID' if c.get('AttachPrototypeSID') else 'AttachSID').value = MAG
                if c.get('WeaponSpecificIcon'):           # inventory layer of our magazine
                    setv(c, 'WeaponSpecificIcon', van_tex('Inventory/WeaponAndAttachments/AK74', 'T_inv_w_ak74_defaultmag'),
                         tex_path('T_inv_w_akm47_defaultmag'))
            keep.append(c)
        if path == 'CompatibleAttachments':
            # the AKM-74S extended and paired magazines are 5.45x39: off for now (user, 2026-10-05). The list merges by
            # index with the AKM-74S one (9 entries), so keep 9: freed slots repeat the last entry (red dot sight), else
            # the AKM-74S tail (its muzzle brake, launcher, red dot) would come back in those slots.
            keep = [c for c in keep if strip(c.val('AttachPrototypeSID')) not in DISABLED_ATTACH]
            n_van = len(at(gs_all[BASE], path).children)
            while len(keep) < n_van:
                keep.append(copy.deepcopy(keep[-1]))
        for i, c in enumerate(keep):
            c.key = f'[{i}]'
        lst.children = keep
    assert sum(strip(c.val('AttachPrototypeSID') or c.val('AttachSID')) == MAG for path in
               ('CompatibleAttachments', 'PreinstalledAttachmentsItemPrototypeSIDs', 'WeaponReloadTimePerAttachment')
               for c in at(m_gs, path).children) == 3
    mag = own(items[MAG_BASE], MAG, 'AttachPrototypes.cfg')
    setv(mag, 'MeshPrototypeSID', 'GunAK74_MagDefaultFull', MESH_MAG_FULL)
    arr = at(mag, 'Magazine.MeshArray').children
    setv(arr[0], 'MeshPrototypeSID', 'GunAK74_MagDefaultFull', MESH_MAG_FULL)
    setv(arr[1], 'MeshPrototypeSID', 'GunAK74_MagDefaultEmpty', MESH_MAG_EMPTY)
    # mesh prototypes (template [0] fields written out)
    mesh_lines = HEAD + ['// meshes of the new AK-47 model (Zone Kit assets in /AKM47/Weapons/AKM47)']
    for sid, mesh in ((MESH_WORLD, 'SM_AKM47'), (MESH_MAG_FULL, 'SM_AKM47_MagFull'), (MESH_MAG_EMPTY, 'SM_AKM47_Mag')):
        mesh_lines += [f'{sid} : struct.begin {{refurl=../MeshPrototypes.cfg;refkey=[0]}}', f'   SID = {sid}',
                       f'   MeshPath = {sm_path(mesh)}', "   MaterialPath = MaterialInstanceConstant''",
                       '   MeshType = EMeshSubType::Static', '   Pitch = 0.0', '   Yaw = 0.0', '   Roll = 0.0',
                       '   ScaleX = 1.0', '   ScaleY = 1.0', '   ScaleZ = 1.0', 'struct.end']
    f = dict(files)
    f[('ItemPrototypes', 'z_AKM47.cfg')] = (HEAD + ['// The gun (stats in WeaponData). Name/description: mod text sid_items_GunAKM47_ST_*',
                                                    '// 3D model: "AK-47" by Lokeig, CC BY-NC 4.0']
                                            + lines_of(m_item) + ammo_lines + ['', '// its magazine (AK-47 model)'] + lines_of(mag))
    f[('WeaponData', 'WeaponGeneralSetupPrototypes', 'z_AKM47.cfg')] = (
        HEAD + ['// 7.62x39, more recoil, less accurate, jams less; AK-47 model parts and magazine'] + lines_of(m_gs))
    f[('MeshPrototypes', 'z_AKM47.cfg')] = mesh_lines
    return f

ZONEKIT_GD = os.path.join(ROOT, 'zonekit', 'Content', 'GameLite', 'GameData')
model = model_files()
for gd in GDS:
    stale = os.path.join(gd, 'ObjPrototypes', 'z_AKM47.cfg')    # the old wrapper hook (removed 2026-10-05)
    if os.path.exists(stale):
        os.remove(stale)
        if not os.listdir(os.path.dirname(stale)):
            os.rmdir(os.path.dirname(stale))
    for parts, body in (model if os.path.normcase(gd) == os.path.normcase(ZONEKIT_GD) else files).items():
        p = os.path.join(gd, *parts)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('\n'.join(body) + '\n')
print(f'NPC gun pools: {len(npc_pool)} entries in {len(targets)} loadouts')
for (t, key), adds in npc_pool.items():
    print(f'   {t} {key}: weight {adds[0][1][1]}')
print('traders:')
for (lst, key), adds in trade.items():
    print('   ', lst, key, ', '.join(' '.join(f'{k}={v}' for k, v in a if k != 'ItemPrototypeSID') + ' ' + a[0][1] for a in adds))
print('stash loot:', len(loot), 'entries in', len({k[0] for k in loot}), 'lists')
for (lst, key), adds in loot.items():
    if not lst.startswith(('Stash_Medium_', 'Stash_Expensive_')):
        print('   ', lst, key, ', '.join(f"{dict(a)['ItemPrototypeSID']} w{dict(a)['Weight']} {dict(a)['MinCount']}-{dict(a)['MaxCount']}" for a in adds))
for line in smart_report:
    print('   smart', line)
for gd in GDS:
    print('wrote', gd)
