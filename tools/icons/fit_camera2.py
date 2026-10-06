"""Refine an icon camera with Nelder-Mead on IoU (continuous yaw, pitch, roll, perspective p=1/d, scale, offset).
Starts from the best grid candidates of fit_camera's search. Usage: py fit_camera2.py <icon> <set> <out.json> <mirror 0|1> [twin-of.json]"""
import sys, json, math
import numpy as np
from PIL import Image
from fit_camera import project, place, raster, bbox_fit

icon, setname, out, mirror = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == '1'
full = Image.open(icon).convert('RGBA').getchannel('A')
DS = 2 if full.size[0] > 1000 else 1                       # work at half size for the big images
mask = np.asarray(full.resize((full.size[0] // DS, full.size[1] // DS))) > 127
T = np.load('tris_ak74.npz'); tris = np.concatenate([T[n] for n in setname.split('+')])
centre = tris.reshape(-1, 3).mean(0)

def cam_of(x):
    yaw, pitch, roll, p, ls, tx, ty = x
    return dict(yaw=yaw, pitch=pitch, roll=roll, d=1.0 / max(p, 1e-3), mirror=mirror, s=math.exp(ls), tx=tx, ty=ty)
def score(x):
    if x[3] < 0.0 or x[3] > 4.0: return 0.0
    c = cam_of(x); u, v, _ = project(tris, c, centre)
    sil = raster(place(u, v, c), (mask.shape[1], mask.shape[0]))
    return (sil & mask).sum() / max(1, (sil | mask).sum())
def nelder_mead(x0, step, iters=400):
    n = len(x0); pts = [np.array(x0, float)] + [np.array(x0, float) + np.eye(n)[i] * step[i] for i in range(n)]
    vals = [-score(p) for p in pts]
    for _ in range(iters):
        o = np.argsort(vals); pts = [pts[i] for i in o]; vals = [vals[i] for i in o]
        c = np.mean(pts[:-1], 0); xr = c + (c - pts[-1]); fr = -score(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = -score(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = -score(xc)
            if fc < vals[-1]: pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]; vals = [vals[0]] + [-score(p) for p in pts[1:]]
    i = int(np.argmin(vals)); return pts[i], -vals[i]

# starting points: grid over yaw/pitch/perspective, bbox-fitted
starts = []
for yaw in np.radians(np.arange(-50, 51, 10)):
    for pitch in np.radians(np.arange(-40, 41, 10)):
        for p in (0.0, 0.5, 1.0, 2.0):
            c = bbox_fit(dict(yaw=yaw, pitch=pitch, roll=0.0, d=1.0 / max(p, 1e-3), mirror=mirror), tris, centre, mask)
            x = [yaw, pitch, 0.0, p, math.log(c['s']), c['tx'], c['ty']]
            starts.append((score(x), x))
starts.sort(key=lambda t: -t[0])
if len(sys.argv) > 5:                      # refine from a given camera with (yaw, pitch) negated: the mirror-twin
    c0 = json.load(open(sys.argv[5]))      # solution (a thin gun looks the same from (y, p) and (-y, -p))
    x0 = [-c0['yaw'], -c0['pitch'], c0['roll'], 1.0 / c0['d'], math.log(c0['s'] / DS), c0['tx'] / DS, c0['ty'] / DS]
    starts = [(score(x0), x0)]
best = None
for sc0, x0 in starts[:6]:
    x, sc = nelder_mead(x0, [0.08, 0.08, 0.04, 0.3, 0.05, 6, 6])
    x, sc = nelder_mead(x, [0.02, 0.02, 0.01, 0.1, 0.01, 2, 2])
    print(f'  start {sc0:.3f} -> {sc:.3f}')
    if not best or sc > best[1]: best = (x, sc)
x, sc = best; cam = cam_of(x)
cam['s'] *= DS; cam['tx'] *= DS; cam['ty'] *= DS
cam.update(centre=centre.tolist(), iou=sc, size=list(full.size), yaw_deg=math.degrees(cam['yaw']),
           pitch_deg=math.degrees(cam['pitch']), roll_deg=math.degrees(cam['roll']))
json.dump(cam, open(out, 'w'), indent=1)
print(f"FIT {out}: IoU {sc:.3f} yaw {cam['yaw_deg']:.1f} pitch {cam['pitch_deg']:.1f} roll {cam['roll_deg']:.1f} d {cam['d']:.2f} mirror {mirror}")
