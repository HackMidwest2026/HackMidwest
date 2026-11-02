"""Real clip timing marks (half-res 640x360 frames, numbered as capture frames = t * 60): input-display A presses,
Mario's menu wheel, damage stars (yellow), the Duplighost transform ring (pink/magenta, and yellow at its start).
usage: python3 clip_marks.py FRAMEDIR FIRST LAST"""
import sys, os
import numpy as np
from PIL import Image
D, A, B = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rows = []
for f in range(A, B + 1):
    p = os.path.join(D, '%04d.png' % f)
    if not os.path.exists(p): continue
    im = np.asarray(Image.open(p).convert('RGB')).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    a_fill = int(b[26:35, 109:120].mean())                                     # input display: A (blue) filled when held (~100 idle, ~175 held)
    wheel = int(((r > 200) & (g > 200) & (b > 200))[200:340, 160:340].sum())   # Mario's menu: the white wheel/spotlight
    yellow = int(((r > 200) & (g > 180) & (b < 110))[60:300, 80:640].sum())    # damage stars / ring start
    mag = int(((r > 170) & (b > 170) & (g < 110))[60:330, 80:640].sum())       # pink transform ring
    rows.append((f, a_fill, wheel, yellow, mag))
last = None
for x in rows:
    key = (x[1] > 140, x[2] > 300, x[3] > 150, x[4] > 150)
    if key != last: print('frame %d (t=%.3f s): A %s, wheel %s, yellow %s, ring %s   raw %s' % (x[0], x[0] / 60, *key, x[1:]))
    last = key
