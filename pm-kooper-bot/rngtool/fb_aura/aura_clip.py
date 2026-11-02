"""Real-console check (S-Video -> GV-USB2, 1280x720 60 fps recording): do the white star outlines around Final Bowser
move like the energy_in_out type-4 aura model? Takes capture frames START..START+COUNT (a stretch with a still
camera), keeps the distinct game frames (the game draws at 30 fps: every 2nd capture frame, with occasional cadence
slips), finds bright blobs over the dark sky (luma 50+ above the per-pixel median, median luma < 90), links them into
tracks (2-16 px steps), and fits ONE common centre and px/unit with every star at angle theta0 - 2 t (deg, counter-
clockwise) and radius k (r0 + v t), as the model says. Prints the tracks, the fit and the rms residual.
The recording is not part of the repo. usage: python3 aura_clip.py CLIP.mkv [START=9] [COUNT=16] [T0_SECONDS=1.0]"""
import sys, os, math, subprocess, tempfile, glob
import numpy as np
from PIL import Image
from scipy import ndimage, optimize

clip = sys.argv[1]; START = int(sys.argv[2]) if len(sys.argv) > 2 else 9
COUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 16; T0 = sys.argv[4] if len(sys.argv) > 4 else '1.0'
tmp = tempfile.mkdtemp()
subprocess.run(['ffmpeg', '-v', 'error', '-ss', T0, '-i', clip, '-frames:v', str(START + COUNT), os.path.join(tmp, 'g%03d.png')], check=True)
F = [np.asarray(Image.open(os.path.join(tmp, 'g%03d.png' % i)).convert('RGB')).astype(int) for i in range(START, START + COUNT)]
G = [F[0]]
for f in F[1:]:
    if np.abs(f - G[-1])[150:700, 320:1270].mean() > 0.5: G.append(f)
lum = lambda a: a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
med = lum(np.median(np.stack(G), 0))
B = []
for g in G:
    m = (lum(g) - med > 50) & (med < 90); m[:150] = False; m[:, :700] = False
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
    cs = ndimage.center_of_mass(m, lab, range(1, n + 1)); sz = ndimage.sum(m, lab, range(1, n + 1))
    B.append([(c[1], c[0]) for c, s in zip(cs, sz) if 15 <= s <= 700])
tracks = []
for k, bl in enumerate(B):
    for p in bl:
        best = None
        for t in tracks:
            if t[-1][0] == k - 1:
                d = math.dist(t[-1][1], p)
                if 2 < d < 16 and (best is None or d < best[0]): best = (d, t)
        if best: best[1].append((k, p))
        else: tracks.append([(k, p)])
T = [t for t in tracks if len(t) >= 4]
print('distinct game frames', len(G), '; tracks with >= 4 frames:', len(T))
for t in T: print('  ', [(k, int(x), int(y)) for k, (x, y) in t])


def res(par, rate=2.0):
    cx, cy, kk = par[:3]; out = []; j = 3
    for t in T:
        th0, r0, v = par[j:j + 3]; j += 3
        for k, (x, y) in t:
            th = math.radians(th0 - rate * k); r = kk * (r0 + v * k)
            out += [cx + r * math.cos(th) - x, cy - r * math.sin(th) - y]
    return out


for rate in (2.0, 0.0, -2.0):
    best = None
    for cx0 in range(900, 1250, 50):
        for cy0 in range(150, 450, 50):
            p0 = [cx0, cy0, 5.0]
            for t in T:
                k, (x, y) = t[0]; p0 += [math.degrees(math.atan2(-(y - cy0), x - cx0)) + rate * k, math.dist((x, y), (cx0, cy0)) / 5, 1.5]
            s = optimize.least_squares(lambda p: res(p, rate), p0)
            if best is None or s.cost < best.cost: best = s
    r = np.array(best.fun).reshape(-1, 2)
    print('rotation %+.0f deg/frame: centre (%.1f, %.1f) px, %.2f px/unit, rms residual %.2f px over %d points'
          % (-rate, best.x[0], best.x[1], best.x[2], math.sqrt((r ** 2).sum(1).mean()), len(r)))
