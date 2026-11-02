"""Real footage -> star restart observations for aura_relock.c.
Takes aura_detect.py's JSON, refits every track with the aura model (bounded speeds 0.6-2.6, restart radius 10 units)
under one camera: centre and px/unit start from the emulator geometry mapped to the capture (registration of the
emulator menu frame onto the clip: capture x = 274 + 3.264 X, y = -24 + 3.32 Y in N64 px; centre (232.0, 117.3),
1.70 / 1.61 units -> kx 5.55, ky 5.35) and are refined on the good tracks. Each kept track gives (restart frame f0,
draw angle A); duplicates (same f0 +-1, A +-6) are merged. Writes obs.txt (anchor first: the best-fitting long track).
usage: python3 aura_realobs.py DET.json OBS.txt [MAXRMS=4.5] [F0MIN=-6] [F0MAX=99]"""
import sys, json, math
import numpy as np
from scipy import optimize
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import aura_detect as d

D = json.load(open(sys.argv[1])); OUT = sys.argv[2]
MAXRMS = float(sys.argv[3]) if len(sys.argv) > 3 else 4.5
F0MIN = float(sys.argv[4]) if len(sys.argv) > 4 else -6; F0MAX = float(sys.argv[5]) if len(sys.argv) > 5 else 99
B = [[tuple(b) for b in fr] for fr in D['blobs']]
T = [t for t in d.link(B) if len(t) >= 4]


def fit1(t, cam):
    CX, CY, KX, KY = cam
    def res(p):
        f0, A, v = p; out = []
        for k, x, y, s in t:
            n = k - f0 + 1; th = math.radians(A - 2 * n); r = 10 + v * n
            out += [CX + KX * r * math.cos(th) - x, CY - KY * r * math.sin(th) - y]
        return out
    best = None; k, x, y, s = t[0]
    for v0 in (0.8, 1.6, 2.4):
        r = math.hypot((x - CX) / KX, (y - CY) / KY); n0 = max(1, (r - 10) / v0)
        p0 = [k - n0 + 1, math.degrees(math.atan2(-(y - CY) / KY, (x - CX) / KX)) + 2 * n0, v0]
        so = optimize.least_squares(res, p0, bounds=([-80, -1e4, 0.55], [80, 1e4, 2.65]))
        if best is None or so.cost < best.cost: best = so
    r = np.array(best.fun).reshape(-1, 2)
    return best.x, math.sqrt((r ** 2).sum(1).mean())


cam = [1031.2, 365.4, 5.55, 5.35]
for it in range(2):
    fits = [(t,) + fit1(t, cam) for t in T]
    good = [f for f in fits if f[2] < MAXRMS and len(f[0]) >= 5]
    def res(c):
        return [f2 for t, p, r in good for f2 in [fit1(t, c)[1]]]
    if len(good) >= 4:
        so = optimize.least_squares(res, cam, diff_step=[1e-3] * 4, bounds=([950, 280, 4.0, 4.0], [1110, 450, 7.0, 7.0]))
        cam = list(so.x)
fits = [(t,) + fit1(t, cam) for t in T]
print('camera: centre (%.1f, %.1f) kx %.2f ky %.2f; tracks %d, rms < %.1f: %d' % (*cam, len(T), MAXRMS, sum(1 for f in fits if f[2] < MAXRMS)))
obs = []
for t, p, r in fits:
    if r >= MAXRMS or not (F0MIN <= p[0] <= F0MAX): continue
    obs.append(dict(f0=float(p[0]), A=float(p[1] % 360), v=float(p[2]), rms=r, n=len(t)))
obs.sort(key=lambda o: o['f0'])
merged = []
for o in obs:
    m = next((q for q in merged if abs(q['f0'] - o['f0']) <= 1.0 and min(abs(q['A'] - o['A']), 360 - abs(q['A'] - o['A'])) <= 6), None)
    if m:
        if o['n'] > m['n']: m.update(o)
    else: merged.append(o)
anchor = min(merged, key=lambda o: o['rms'] / math.sqrt(o['n']))
lines = [anchor] + [o for o in merged if o is not anchor]
with open(OUT, 'w') as fh:
    fh.write('%d\n' % len(lines))
    for o in lines: fh.write('%.2f %d\n' % (o['f0'], round(o['A']) % 360))
for o in lines: print('  f0 %6.2f A %6.1f v %.2f rms %.2f n %d' % (o['f0'], o['A'], o['v'], o['rms'], o['n']))
json.dump(dict(cam=cam, obs=lines), open(OUT + '.json', 'w'))
