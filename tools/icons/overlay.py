"""Overlay: vanilla icon (as is) with the fitted silhouette outline in green. py overlay.py <icon> <set> <cam.json> <out.png>"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
from fit_camera import project, place, raster
icon, setname, camf, out = sys.argv[1:5]
cam = json.load(open(camf)); T = np.load('tris_ak74.npz')
tris = np.concatenate([T[n] for n in setname.split('+')])
u, v, _ = project(tris, cam, np.array(cam['centre']))
sil = Image.fromarray((raster(place(u, v, cam), tuple(cam['size'])) * 255).astype('uint8'))
edge = np.asarray(sil.filter(ImageFilter.FIND_EDGES)) > 0
base = Image.new('RGBA', sil.size, (40, 40, 40, 255)); base.alpha_composite(Image.open(icon).convert('RGBA'))
a = np.array(base); a[edge] = (0, 255, 0, 255)
Image.fromarray(a).resize((sil.size[0] * 2, sil.size[1] * 2), Image.NEAREST).save(out)
