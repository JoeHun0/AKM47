"""Stack: vanilla layer(s) on top, render below, render outline (green) drawn on the vanilla.
py compare.py <out.png> <render.png> <vanilla.png> [more vanilla layers...]"""
import sys
import numpy as np
from PIL import Image, ImageFilter
out, render, *van = sys.argv[1:]
r = Image.open(render).convert('RGBA'); W, H = r.size
v = Image.new('RGBA', (W, H), (40, 40, 40, 255))
for f in van: v.alpha_composite(Image.open(f).convert('RGBA'))
edge = np.asarray(r.getchannel('A').point(lambda a: 255 if a > 127 else 0).filter(ImageFilter.FIND_EDGES)) > 0
va = np.array(v); va[edge] = (0, 255, 0, 255)
rb = Image.new('RGBA', (W, H), (40, 40, 40, 255)); rb.alpha_composite(r)
c = Image.new('RGBA', (W, H * 2)); c.paste(Image.fromarray(va), (0, 0)); c.paste(rb, (0, H))
if W > 1000: c = c.resize((W // 2, H))
c.save(out)
