"""Fit the camera of a vanilla icon: project the AKM-74S part triangles, rasterize the silhouette and maximise
its overlap (IoU) with the icon's alpha mask. Camera = view from the gun's right side (-Y), turned by yaw (about
Z), pitch, roll, perspective distance d (m), optional horizontal mirror, then scale + offset in pixels.
Usage: py fit_camera.py <icon.png> <set: body|body+mag> <out.json> [mirror 0|1|auto]"""
import sys, json, math
import numpy as np
from PIL import Image, ImageDraw

def rot(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = map(lambda a: a, (math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch),
                                                 math.cos(roll), math.sin(roll)))
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])     # pitch: tilt about the image x axis
    Ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]])     # roll: about the view axis (y)
    return Ry @ Rx @ Rz

def project(P, cam, centre):
    """P (...,3) metres. Returns image-space u (right), v (down) before scale/offset, and depth."""
    Q = (P - centre) @ rot(cam['yaw'], cam['pitch'], cam['roll']).T
    depth = Q[..., 1]                                          # camera at -y looking +y
    k = cam['d'] / (cam['d'] + depth)
    u = Q[..., 0] * k
    v = -Q[..., 2] * k
    if cam.get('mirror'):
        u = -u
    return u, v, depth

def raster(tris_uv, size):
    img = Image.new('L', size, 0); dr = ImageDraw.Draw(img)
    for t in tris_uv:
        dr.polygon([tuple(p) for p in t], fill=255)
    return np.asarray(img) > 127

def place(u, v, cam):
    return np.stack([u * cam['s'] + cam['tx'], v * cam['s'] + cam['ty']], -1)

def iou(cam, tris, centre, mask):
    u, v, _ = project(tris, cam, centre)
    sil = raster(place(u, v, cam), (mask.shape[1], mask.shape[0]))
    return (sil & mask).sum() / max(1, (sil | mask).sum())

def bbox_fit(cam, tris, centre, mask):
    u, v, _ = project(tris, cam, centre)
    ys, xs = np.nonzero(mask)
    w_img, h_img = xs.max() - xs.min(), ys.max() - ys.min()
    s = min(w_img / (u.max() - u.min()), h_img / (v.max() - v.min()))
    cam['s'] = s
    cam['tx'] = (xs.min() + xs.max()) / 2 - s * (u.max() + u.min()) / 2
    cam['ty'] = (ys.min() + ys.max()) / 2 - s * (v.max() + v.min()) / 2
    return cam

def fit(icon, setname, mirror):
    mask = np.asarray(Image.open(icon).convert('RGBA').getchannel('A')) > 127
    T = np.load('tris_ak74.npz')
    tris = np.concatenate([T[n] for n in setname.split('+')])
    centre = tris.reshape(-1, 3).mean(0)
    best = None
    mirrors = [False, True] if mirror == 'auto' else [mirror == '1']
    for mir in mirrors:
        for yaw in np.radians(np.arange(-40, 41, 10)):
            for pitch in np.radians(np.arange(-30, 31, 10)):
                for d in (0.6, 1.2, 3.0, 50.0):
                    cam = dict(yaw=yaw, pitch=pitch, roll=0.0, d=d, mirror=mir)
                    sc = iou(bbox_fit(cam, tris, centre, mask), tris, centre, mask)
                    if not best or sc > best[0]:
                        best = (sc, dict(cam))
    sc, cam = best
    steps = dict(yaw=math.radians(4), pitch=math.radians(4), roll=math.radians(2), d=0.3, s=0.02, tx=3, ty=3)
    for it in range(60):
        improved = False
        for k, st in steps.items():
            for sign in (1, -1):
                c = dict(cam)
                c[k] = c[k] * (1 + sign * st) if k in ('s',) else c[k] + sign * st
                if k == 'd' and c[k] <= 0.2: continue
                if k in ('yaw', 'pitch', 'roll', 'd'):
                    c = bbox_fit(c, tris, centre, mask) if it < 20 else c
                v = iou(c, tris, centre, mask)
                if v > sc:
                    sc, cam, improved = v, c, True
        if not improved:
            steps = {k: v / 2 for k, v in steps.items()}
            if steps['yaw'] < math.radians(0.05): break
    cam['centre'] = centre.tolist(); cam['iou'] = sc; cam['size'] = [mask.shape[1], mask.shape[0]]
    cam['yaw_deg'], cam['pitch_deg'], cam['roll_deg'] = (math.degrees(cam[k]) for k in ('yaw', 'pitch', 'roll'))
    cam['mirror'] = bool(cam['mirror'])
    return cam

if __name__ == '__main__':
    icon, setname, out = sys.argv[1:4]
    mirror = sys.argv[4] if len(sys.argv) > 4 else 'auto'
    cam = fit(icon, setname, mirror)
    json.dump(cam, open(out, 'w'), indent=1)
    print(f"FIT {out}: IoU {cam['iou']:.3f} yaw {cam['yaw_deg']:.1f} pitch {cam['pitch_deg']:.1f} roll {cam['roll_deg']:.1f} "
          f"d {cam['d']:.2f} mirror {cam['mirror']} s {cam['s']:.1f} t ({cam['tx']:.0f},{cam['ty']:.0f})")
