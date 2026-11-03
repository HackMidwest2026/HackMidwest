"""Matched-filter front end for Final Bowser's aura stars on a 1280x720 capture (README section 8).

Stages (each a function; aura_table.py drives them):
  prep()        capture stretch -> game frames by content (a capture frame is new when its mean |diff| > 1.2 in the
                play area; the 2-3 capture copies of one game frame are averaged), cropped to the aura's region;
  background()  per game frame a background = per-pixel median of the K most similar other game frames (similarity on
                a 3x-subsampled crop of Bowser, trimmed mean |diff|, frames within 3 of the frame excluded). Bowser's
                idle animation and Star Rod colour cycle repeat (about 36 game frames), so similar frames have the same
                pose and colour phase and the stars, which move, drop out of the median. A per-pixel noise sigma is the
                MAD of (frame - background) over the stretch (high where the blue flames flicker);
  templates()   emulator sprite coverage (aura_tmpl.py) -> capture scale (same projection scale as the star path),
                rotated in ROT-degree bins (5-fold symmetric: 0..72), blurred by the capture PSF (S-Video luma low-pass
                plus the GV-USB2/OBS rescale, Gaussian sigma SIGX x SIGY capture px);
  frame_maps()  per game frame, per size class and rotation bin, the matched-filter numerator
                  N(p) = sum_x c(x - p) R(x) (W - B(x)) / sigma(x)^2
                and per size the energy D(p) = sum_x c(x - p)^2 (W - B(x))^2 / sigma(x)^2 (rotation-averaged c^2):
                the log-likelihood ratio of a star with alpha a at p is a N - a^2 D / 2 (Gaussian noise, star = alpha
                blend of white W over the background B, which is how the game draws it).
Coordinates: crop px (x0, y0 = crop origin in the capture). The star model (decomp energy_in_out_update, type 4):
on render frame f0 + t of a star restarted (drawn) on frame f0: radius 10 + v (t + 1) units, angle A - 2 (t + 1) deg
(counter-clockwise, 0 = right), sprite rotated by the same angle, alpha sin(9 t deg)."""
import os, sys, math, subprocess
import numpy as np
from scipy import ndimage, fft as sfft

HERE = os.path.dirname(os.path.abspath(__file__))
X0, Y0, CW, CH = 700, 0, 580, 700          # crop of the 1280x720 capture (the aura's region in this OBS layout)
SIZES = (1.0, 0.7, 0.4)
ROT = 4                                    # rotation bin, deg (templates for 0, 4, .. 68)
NROT = 72 // ROT
EMU_K = (5.203, 5.245)                     # emulator route camera, capture px per unit (RAM projection, 1.594 / 1.580 x 3.264 / 3.32)
CAM_SH, CAM_H = 0.114, -4.9e-4             # route camera shear (capture px per unit of local y) and perspective (per unit of local y)
EMU_PX = (3.264 / 2, 3.32 / 2)             # capture px per glide64 2x px
LUMA = np.array([.2126, .7152, .0722], np.float32)


def luma(a):
    return a[..., 0] * LUMA[0] + a[..., 1] * LUMA[1] + a[..., 2] * LUMA[2]


# ------------------------------------------------------------------ game frames
def read_capture(clip, t0, t1, crop=(X0, Y0, CW, CH)):
    x0, y0, w, h = crop
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', clip, '-vf',
                        'crop=%d:%d:%d:%d' % (w, h, x0, y0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, h, w, 3)


def keyframes(clip, t0, fps=60.0):
    """capture-frame indices (relative to t0) of the encoder's keyframes: a keyframe re-encodes a duplicate copy of a
    game frame differently enough (mean |diff| about 1.5) to look like a new game frame"""
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=key_frame',
                          '-of', 'csv=p=0', clip], capture_output=True, check=True, text=True).stdout.split()
    o = int(round(t0 * fps))
    return set(i - o for i, k in enumerate(out) if k.strip().startswith('1'))


def game_frames(A, thr=1.2, kf=()):
    """A: capture frames (n,h,w,3) uint8 -> (G float16 averaged game frames, list of (first capture idx, copies)).
    A keyframe that would start a new game frame is taken as a copy of the previous one when that game frame has a
    single copy so far, or when its diff is below 0.7 x the median diff of the nearby new game frames."""
    d = [99.0] + [float(np.abs(A[i, 150:690:2, ::2].astype(np.int16) - A[i - 1, 150:690:2, ::2]).mean()) for i in range(1, len(A))]
    new = [i for i in range(len(A)) if d[i] > thr]
    for i in sorted(kf):
        if i in new and new.index(i) > 0:
            j = new.index(i); prev = new[j - 1]
            near = [d[q] for q in new if q != i and abs(q - i) <= 12]
            if i - prev == 1 or (near and d[i] < 0.7 * np.median(near)):
                new.remove(i)
    G = []; idx = []
    for k, i in enumerate(new):
        j = new[k + 1] if k + 1 < len(new) else len(A)
        G.append(A[i:j].astype(np.float32).mean(0).astype(np.float16)); idx.append((i, j - i))
    return np.stack(G), idx, d


def prep(clip, t0, t1, pre):
    A = read_capture(clip, t0, t1)
    G, idx, d = game_frames(A, kf=keyframes(clip, t0))
    del A
    np.save(pre + '_G.npy', G); np.save(pre + '_gidx.npy', np.array(idx))
    return G, idx


# ------------------------------------------------------------------ background
def background(G, K=12, excl=3, box=(150, 560, 100, 540)):
    """kNN-median background (float16, like G) and the per-pixel noise sigma (float32)"""
    n = len(G)
    y0, y1, x0, x1 = box
    D = np.stack([G[k, y0:y1:3, x0:x1:3].astype(np.float32) for k in range(n)]).reshape(n, -1)
    q = int(D.shape[1] * 0.9)
    dist = np.zeros((n, n), np.float32)
    for i in range(n):
        a = np.abs(D - D[i]); dist[i] = np.partition(a, q, 1)[:, :q].mean(1)
    del D
    L = np.stack([luma(G[k].astype(np.float32)) for k in range(n)]).astype(np.float16)
    B = np.empty_like(L); nbrs = []
    for k in range(n):
        dd = dist[k].copy(); dd[max(0, k - excl):k + excl + 1] = 1e9
        nb = np.argsort(dd)[:K]; nbrs.append(nb)
        B[k] = np.median(L[nb].astype(np.float32), 0)
    # noise: MAD of the residual over time (every 2nd frame, to save memory)
    R = np.stack([(L[k].astype(np.float32) - B[k]) for k in range(0, n, 2)])
    sig = 1.4826 * np.median(np.abs(R), 0)
    sig = np.maximum(ndimage.maximum_filter(sig, 5), 2.0).astype(np.float32)
    return L, B, sig, np.array(nbrs), dist


# ------------------------------------------------------------------ templates
def load_cov(path=None):
    z = np.load(path or os.path.join(HERE, 'aura_tmpl.npz'))
    return {s: z['cov_%.1f' % s] for s in SIZES}


def load_off(path=None):
    """sprite centroid offset from the model point per size, (radial, tangential) units (aura_tmpl.py)"""
    z = np.load(path or os.path.join(HERE, 'aura_tmpl.npz'))
    return {s: tuple(z['off_%.1f' % s]) for s in SIZES}


OFF = load_off()


def templates(cov, kx, ky, sigx=1.4, sigy=1.2, half=24):
    """capture-scale templates T[s][rbin] (2 half + 1 square, centre = model point) and the rotation-averaged squared
    template T2[s]. Scale: the sprite lives in the same billboard plane as the path, so it scales with the fitted kx, ky
    against the emulator camera. Each template is made zero-mean over a disk around the sprite (radius: the sprite's
    outer radius + 4 px), i.e. orthogonal to a uniform blob there: a broad bright patch (colour-flash edge, menu
    bubble) gives no response, only the outline shape does."""
    sx = EMU_PX[0] * kx / EMU_K[0]; sy = EMU_PX[1] * ky / EMU_K[1]
    T, T2 = {}, {}
    W = 2 * half + 1
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float64) - half
    for s in SIZES:
        c = cov[s]; h0 = (c.shape[0] - 1) / 2.0
        T[s] = []
        for rb in range(NROT):
            r = ndimage.rotate(c, rb * ROT, reshape=False, order=1)     # screen angle rb*ROT (ccw)
            m = ndimage.map_coordinates(r, [yy / sy + h0, xx / sx + h0], order=1, cval=0.0)
            m = ndimage.gaussian_filter(m, (sigy, sigx))
            rr = np.hypot(xx, yy)
            rad = rr[m > 0.15 * m.max()].max() + 4
            d = rr <= rad
            m = np.where(d, m - m[d].mean(), 0.0)
            T[s].append(m.astype(np.float32))
        T2[s] = np.mean([t ** 2 for t in T[s]], 0).astype(np.float32)
    return T, T2


def local_sigma(R, sig, win=11, step=4):
    """per-frame noise floor: robust scale of the residual in win*step px windows (stars cover a small fraction of
    a window, so they do not raise it; a region where the background model failed does)"""
    a = np.abs(R[::step, ::step])
    med = ndimage.median_filter(a, size=win, mode='nearest') * 1.4826
    up = ndimage.zoom(med, step, order=1)[:R.shape[0], :R.shape[1]]
    pad = np.zeros_like(R); pad[:up.shape[0], :up.shape[1]] = up
    return np.maximum(sig, pad)


# ------------------------------------------------------------------ matched filter
class MF:
    """FFT correlation of one frame's weighted residual with every template"""
    def __init__(self, T, T2, shape):
        self.shape = shape
        H, W = shape
        self.half = T[SIZES[0]][0].shape[0] // 2
        self.fs = (H + 2 * self.half + 1, W + 2 * self.half + 1)
        self.FT = {s: [np.conj(sfft.rfft2(t, self.fs)) for t in T[s]] for s in SIZES}
        self.FT2 = {s: np.conj(sfft.rfft2(T2[s], self.fs)) for s in SIZES}
        self.scale = 1.0          # noise scale (spatially correlated capture noise), set by calibrate()

    def calibrate(self, R, B, sig, white, n=4000, seed=0):
        """set self.scale so the SNR N / sqrt(D) at random positions has robust std 1 (null calibration)"""
        self.scale = 1.0
        N, D = self.maps(R, B, sig, white)
        rng = np.random.default_rng(seed); H, W = self.shape
        ys = rng.integers(30, H - 30, n); xs = rng.integers(30, W - 30, n); rb = rng.integers(0, NROT, n)
        z = N[1.0][rb, ys, xs] / np.sqrt(np.maximum(D[1.0][ys, xs], 1e-6))
        self.scale = float(1.4826 * np.median(np.abs(z - np.median(z))))
        return self.scale

    def corr(self, img, Ft):
        """out(p) = sum_x t(x - p + half) img(x), for p over the image"""
        r = sfft.irfft2(sfft.rfft2(img, self.fs) * Ft, self.fs, workers=4)
        return r

    def maps(self, R, B, sig, white):
        """N[s] (NROT, H, W), D[s] (H, W)"""
        H, W = self.shape; h = self.half
        w = np.maximum(white - B, 0.0)
        sig = local_sigma(R, sig) * self.scale
        Q = (R * w / sig ** 2).astype(np.float32); P = (w ** 2 / sig ** 2).astype(np.float32)
        FQ = sfft.rfft2(Q, self.fs, workers=4); FP = sfft.rfft2(P, self.fs, workers=4)
        N, D = {}, {}
        for s in SIZES:
            N[s] = np.stack([self._cut(sfft.irfft2(FQ * Ft, self.fs, workers=4)) for Ft in self.FT[s]])
            D[s] = self._cut(sfft.irfft2(FP * self.FT2[s], self.fs, workers=4))
        return N, D

    def _cut(self, r):
        # correlation via conj(FT(t)) gives out[p] = sum_x img(x) t(x - p) with t indexed from 0; template centre at
        # half -> value for a star centred at p is out[p - half] (circular)
        H, W = self.shape; h = self.half
        return np.roll(r, (h, h), (0, 1))[:H, :W].astype(np.float32)


def sample(M, x, y):
    """bilinear sample of M (..., H, W) at float arrays x, y (crop px); outside -> 0"""
    H, W = M.shape[-2:]
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < W - 1) & (y0 < H - 1)
    x0 = np.clip(x0, 0, W - 2); y0 = np.clip(y0, 0, H - 2)
    v = (M[..., y0, x0] * (1 - fx) * (1 - fy) + M[..., y0, x0 + 1] * fx * (1 - fy) +
         M[..., y0 + 1, x0] * (1 - fx) * fy + M[..., y0 + 1, x0 + 1] * fx * fy)
    return np.where(ok, v, 0.0)


def star_xy(cam, A, v, t, size=None):
    """crop-px position of the sprite centre of a star restarted with draw A, speed v, t frames after its restart frame
    (size given: the sprite's own offset from the model point is added). cam = (cx, cy, kx, ky[, sh, h]): the aura's
    plane maps to the screen by a homography; with local X (right) and Y (up) in units,
      x = cx + (kx X + sh Y) / (1 + h Y),  y = cy - ky Y / (1 + h Y)
    (exact for the emulator's route camera: rms 0.000 px on 200 frames of RAM positions, sh 0.114, h -4.9e-4)"""
    cx, cy, kx, ky = cam[:4]
    sh, h = (cam[4], cam[5]) if len(cam) > 4 else (CAM_SH, CAM_H)
    th = np.radians(A - 2.0 * (t + 1)); r = 10.0 + v * (t + 1)
    o_r, o_t = OFF[size] if size is not None else (0.0, 0.0)
    r = r + o_r
    X = r * np.cos(th) - o_t * np.sin(th); Y = r * np.sin(th) + o_t * np.cos(th)
    w = 1.0 + h * Y
    return cx - X0 + (kx * X + sh * Y) / w, cy - Y0 - ky * Y / w, np.degrees(th)


def alpha(t):
    return np.sin(np.radians(9.0 * np.asarray(t, float)))


def peaks(N, D, thr=6.0, sizes=SIZES, sep=8):
    """local maxima of the matched-filter SNR (N / sqrt(D), max over rotation bins and the given sizes):
    list of (x, y, snr, size, rotation deg) in crop px"""
    best = None
    for s in sizes:
        snr = N[s] / np.sqrt(np.maximum(D[s], 1e-3))
        rb = np.argmax(snr, 0); m = np.take_along_axis(snr, rb[None], 0)[0]
        if best is None: best = [m, np.full(m.shape, s), rb]
        else:
            u = m > best[0]; best[0] = np.where(u, m, best[0]); best[1] = np.where(u, s, best[1]); best[2] = np.where(u, rb, best[2])
    m = best[0]
    mx = ndimage.maximum_filter(m, 2 * sep + 1)
    ys, xs = np.nonzero((m == mx) & (m > thr))
    return [(float(x), float(y), float(m[y, x]), float(best[1][y, x]), float(best[2][y, x] * ROT)) for y, x in zip(ys, xs)]
