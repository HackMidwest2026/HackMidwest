"""Rank cloud9_search.c candidates by how well their 10 puffs, drawn as white disks (size by age, rising 0.6/frame),
explain the capture's white masks (masks.bin from cloud9_prep.py): per frame, IoU of predicted puffs vs observed
white, outside the white that is there without any puff (frame 0 = before puff 0, and Mario's cloud is not
modelled, so the absolute IoU is low; only the ranking and its margin matter).
usage: python3 cloud9_score.py masks.bin solutions.txt"""
import sys, numpy as np, cv2
X0, Y0, W, H, NM = 560, 360, 440, 320, 21
M = np.fromfile(sys.argv[1], np.uint8).reshape(NM, H, W).astype(bool)
SC = [0, .30, .80, 1.20, 1.12, 1.04, 1.00, .94, .92, 1.0, 1.05, 1.07, 1.05, 1.0, .94, .92]
def pred(vals, m):
    p = np.zeros((H, W), np.uint8)
    for k, (dx, dy) in enumerate(vals):
        age = m - k
        if age < 1 or age >= len(SC): continue
        cx = 773.8 + 4.313 * dx - X0; cy = 503.5 - 4.18 * (dy + 0.6 * (age - 1)) - Y0
        cv2.circle(p, (int(round(cx)), int(round(cy))), max(2, int(round(0.85 * 24.7 * SC[age]))), 1, -1)
    return p.astype(bool)
rows = []
for line in open(sys.argv[2]):
    t = line.split(); seed, ph = t[0], t[1]
    vals = [tuple(int(v) for v in x.rstrip('+').split(',')) for x in t[2:]]
    sc = 0
    for m in range(1, 16):
        p = pred(vals, m); o = M[m]
        sc += (p & o).sum() / max(1, (p | o).sum())
    rows.append((sc / 15, seed, ph, ' '.join(t[2:])))
rows.sort(reverse=True)
for r in rows[:8]: print('%.4f %s %s %s' % r)
s = np.array([r[0] for r in rows]); print('n', len(s), 'median %.4f  sd %.4f  best-2nd %.4f  (best - median)/sd %.1f' % (np.median(s), s.std(), s[0] - s[1], (s[0] - np.median(s)) / s.std()))
