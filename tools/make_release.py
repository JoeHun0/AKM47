r"""Make the release zip for Vortex / Nexus / manual install from the Zone Kit's packaged mod.
Usage: py tools\make_release.py <version>
Do first: sync the PROD build into the Zone Kit mod (make_akm47.py, copy zonekit\Content\GameLite) and run
Package Mod in the Zone Kit. This script only zips what Package Mod produced.

Output: release\AKM47_<version>.zip with
  AKM47\  the six Zone Kit containers (NewContent + OverrideContent .pak/.ucas/.utoc), unchanged names
  README.txt (+ install steps), CREDITS.txt
Vortex puts the six files into Stalker2\Content\Paks\~mods (same layout as other Zone Kit mods on Nexus,
e.g. ZoneLink). Safety checks: all six files present, and the packaged cfgs are the prod build (no TEST marker,
identical to zonekit\Content\GameLite\GameData).
"""
import filecmp, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGED = r'D:\Programs\Epic\STALKER2ZoneKit\Stalker2\SavedMods\Staged\AKM47\Windows'
REPAK = r'C:\Users\KotnyekJM\Documents\stalker 2 mods\NPCGunProgression\repak.exe'
assert len(sys.argv) > 1, 'pass a version, e.g. 1.0'
VERSION = sys.argv[1]
INSTALL = r'''
Install
-------
Vortex: drag the zip into Vortex (or Mod Manager Download), install, enable, deploy.
Manual: copy the six files from the AKM47 folder of the zip into
  <game folder>\Stalker2\Content\Paks\~mods
(create the ~mods folder if it doesn't exist). Keep the file names unchanged.
Don't use this together with the Steam Workshop / mod.io version (it would load twice).
Uninstall: delete the six AKM47Stalker2-Windows-*.pak/.ucas/.utoc files.

Version {ver}
'''

files = []
for part in ('NewContent', 'OverrideContent'):
    d = os.path.join(STAGED, part, 'Windows', 'Stalker2', 'Mods', 'AKM47', 'Content', 'Paks', 'Windows')
    for ext in ('pak', 'ucas', 'utoc'):
        p = os.path.join(d, f'AKM47Stalker2-Windows-{part}.{ext}')
        assert os.path.isfile(p), f'{p} missing - run Package Mod first'
        files.append(p)

# the packaged cfgs must be the prod build
tmp = tempfile.mkdtemp()
try:
    over = [f for f in files if f.endswith('OverrideContent.pak')][0]
    subprocess.run([REPAK, 'unpack', '-q', '-f', '-o', tmp, over], check=True)
    cfgs = [os.path.join(dp, f) for dp, _, fs in os.walk(tmp) for f in fs if f.endswith('.cfg')]
    assert cfgs, 'no cfg files in the OverrideContent pak'
    gd = os.path.join(ROOT, 'zonekit', 'Content', 'GameLite', 'GameData')
    for c in cfgs:
        txt = open(c, encoding='utf-8', errors='replace').read()
        assert 'TEST BUILD' not in txt and 'AKM47_TEST' not in txt, f'TEST build packaged: {c} - sync prod and repackage'
        rel = c.replace('\\', '/').split('/GameData/', 1)[-1]
        ours = os.path.join(gd, *rel.split('/'))
        if os.path.isfile(ours):
            assert filecmp.cmp(c, ours, shallow=False), f'packaged {rel} differs from the current build - repackage'
    print(f'packaged cfgs OK ({len(cfgs)} files, prod)')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

readme = open(os.path.join(ROOT, 'README.txt'), encoding='utf-8').read().rstrip() + '\n' + INSTALL.format(ver=VERSION)
out = os.path.join(ROOT, 'release', f'AKM47_{VERSION}.zip')
os.makedirs(os.path.dirname(out), exist_ok=True)
assert not os.path.exists(out), f'{out} exists - pass a new version'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, 'AKM47/' + os.path.basename(p))
    z.writestr('README.txt', readme.replace('\n', '\r\n'))
    z.write(os.path.join(ROOT, 'CREDITS.txt'), 'CREDITS.txt')
print('wrote', out, os.path.getsize(out), 'bytes')
