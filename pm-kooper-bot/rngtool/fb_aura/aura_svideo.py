"""How many bits of each aura rand_int(359) survive S-Video -> GV-USB2 (simulation, same capture model as
readouts/shimmer_svideo.py: 4.2 MHz luma, 1.3 MHz chroma, 720x480 sampling, noise Y 2 / C 3 levels, 8-bit rounding).

Star model (fitted to glide64 renders by aura_geom.py, see README): the star restarted with angle A (= the draw) is at
frame t (t = 1..19 after the restart) at screen angle A - 2t (counter-clockwise, 0 = right), radius
k * (10 + v*t) local units from the aura centre (232.0, 117.3) in 320x240 px, k = 1.70 px/unit horizontally and
1.61 vertically, with alpha sin(9 t deg); the sprite is a 5-pointed star outline, outer radius 5 px x size class
(1.0 / 0.7 / 0.4), rotated with the angle, colour (255, 250, 220), alpha-blended over the measured background frame
(bg_menu_320.png: the phase-2 battle menu with every star hidden, glide64).
The page's model is assumed exact except the aura centre (unknown to +-0.5 px). Other stars are not drawn (overlap
is discussed in the README). bits = log2(360) - H(posterior over the 360 integer draws), using every frame of the
star's 19-frame life.
usage: python3 aura_svideo.py [n_trials]"""
import sys, math, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'readouts'))
from shimmer_svideo import svid

HERE = os.path.dirname(os.path.abspath(__file__))
BG = np.asarray(Image.open(os.path.join(HERE, 'bg_menu_320.png')).convert('RGB')).astype(float) / 255.0
CX, CY, KX, KY = 232.0, 117.3, 1.70, 1.61
COL = np.array((1.0, 0.98, 0.86))
BOX = 14            # half-size of the evaluation window around a star (320 px)


def star_mask(cx, cy, R, rot, x0, y0, W, ss=4):
    """coverage (0..1) of a 1 px wide 5-point star outline centred (cx, cy), in a W x W window at (x0, y0)"""
    yy, xx = (np.mgrid[0:W * ss, 0:W * ss] + 0.5) / ss
    xx = xx + x0 - cx; yy = yy + y0 - cy
    pts = []
    for j in range(10):
        a = math.radians(rot + 90 + 36 * j); rr = R if j % 2 == 0 else R * 0.45
        pts.append((rr * math.cos(a), -rr * math.sin(a)))
    d = np.full(xx.shape, 1e9)
    for j in range(10):
        (ax, ay), (bx, by) = pts[j], pts[(j + 1) % 10]
        ex, ey = bx - ax, by - ay; L2 = ex * ex + ey * ey
        tt = np.clip(((xx - ax) * ex + (yy - ay) * ey) / L2, 0, 1)
        d = np.minimum(d, np.hypot(xx - ax - tt * ex, yy - ay - tt * ey))
    m = (d <= 0.5).astype(float)
    return m.reshape(W, ss, W, ss).mean((1, 3))


def star_pos(A, t, v, ox=0.0, oy=0.0):
    th = math.radians(A - 2 * t); r = 10 + v * t
    return CX + ox + KX * r * math.cos(th), CY + oy - KY * r * math.sin(th)


def window(A, t, v, size, x0, y0, W, ox=0.0, oy=0.0):
    img = BG[y0:y0 + W, x0:x0 + W].copy()
    cx, cy = star_pos(A, t, v, ox, oy)
    a = math.sin(math.radians(9 * t))
    m = star_mask(cx, cy, 5 * size, A - 2 * t, x0, y0, W) * a
    return img * (1 - m[..., None]) + COL * m[..., None]


def bits_one(A, v, size, rng, span=12):
    """posterior over integer draws A' in A +- span (farther ones put the star 10+ px away: no mass), centre +-0.5 px"""
    W = 2 * BOX
    ll = {a: -1e18 for a in range(A - span, A + span + 1)}
    obs = {}
    for t in range(1, 20):
        sx, sy = star_pos(A, t, v)
        x0, y0 = int(sx) - BOX, int(sy) - BOX
        if x0 < 0 or y0 < 0 or x0 + W > 320 or y0 + W > 240: continue
        obs[t] = (x0, y0, svid(window(A, t, v, size, x0, y0, W), 1.3, rng, 2.0, 3.0))
    for a in ll:
        for ox in (-0.5, 0, 0.5):
            for oy in (-0.5, 0, 0.5):
                tot = 0.0
                for t, (x0, y0, (Yo, Uo, Vo)) in obs.items():
                    Yc, Uc, Vc = svid(window(a, t, v, size, x0, y0, W, ox, oy), 1.3)
                    tot += ((Yc - Yo) ** 2).sum() / 4.0 + ((Uc - Uo) ** 2).sum() / 9.0 + ((Vc - Vo) ** 2).sum() / 9.0
                ll[a] = max(ll[a], -0.5 * tot)
    L = np.array(list(ll.values())); L -= L.max(); p = np.exp(L); p /= p.sum()
    H = -(p[p > 1e-300] * np.log2(p[p > 1e-300])).sum()
    return math.log2(360) - H, list(ll)[int(np.argmax(L))] == A


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rng = np.random.default_rng(5)
    print('angle region      size  v    bits (mean, min of %d)  argmax exact' % n)
    for label, angs in (('sky (30-150 deg)', (40, 75, 110, 140)), ('over Bowser (180-330)', (200, 240, 280, 320))):
        for size in (1.0, 0.7, 0.4):
            for v in (0.6, 2.6):
                res = [bits_one(angs[k % len(angs)] + int(rng.integers(0, 5)), v, size, rng) for k in range(n)]
                b = [r[0] for r in res]
                print('%-22s %.1f  %.1f  %.2f  %.2f  %d/%d' % (label, size, v, np.mean(b), np.min(b), sum(r[1] for r in res), n), flush=True)
