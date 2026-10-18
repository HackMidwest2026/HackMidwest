"""Track Laki and the star piece in an extracted clip (DIR/f%04d.png) by normalized cross-correlation; templates are
cut from frame 40 of the user clip (boxes in objs). usage: video_track_ncc.py DIR > track.txt"""
import numpy as np, glob, sys
from PIL import Image
D = sys.argv[1]
fs = sorted(glob.glob(D + '/f*.png'))
def load(i): return np.asarray(Image.open(fs[i]).convert('L')).astype(np.float32)
def ncc_search(img, tpl, cx, cy, R=60, Ry=20):
    th, tw = tpl.shape; t = tpl - tpl.mean(); tn = np.sqrt((t * t).sum())
    best = (-2, cx, cy)
    for y in range(max(0, cy - Ry), min(img.shape[0] - th, cy + Ry) + 1, 2):
        for x in range(max(0, cx - R), min(img.shape[1] - tw, cx + R) + 1, 2):
            w = img[y:y + th, x:x + tw]; w = w - w.mean(); s = (w * t).sum() / (np.sqrt((w * w).sum()) * tn + 1e-6)
            if s > best[0]: best = (s, x, y)
    s, bx, by = best
    for y in range(max(0, by - 2), min(img.shape[0] - th, by + 2) + 1):
        for x in range(max(0, bx - 2), min(img.shape[1] - tw, bx + 2) + 1):
            w = img[y:y + th, x:x + tw]; w = w - w.mean(); s2 = (w * t).sum() / (np.sqrt((w * w).sum()) * tn + 1e-6)
            if s2 > best[0]: best = (s2, x, y)
    return best
ref = load(39)
objs = {'laki': (425, 262, 75, 65), 'star': (705, 365, 75, 70)}
tpls = {k: ref[y:y + h, x:x + w].copy() for k, (x, y, w, h) in objs.items()}
pos = {k: (v[0], v[1]) for k, v in objs.items()}
order = list(range(39, len(fs))) + list(range(38, -1, -1))
res = {}
for i in order:
    if i == 38: pos = {k: res[39][k][1:] for k in objs}
    img = load(i); r = {}
    for k in objs:
        s, x, y = ncc_search(img, tpls[k], *pos[k]); r[k] = (s, x, y)
        if s > 0.5: pos[k] = (x, y)
    res[i] = r
for i in range(len(fs)):
    r = res[i]; print(i, ' '.join('%s %.2f %d %d' % (k, *r[k]) for k in objs))
