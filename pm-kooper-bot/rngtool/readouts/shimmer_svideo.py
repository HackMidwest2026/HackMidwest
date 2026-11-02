"""How many bits of gRandSeed one star-power shimmer gives through S-Video -> GV-USB2 (720x480).
Render model from the display list in JP RAM (0x80109640 texture, DL decoded in README):
  2-cycle: COMB = PRIM + (TEX0_I - 127)*127/255 (clamped); C = SHADE_A*COMB + (1-SHADE_A)*255 (shade is white,
  shade alpha 1 at the particle centre, 0 at the diamond tips); alpha = (TEX_A - SHADE_A)*TEX_A + SHADE_A;
  framebuffer = alpha*C + (1-alpha)*bg. Texture: 32x16 IA8 4-point star (shimmer_tex.txt), mirrored to 32x32,
  spanning ~5.5*scale px (320x240), measured on glide64 frames. NOT verified on an accurate RDP (see README).
Positions/scales are fixed (shimmer_geom.tracks); only PRIM (128+r, 128+g, 128+b) is random.
S-Video: 320->720 resample, line doubling, luma Gaussian low-pass 4.2 MHz, chroma low-pass BW MHz, noise, 8-bit.
For each readable particle (best frame), every candidate (r,g,b) on a STEP grid is scored on a local window with
the other particles held at their true colours (sequential decoding, slightly optimistic); bits = prior entropy
of the grid minus posterior entropy (capped by the grid: STEP=4 -> at most ~10.5 bits/particle).
usage: STEP=4 NP=56 python3 shimmer_svideo.py [BW_MHz] [luma_noise] [chroma_noise] [trials] [gain]"""
import sys, math, random
import numpy as np
from shimmer_geom import tracks, readable
HERE = __file__.rsplit('/', 1)[0] if '/' in __file__ else '.'
def load_tex():
    t = np.array([[int(v, 16) for v in l.split()] for l in open(HERE + '/shimmer_tex.txt') if l.strip()], dtype=float)
    t = np.vstack([t, t[::-1]])
    return (t // 16) * 17 / 255.0, (t % 16) * 17 / 255.0
TI, TA = load_tex()
def layer(x, y, sc):
    half, dr = 2.75 * sc, 5.0 * sc
    px = np.arange(int(math.floor(x - half)), int(math.ceil(x + half)) + 1)
    py = np.arange(int(math.floor(y - half)), int(math.ceil(y + half)) + 1)
    PX, PY = np.meshgrid(px, py)
    u = (PX + 0.5 - x) / (2 * half) + 0.5; v = (PY + 0.5 - y) / (2 * half) + 0.5
    m = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    ti = np.clip((v * 32).astype(int), 0, 31); tj = np.clip((u * 32).astype(int), 0, 31)
    I = np.where(m, TI[ti, tj], 0); A = np.where(m, TA[ti, tj], 0)
    sa = np.clip(1 - (np.abs(PX + 0.5 - x) + np.abs(PY + 0.5 - y)) / dr, 0, 1) * m
    a = (A - sa) * A + sa
    return PX, PY, I, sa, a
def draw(fb, L, prim):
    """fb (...,H,W,3) float; prim (...,3) -> draws particle layer L in place (broadcast over leading dims)."""
    PX, PY, I, sa, a = L
    ok = (PX >= 0) & (PX < fb.shape[-2]) & (PY >= 0) & (PY < fb.shape[-3]) & (a > 0)
    ys, xs = PY[ok], PX[ok]; I, sa, a = I[ok], sa[ok], a[ok]
    p = prim[..., None, :]                                                  # (...,1,3)
    comb = np.clip(p + ((I - 127 / 255.0) * 127 / 255.0)[:, None], 0, 1)
    c = sa[:, None] * comb + (1 - sa[:, None])
    fb[..., ys, xs, :] = a[:, None] * c + (1 - a[:, None]) * fb[..., ys, xs, :]
def gk(sig):
    r = max(1, int(3 * sig)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); return k / k.sum()
def lp(ch, mhz):
    k = gk(13.5 / (2 * math.pi * mhz)); pad = len(k) // 2
    chp = np.pad(ch, [(0, 0)] * (ch.ndim - 1) + [(pad, pad)], mode='edge')
    out = np.zeros_like(ch)
    for i, w in enumerate(k): out += w * chp[..., i:i + ch.shape[-1]]
    return out
def svid(win, bw, rng=None, ny=2.0, nc=3.0, gain=1.0):
    """win (...,h,w,3) in 320 px -> (...,2h, 2.25w) YUV (720x480 scale)."""
    h, w = win.shape[-3], win.shape[-2]; W2 = int(round(w * 2.25))
    xs = np.linspace(0, w - 1, W2); j0 = np.floor(xs).astype(int); j1 = np.minimum(j0 + 1, w - 1); f = xs - j0
    img = win[..., :, j0, :] * (1 - f)[:, None] + win[..., :, j1, :] * f[:, None]
    img = np.repeat(img, 2, axis=-3) * 255
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B; U = (B - Y) * 0.564; V = (R - Y) * 0.713
    Y, U, V = lp(Y, 4.2), lp(U, bw), lp(V, bw)
    if rng is not None:
        Y = Y + rng.normal(0, ny, Y.shape); U = U + rng.normal(0, nc, U.shape); V = V + rng.normal(0, nc, V.shape)
    Y = np.clip((Y - 16) * gain + 16, 0, 255); U = np.clip(U * gain, -128, 127); V = np.clip(V * gain, -128, 127)
    if rng is not None: Y, U, V = np.round(Y), np.round(U), np.round(V)
    return Y, U, V
def main():
    bw = float(sys.argv[1]) if len(sys.argv) > 1 else 1.3
    ny = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    nc = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    ntr = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    gain = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    ex, ey = 52, 46
    T = tracks(ex, ey); rd = readable(ex, ey)
    bg = np.zeros((240, 320, 3)); bg[:, :] = (0.05, 0.05, 0.15); bg[18:50, 12:200] = (0.75, 0.63, 0.31)
    import os
    STEP = int(os.environ.get('STEP', 4)); NP = int(os.environ.get('NP', 56))
    C = np.array([(r, g, b) for r in range(0, 128, STEP) for g in range(0, 128 - r, STEP) for b in range(0, 128 - r - g, STEP)], float)
    Hprior = math.log2(len(C))
    rng = np.random.default_rng(7); R = random.Random(3)
    tots = []
    for t in range(ntr):
        raw = []
        for j in range(56):
            r = R.randint(0, 127); g = R.randint(0, 127 - r); b = R.randint(0, 127 - r - g); raw.append((r, g, b))
        prim = (128 + np.array(raw, float)) / 255.0
        layers = {}
        per = []
        for j, (k, rad) in sorted(rd.items())[:NP]:
            fb = bg.copy()
            for i in range(56):
                x, y, sc = T[i][k]
                if i != j: draw(fb, layer(x, y, sc), prim[i])
            x, y, sc = T[j][k]; L = layer(x, y, sc)
            m = int(6 * sc) + 6
            y0, y1, x0, x1 = max(0, int(y) - m), min(240, int(y) + m), max(0, int(x) - m), min(320, int(x) + m)
            Lw = (L[0] - x0, L[1] - y0) + L[2:]
            base = fb[y0:y1, x0:x1]
            tw = base.copy(); draw(tw, Lw, prim[j]); Yo, Uo, Vo = svid(tw, bw, rng, ny, nc, gain)
            cw = np.repeat(base[None], len(C), 0); draw(cw, Lw, (128 + C) / 255.0)
            Yc, Uc, Vc = svid(cw, bw, None, ny, nc, gain)
            d = (((Yc - Yo) ** 2).sum((-1, -2)) / ny ** 2 + ((Uc - Uo) ** 2).sum((-1, -2)) / nc ** 2 + ((Vc - Vo) ** 2).sum((-1, -2)) / nc ** 2)
            ll = -0.5 * d; ll -= ll.max(); p = np.exp(ll); p /= p.sum()
            H = -(p[p > 1e-300] * np.log2(p[p > 1e-300])).sum()
            per.append(Hprior - H)
        tots.append(sum(per))
        print('BW %.1f MHz noise Y%.1f C%.1f gain %.1f trial %d: %d particles, total %.0f bits, mean %.2f, min %.2f, max %.2f (grid cap %.1f)' % (
            bw, ny, nc, gain, t, len(per), sum(per), np.mean(per), np.min(per), np.max(per), Hprior))
if __name__ == '__main__':
    main()
