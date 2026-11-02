"""Long still stretch (real footage): from star tracks to the 16 aura parts.
Every star of the aura is one of 16 parts with a fixed speed v (0.6..2.6 in 0.2 steps), a fixed size (1.0/0.7/0.4)
and a fixed restart phase (frame mod 20). So the restarts seen over many cycles cluster by (f0 mod 20, v): each
cluster is one part; its restarts every 20 frames each give one rand_int(359) draw (the angle A).
Steps: tracks from aura_detect blobs -> per-track fit with a common camera (refined) -> restart frame f0, A, v ->
clustering by (round(f0) mod 20, v) -> per part: phase, speed, how many restarts were seen.
Writes PARTS.json: camera, the restarts (f0, A, v, rms, n, part) and the parts.
usage: python3 aura_parts.py BLOBS.json PARTS.json [MAXRMS=4.0]"""
import sys, os, json, math
import numpy as np
from scipy import optimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aura_detect as d

D = json.load(open(sys.argv[1])); OUT = sys.argv[2]; MAXRMS = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
B = [[tuple(b) for b in fr] for fr in D['blobs']]
T = [t for t in d.link(B) if len(t) >= 5]


def fit1(t, cam, vfix=None):
    CX, CY, KX, KY = cam
    def res(p):
        f0, A = p[:2]; v = vfix if vfix is not None else p[2]; out = []
        for k, x, y, s in t:
            n = k - f0 + 1; th = math.radians(A - 2 * n); r = 10 + v * n
            out += [CX + KX * r * math.cos(th) - x, CY - KY * r * math.sin(th) - y]
        return out
    best = None; k, x, y, s = t[0]
    for v0 in ((0.8, 1.6, 2.4) if vfix is None else (vfix,)):
        r = math.hypot((x - CX) / KX, (y - CY) / KY); n0 = max(1, (r - 10) / v0)
        p0 = [k - n0 + 1, math.degrees(math.atan2(-(y - CY) / KY, (x - CX) / KX)) + 2 * n0] + ([v0] if vfix is None else [])
        lo = [-80 + k, -1e4] + ([0.55] if vfix is None else []); hi = [80 + k, 1e4] + ([2.65] if vfix is None else [])
        so = optimize.least_squares(res, p0, bounds=(lo, hi))
        if best is None or so.cost < best.cost: best = so
    r = np.array(best.fun).reshape(-1, 2)
    p = list(best.x) + ([vfix] if vfix is not None else [])
    return p, math.sqrt((r ** 2).sum(1).mean())


cam = [1033.6, 346.9, 5.19, 5.08]          # from the Peach Beam clip's still stretch (same battle camera)
sub = sorted(T, key=len, reverse=True)[:40]
for it in range(2):
    good = [t for t in sub if fit1(t, cam)[1] < MAXRMS]
    so = optimize.least_squares(lambda c: [fit1(t, c)[1] for t in good], cam, diff_step=[1e-3] * 4,
                                bounds=([950, 250, 4.0, 4.0], [1110, 450, 7.0, 7.0]))
    cam = list(so.x)
print('camera: centre (%.1f, %.1f) kx %.2f ky %.2f (from %d long tracks)' % (*cam, len(good)))
R = []
for t in T:
    p, r = fit1(t, cam)
    if r < MAXRMS: R.append(dict(f0=p[0], A=p[1] % 360, v=p[2], rms=r, n=len(t), first=t[0][0], last=t[-1][0],
                                 size=float(np.median([q[3] for q in t]))))
print('tracks %d, fitted within %.1f px: %d' % (len(T), MAXRMS, len(R)))
# cluster: phase = round(f0) mod 20, speed to the 0.2 grid
H = {}
for r in R:
    key = (int(round(r['f0'])) % 20, round((r['v'] - 0.6) / 0.2))
    H.setdefault(key, []).append(r)
parts = sorted(H.items(), key=lambda kv: -len(kv[1]))
print('clusters (phase mod 20, speed index -> v): restarts seen')
for (ph, vi), rs in parts[:30]:
    print('  phase %2d  v %.1f : %3d restarts  (f0 residual mod 20: %s)' % (ph, 0.6 + 0.2 * vi, len(rs),
          ' '.join('%+.1f' % (r['f0'] - round(r['f0'])) for r in rs[:10])))
json.dump(dict(cam=cam, restarts=R, clusters=[dict(phase=ph, vi=vi, n=len(rs)) for (ph, vi), rs in parts]), open(OUT, 'w'))
