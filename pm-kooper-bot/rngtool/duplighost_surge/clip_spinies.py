"""Real-console clip (S-Video, 1280x720 60 fps capture): find the Spiny Surge throws and the turn's timing marks.

Per capture frame: red spiny pixels (R > 140, G < 90, B < 100) inside the game picture, connected blobs. A throw is a
blob that appears next to Lakilester's hand (the launch area) with no blob there before. Prints the throw frames
(capture frames; 2 per game frame), blob tracks for the first frames of each flight (for the readout precision) and,
with --marks, frame-difference events used for the timing checks.
usage: python3 clip_spinies.py FRAMEDIR FIRST LAST [OUT.json]   (frames extracted with ffmpeg as %04d.png = frame no.)"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage

D, A, B = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else None
X0 = 160                                   # left edge of the game picture (input display to the left)
res = []
for f in range(A, B + 1):
    p = os.path.join(D, '%04d.png' % f)
    if not os.path.exists(p): continue
    im = np.asarray(Image.open(p).convert('RGB')).astype(np.int16)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    m = (r > 140) & (g < 90) & (b < 100) & (r - g > 90)
    m[:, :X0] = False; m[:60] = False
    lab, n = ndimage.label(m)
    blobs = []
    if n:
        idx = np.arange(1, n + 1)
        area = ndimage.sum(m, lab, idx)
        com = ndimage.center_of_mass(m, lab, idx)
        for a, (cy, cx) in zip(area, com):
            if a >= 150: blobs.append((round(cx, 1), round(cy, 1), int(a)))
    res.append({'f': f, 'blobs': blobs, 'red': int(m.sum())})
if OUT: json.dump(res, open(OUT, 'w'))
for x in res:
    print(x['f'], x['red'], x['blobs'][:8])
