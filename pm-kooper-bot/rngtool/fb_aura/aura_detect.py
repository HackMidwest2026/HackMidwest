"""Star detector for Final Bowser's aura on a real capture (1280x720, 60 fps, S-Video -> GV-USB2), still-camera stretch.
1. Game frames: the game draws at 30 fps; a capture frame is a new game frame when it differs from the previous one
   (mean |diff| > 0.5 in the play area). Cadence slips are handled because frames are found by content.
2. Blobs: luma at least TH above the per-pixel temporal median of the stretch and bluish-white (B >= 150), right of
   x = XMIN; connected components (dilated 2 px) of 12..900 px.
3. Tracks: blobs linked frame to frame (step 2..18 px, nearest).
4. Fit, all tracks at once (the aura model, README section 3): a star restarted on game frame f0 with draw A is at
   frame f at angle A - 2 (f - f0 + 1) deg (counter-clockwise) and radius 10 + v (f - f0 + 1) units from one common
   centre (cx, cy), with kx, ky capture px per unit. Unknowns: cx, cy, kx, ky, and per track f0 (real), A, v.
   Tracks with a large residual are dropped and the fit repeated.
Output: JSON with the game frames' capture indices and the per-track fit (restart frame, draw angle, speed, residual).
usage: python3 aura_detect.py CLIP START_S N_CAPTURE_FRAMES OUT.json [XMIN=650] [TH=45]"""
import sys, os, math, json, subprocess, tempfile, shutil
import numpy as np
from PIL import Image
from scipy import ndimage, optimize


def game_frames(clip, start, n, tmp):
    subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(start), '-i', clip, '-frames:v', str(n), os.path.join(tmp, 'g%04d.png')], check=True)
    F = []; idx = []
    prev = None
    for i in range(1, n + 1):
        p = os.path.join(tmp, 'g%04d.png' % i)
        if not os.path.exists(p): break
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.int16)
        if prev is None or np.abs(a - prev)[150:700, 320:1270].mean() > 0.5:
            F.append(a); idx.append(i - 1)
        prev = a
    return F, idx


def segments(F, jump=20.0):
    """split at screen changes (menu boxes, target highlight): mean |diff| > jump"""
    cut = [0] + [i for i in range(1, len(F)) if np.abs(F[i] - F[i - 1])[150:700, 320:1270].mean() > jump] + [len(F)]
    return [(a, b) for a, b in zip(cut, cut[1:]) if b > a]


def blobs(F, xmin, th):
    lum = lambda a: a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
    out = []
    for a, b in segments(F):
        med = np.median(np.stack([f.astype(float) for f in F[a:b]]), 0)
        for f in F[a:b]:
            out.append(blob1(f, med, lum, xmin, th))
    return out


def blob1(f, med, lum, xmin, th):
    if True:
        m = (lum(f) - lum(med) > th) & (f[..., 2] >= 150) & (f[..., 2] - med[..., 2] > 30)
        m[:140] = False; m[:, :xmin] = False; m[690:] = False
        lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
        if n == 0: return []
        cs = ndimage.center_of_mass(m, lab, range(1, n + 1)); sz = ndimage.sum(m, lab, range(1, n + 1))
        return [(c[1], c[0], int(s)) for c, s in zip(cs, sz) if 12 <= s <= 900]


def link(B, lo=2, hi=18):
    tracks = []
    for k, bl in enumerate(B):
        for x, y, s in bl:
            best = None
            for t in tracks:
                if t[-1][0] == k - 1:
                    d = math.dist(t[-1][1:3], (x, y))
                    if lo < d < hi and (best is None or d < best[0]): best = (d, t)
            if best: best[1].append((k, x, y, s))
            else: tracks.append([(k, x, y, s)])
    return tracks


def fit(T, init=None):
    def unpack(p):
        return p[:4], [p[4 + 3 * j: 7 + 3 * j] for j in range(len(T))]
    def res(p):
        (cx, cy, kx, ky), per = unpack(p); out = []
        for t, (f0, A, v) in zip(T, per):
            for k, x, y, s in t:
                n = k - f0 + 1; th = math.radians(A - 2 * n); r = 10 + v * n
                out += [cx + kx * r * math.cos(th) - x, cy - ky * r * math.sin(th) - y]
        return out
    best = None
    starts = [init] if init else [(cx, cy, 3.0, 3.0) for cx in (1000, 1080) for cy in (300, 380)]
    for cx0, cy0, kx0, ky0 in starts:
        p0 = [cx0, cy0, kx0, ky0]
        for t in T:
            k, x, y, s = t[0]
            r = math.hypot((x - cx0) / kx0, (y - cy0) / ky0); v0 = 1.6
            n0 = max(1.0, (r - 10) / v0)
            p0 += [k - n0 + 1, math.degrees(math.atan2(-(y - cy0) / ky0, (x - cx0) / kx0)) + 2 * n0, v0]
        s = optimize.least_squares(res, p0, loss='soft_l1', f_scale=3.0)
        if best is None or s.cost < best.cost: best = s
    (cx, cy, kx, ky), per = unpack(best.x)
    r = np.array(res(best.x)).reshape(-1, 2); i = 0; rows = []
    for t, (f0, A, v) in zip(T, per):
        rr = r[i:i + len(t)]; i += len(t)
        rows.append(dict(f0=float(f0), A=float(A % 360), v=float(v), n=len(t), rms=float(math.sqrt((rr ** 2).sum(1).mean())),
                         first=int(t[0][0]), size=float(np.median([q[3] for q in t])), pts=[(int(q[0]), round(q[1], 1), round(q[2], 1)) for q in t]))
    return dict(cx=cx, cy=cy, kx=kx, ky=ky), rows


if __name__ == '__main__':
    clip, start, n, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    xmin = int(sys.argv[5]) if len(sys.argv) > 5 else 650; th = float(sys.argv[6]) if len(sys.argv) > 6 else 45
    tmp = tempfile.mkdtemp(dir='/dev/shm')
    try:
        F, idx = game_frames(clip, start, n, tmp)
    finally:
        shutil.rmtree(tmp)
    B = blobs(F, xmin, th)
    T = [t for t in link(B) if len(t) >= 5]
    print('game frames', len(F), 'capture idx', idx[:6], '...; blobs/frame', [len(b) for b in B])
    print('tracks >= 5 frames:', len(T), 'segments', segments(F))
    cam, rows = fit(T)
    for it in range(3):
        keep = [t for t, r in zip(T, rows) if r['rms'] < 4.0]
        if len(keep) == len(T) or len(keep) < 4: break
        T = keep; cam, rows = fit(T, (cam['cx'], cam['cy'], cam['kx'], cam['ky']))
    print('camera fit: centre (%.1f, %.1f), kx %.2f ky %.2f px/unit; %d tracks' % (cam['cx'], cam['cy'], cam['kx'], cam['ky'], len(rows)))
    for r in sorted(rows, key=lambda r: r['f0']):
        print('  restart f0 %6.2f  A %6.1f  v %.2f  n %2d  rms %.2f  size %4.0f' % (r['f0'], r['A'], r['v'], r['n'], r['rms'], r['size']))
    json.dump(dict(start=start, idx=idx, cam=cam, tracks=rows, blobs=B), open(out, 'w'))


def load_crop(clip, t0, t1, x0=650, y0=100, w=630, h=600):
    """capture frames t0..t1 s, cropped, as uint8 (n, h, w, 3) via an ffmpeg raw pipe (no frame files)"""
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', clip,
                        '-vf', 'crop=%d:%d:%d:%d' % (w, h, x0, y0), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, h, w, 3)


def game_frames_arr(A):
    keep = [0]
    for i in range(1, len(A)):
        if np.abs(A[i].astype(np.int16) - A[i - 1]).mean() > 0.5: keep.append(i)
    return keep


def blobs_rolling(G, th=45, win=10, x0=650, y0=100):
    """blobs per game frame against a rolling per-pixel median (+-win game frames; Bowser's colour cycling is slow);
    coordinates returned in full-capture pixels"""
    L = (G[..., 0] * .299 + G[..., 1] * .587 + G[..., 2] * .114).astype(np.float32)
    Bl = G[..., 2].astype(np.float32)
    out = []
    for k in range(len(G)):
        a, b = max(0, k - win), min(len(G), k + win + 1)
        sl = list(range(a, b, 2)) if b - a > 12 else list(range(a, b))
        ml = np.median(L[sl], 0); mb = np.median(Bl[sl], 0)
        m = (L[k] - ml > th) & (Bl[k] >= 150) & (Bl[k] - mb > 30)
        m[:40] = False
        lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
        if n == 0: out.append([]); continue
        cs = ndimage.center_of_mass(m, lab, range(1, n + 1)); sz = ndimage.sum(m, lab, range(1, n + 1))
        out.append([(c[1] + x0, c[0] + y0, int(s)) for c, s in zip(cs, sz) if 12 <= s <= 900])
    return out


def bg_mask(G, sat=60, lumax=150, grow=6, x0=650, y0=100):
    """True where a star can be read: background neither saturated (Bowser's body, colour-cycling) nor bright,
    from the median of the stretch; grown by `grow` px around excluded areas"""
    med = np.median(G[::8].astype(np.float32), 0)
    s = med.max(2) - med.min(2); l = med @ np.array([.299, .587, .114], np.float32)
    bad = ndimage.binary_dilation((s > sat) | (l > lumax), iterations=grow)
    return ~bad


def filter_blobs(B, ok, x0=650, y0=100):
    out = []
    for fr in B:
        out.append([b for b in fr if 0 <= int(b[1]) - y0 < ok.shape[0] and 0 <= int(b[0]) - x0 < ok.shape[1] and ok[int(b[1]) - y0, int(b[0]) - x0]])
    return out
