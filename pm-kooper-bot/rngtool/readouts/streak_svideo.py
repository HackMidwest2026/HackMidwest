"""Angle precision of one energy_in_out streak through S-Video -> GV-USB2, and the bits it gives about the
rand_int(359) that set it. Streak model (measured on glide64 frames of Charge / Spiny Flip): a 1 px wide line,
L px long (320x240 space), at radius RHO from a known centre, colour (255,245,200)*alpha over a dark blue bg.
Angle is fitted by a template search over 0..359 deg (with the centre uncertain by +-CE px).
bits = log2(360) - H(posterior on the 360 integer angles), averaged over random true angles."""
import sys, math
import numpy as np
from shimmer_svideo import svid
def streak(theta, L, rho, alpha, cx, cy, H=40, W=40, ss=4):
    img = np.zeros((H, W, 3)); img[:] = (0.05, 0.05, 0.25)
    yy, xx = np.mgrid[0:H * ss, 0:W * ss] / ss
    t = math.radians(theta); dx, dy = math.cos(t), -math.sin(t)
    px, py = xx - cx, yy - cy
    along = px * dx + py * dy; perp = np.abs(-px * dy + py * dx)
    m = ((along >= rho) & (along <= rho + L) & (perp <= 0.5)).astype(float)
    cov = m.reshape(H, ss, W, ss).mean((1, 3)) * alpha
    col = np.array((1.0, 0.96, 0.78))
    return img * (1 - cov[..., None]) + col * cov[..., None]
def run(L, rho, alpha, bw=1.3, ny=2.0, nc=3.0, CE=0.5, n=12, seed=1):
    rng = np.random.default_rng(seed); out = []
    angs = np.arange(360)
    for k in range(n):
        th = rng.uniform(0, 360); cx, cy = 20 + rng.uniform(-.5, .5), 20 + rng.uniform(-.5, .5)
        Yo, Uo, Vo = svid(streak(th, L, rho, alpha, cx, cy), bw, rng, ny, nc)
        ll = []
        for a in angs:
            best = -1e18
            for ox in (-CE, 0, CE):
                for oy in (-CE, 0, CE):
                    Yc, Uc, Vc = svid(streak(a, L, rho, alpha, 20 + ox, 20 + oy), bw)
                    d = ((Yc - Yo) ** 2).sum() / ny ** 2 + ((Uc - Uo) ** 2).sum() / nc ** 2 + ((Vc - Vo) ** 2).sum() / nc ** 2
                    best = max(best, -0.5 * d)
            ll.append(best)
        ll = np.array(ll); ll -= ll.max(); p = np.exp(ll); p /= p.sum()
        H = -(p[p > 1e-300] * np.log2(p[p > 1e-300])).sum(); out.append(math.log2(360) - H)
    return np.mean(out), np.min(out)
if __name__ == '__main__':
    for L, rho, alpha in ((4, 8, 0.5), (6, 10, 0.5), (6, 10, 1.0), (8, 14, 0.7), (4, 8, 0.25)):
        m, mn = run(L, rho, alpha)
        print('streak L %d px rho %d px alpha %.2f: %.2f bits mean (min %.2f) of 8.49' % (L, rho, alpha, m, mn))
