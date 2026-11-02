"""Recover gRandSeed from the star-power shimmer (status_star_shimmer.c) in a real console capture of a Focus.

The shimmer is a 5-point star of 56 pastel diamonds that bursts out of the star-power bar on the first status-bar
update after add_star_power(). Every particle's colour is drawn in that one update, in particle order:
r = rand_int(127), g = rand_int(127 - r), b = rand_int(127 - r - g), prim = 128 + raw. Positions and scales are fixed.

Pipeline (numpy + ffmpeg only, plus the C brute force focus_search.c):
 1. decode ~40 frames from the onset as YUV (no RGB round trip); keep distinct game frames (drops 60 fps doubles and
    OBS repeats);
 2. fit the capture geometry (scale x/y, emitter position, which game frame is animTime 0) by correlating luma with
    the exact particle tracks (float32, as the game computes them);
 3. measure each particle's centre Y,U,V on the frames where its centre is clear of its neighbours (median over frames);
 4. seed-free colour calibration: centre colour = min(255, 192 + raw) per channel (the decoded combiner), then BT.709
    limited YCbCr, then a per-channel gain and offset chosen so the measured mean/variance over all particles match the
    model's prior mean/variance (no seed is used for this);
 5. brute force every 32-bit state before particle J0's draws (J0 = first measured particle) with a capped chi-square
    and prefix early rejection; walk the winner back to the state before particle 0;
 6. checks: a search on the first half of the particles only, and the held-out cost of the other half vs random seeds.

usage: python3 focus_seed.py CLIP --onset N [--out result.json]
  N = 1-based frame number (ffmpeg numbering) of the first capture frame that shows the shimmer star, +-2 is fine.
Tested on one real N64 -> S-Video -> GV-USB2 -> OBS 1280x720 60 fps clip (README, "Focus shimmer on hardware")."""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shimmer_geom import V, S, s8          # InitialVelocities and AnimatedScale tables

M32 = 0xFFFFFFFF
A_LCG, A_INV = 0x5D588B65, pow(0x5D588B65, -1, 1 << 32)
def adv(s): return (s * A_LCG + 1) & M32
def back(s): return ((s - 1) * A_INV) & M32
def rii(s, mx):
    d = M32 // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    mx = abs(mx)
    if mx == 0: return s, 0
    if mx == 1: s, v = rii(s, 1000); return s, int(v > 500)
    if mx == 100: s, v = rii(s, 1009); return s, v // 10
    return rii(s, mx)
def particles(s, n):
    out = []
    for _ in range(n):
        s, r = rand_int(s, 127); s, g = rand_int(s, 127 - r); s, b = rand_int(s, 127 - r - g); out.append((r, g, b))
    return out, s

# ---------------------------------------------------------------- geometry
def disp(k):
    """displacement from the emitter (320x240 space) of each particle at animTime k, float32 like the game"""
    out = []
    for vx, vy in V:
        x = y = np.float32(0); dx = np.float32(s8(vx) * 0.1); dy = np.float32(-s8(vy) * 0.1)
        for _ in range(k + 1):
            x = np.float32(x + dx); y = np.float32(y + dy); dx = np.float32(dx * 0.92); dy = np.float32(dy * 0.92)
        out.append((x, y))
    return np.array(out, dtype=np.float64)
D = [disp(k) for k in range(30)]
SCALE = [v * 0.04 for v in S]

def blur(img, s):
    r = int(3 * s); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    out = np.apply_along_axis(lambda m: np.convolve(m, k, 'same'), 0, img)
    return np.apply_along_axis(lambda m: np.convolve(m, k, 'same'), 1, out)

def read_frames(clip, first, count):
    """frames first..first+count-1 (1-based) as float32 (count, 3, H, W) YUV444 (limited range, as coded)"""
    w, h = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                             'stream=width,height', '-of', 'csv=p=0', clip]).decode().split(',')[:2])
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', clip, '-vf',
                                   "select='between(n\\,%d\\,%d)'" % (first - 1, first + count - 2), '-vsync', '0',
                                   '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-'])
    a = np.frombuffer(raw, np.uint8).reshape(-1, 3, h, w)
    return a.astype(np.float32)

def distinct(frames, first, thr=0.5):
    """indices (into frames) of distinct game frames: drop frames whose luma barely differs from the last kept one"""
    keep = [0]
    for i in range(1, len(frames)):
        if np.abs(frames[i][0] - frames[keep[-1]][0]).mean() > thr: keep.append(i)
    return keep

def shift_score(imgs, ax, ay, koff, BX, BY, step=1):
    tot = np.zeros((len(BY), len(BX))); cnt = np.zeros_like(tot)
    for k, img in imgs.items():
        if not 0 <= k + koff < 30: continue
        d = D[k + koff]
        for j in range(56):
            ys = (BY + ay * d[j, 1]) / step; xs = (BX + ax * d[j, 0]) / step
            ys = np.round(ys).astype(int); xs = np.round(xs).astype(int)
            vy = (ys >= 0) & (ys < img.shape[0]); vx = (xs >= 0) & (xs < img.shape[1])
            sub = np.zeros_like(tot); sub[np.ix_(vy, vx)] = img[np.ix_(ys[vy], xs[vx])]
            tot += sub; cnt += np.outer(vy, vx)
    return tot / np.maximum(cnt, 1), cnt

def fit_geometry(G):
    """G: list of distinct game frames (3,H,W) from the onset guess. Returns (ax, ay, bx, by, koff)."""
    H, W = G[0].shape[1:]
    small = {k: blur(G[k][0, ::2, ::2] - 16, 1.0) for k in (3, 5, 7) if k < len(G)}
    BX = np.arange(0, W, 4.0); BY = np.arange(0, H * 0.6, 4.0)
    best = None
    for koff in range(-2, 3):
        for sc in np.arange(2.0, 4.01, 0.1):
            s, c = shift_score(small, sc, sc, koff, BX, BY, step=2)
            s[c < 0.5 * c.max()] = -1e9
            i = np.unravel_index(np.argmax(s), s.shape)
            if best is None or s[i] > best[0]: best = (s[i], koff, sc, BX[i[1]], BY[i[0]])
    _, koff, sc, bx0, by0 = best
    full = {k: blur(G[k][0] - 16, 1.5) for k in range(2, min(14, len(G)))}
    best = None
    for kf in (koff - 1, koff, koff + 1):
        for ax in np.arange(sc - 0.3, sc + 0.31, 0.05):
            for ay in np.arange(sc - 0.3, sc + 0.31, 0.05):
                BX = np.arange(bx0 - 10, bx0 + 11); BY = np.arange(by0 - 10, by0 + 11)
                s, c = shift_score(full, ax, ay, kf, BX, BY)
                s[c < 0.5 * c.max()] = -1e9
                i = np.unravel_index(np.argmax(s), s.shape)
                if best is None or s[i] > best[0]: best = (s[i], kf, ax, ay, BX[i[1]], BY[i[0]])
    _, koff, ax, ay, bx, by = best
    return float(ax), float(ay), float(bx), float(by), int(koff)

# ---------------------------------------------------------------- colours
HALF = 2.75     # visible half-span of a particle per unit scale, 320 space (shimmer_svideo.layer)
def measure(G, geo, kmin=2, kmax=12, clear=0.9):
    ax, ay, bx, by, koff = geo
    per = {}
    for i in range(len(G)):
        k = i + koff
        if not kmin <= k <= kmax: continue
        f = G[i]; Yb = blur(f[0], 1.0); H, W = Yb.shape
        P = np.c_[bx + ax * D[k][:, 0], by + ay * D[k][:, 1]]; r = HALF * SCALE[k] * ax
        for j in range(56):
            x, y = P[j]
            if not (8 < x < W - 8 and 8 < y < H - 8): continue
            dd = np.hypot(P[:, 0] - x, P[:, 1] - y); dd[j] = 1e9
            if dd.min() / r <= clear: continue
            xi, yi = int(round(x)), int(round(y))
            win = Yb[yi - 4:yi + 5, xi - 4:xi + 5]; a = np.unravel_index(np.argmax(win), win.shape)
            yc, xc = yi - 4 + a[0], xi - 4 + a[1]
            per.setdefault(j, []).append(f[:, yc - 2:yc + 3, xc - 2:xc + 3].reshape(3, -1).mean(1))
    return {j: np.median(v, 0) for j, v in per.items() if len(v) >= 2}

RAW = np.array([(r, g, b) for r in range(128) for g in range(128 - r) for b in range(128 - r - g)], float)
PRIOR = np.array([1 / 128 / (128 - r) / (128 - r - g) for r, g, b in RAW]); PRIOR /= PRIOR.sum()
KY, KU, KV = 219 / 255, 224 / 255 / 1.8556, 224 / 255 / 1.5748
LUM = np.array([0.2126, 0.7152, 0.0722])
ROWS = np.array([KY * LUM, KU * (np.array([0, 0, 1]) - LUM), KV * (np.array([1, 0, 0]) - LUM)])
OFFS = np.array([16, 128, 128])
def centre_rgb(raw, base=192, sat=255): return np.minimum(sat, base + np.asarray(raw, float))

def calibrate(meas):
    """seed-free: per-channel gain/offset so the measured mean and variance match the model prior's"""
    Mm = np.array(list(meas.values()))
    P = centre_rgb(RAW) @ ROWS.T + OFFS
    pm = (PRIOR[:, None] * P).sum(0); pv = (PRIOR[:, None] * (P - pm) ** 2).sum(0)
    gain = np.sqrt(Mm.var(0) / pv)
    A = np.zeros((3, 4)); A[:, :3] = gain[:, None] * ROWS; A[:, 3] = Mm.mean(0) - gain * (pm - OFFS)
    return A, gain

def predict(A, raw): return np.r_[centre_rgb(raw), 1.0] @ A.T

# ---------------------------------------------------------------- search
def run_search(exe, A, sig, meas, use, cap=12.0, t0=6.0, ts=4.5, keep=10):
    J0 = min(use)
    lines = ['192 255 ' + ' '.join('%.6f' % v for v in A.ravel()) + ' %.3f %.3f %.3f %.1f %.1f %.2f' % (*sig, cap, t0, ts)]
    for j in sorted(meas): lines.append('%d %d %.3f %.3f %.3f' % (j, int(j in use), *meas[j]))
    p = subprocess.run([exe, str(J0), str(keep)], input='\n'.join(lines) + '\n', capture_output=True, text=True, check=True)
    res = [(int(a, 16), float(b)) for a, b in (l.split() for l in p.stdout.split('\n') if l.strip())]
    return J0, res

def backtrack(sJ, J0):
    """states s0 such that drawing particles 0..J0-1 from s0 ends exactly at sJ"""
    out = []
    s0 = sJ
    for n in range(1, 3 * J0 * 4 + 1):
        s0 = back(s0)
        if n < 3 * J0 - J0: continue
        _, e = particles(s0, J0)
        if e == sJ: out.append((s0, n))
    return out

def cost(A, sig, meas, sJ, js, cap=12.0):
    cols, _ = particles(sJ, 56)
    J0 = min(meas)
    t = 0.0
    for j in js:
        p = predict(A, cols[j - J0]); t += min(cap, (((meas[j] - p) / sig) ** 2).sum())
    return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('--onset', type=int, required=True)
    ap.add_argument('--sig', default='8,3.5,3.5', help='Y,U,V tolerance (levels) for the search')
    ap.add_argument('--out', default=None)
    ap.add_argument('--exe', default=os.path.join(tempfile.gettempdir(), 'focus_search'))
    a = ap.parse_args()
    if not os.path.exists(a.exe):
        subprocess.run(['gcc', '-O3', '-march=native', '-fopenmp', '-o', a.exe, os.path.join(HERE, 'focus_search.c')], check=True)
    first = a.onset - 4
    F = read_frames(a.clip, first, 64)
    keep = distinct(F, first)
    # start the game-frame list at the onset guess (first distinct frame at or after it)
    i0 = next(i for i, k in enumerate(keep) if k + first >= a.onset)
    G = [F[k] for k in keep[i0:i0 + 20]]; gnum = [k + first for k in keep[i0:i0 + 20]]
    print('distinct game frames from the onset guess (capture frame numbers):', gnum[:14])
    geo = fit_geometry(G)
    ax, ay, bx, by, koff = geo
    print('geometry: scale x %.2f y %.2f px per N64 px, emitter at (%.0f, %.0f), first listed frame = animTime %d' % (ax, ay, bx, by, koff))
    meas = measure(G, geo)
    print('particles measured (clear of neighbours on >= 2 frames): %d of 56 (%s..%s)' % (len(meas), min(meas), max(meas)))
    A, gain = calibrate(meas)
    print('seed-free calibration gains Y U V: %.2f %.2f %.2f' % tuple(gain))
    sig = np.array([float(v) for v in a.sig.split(',')])
    use = sorted(meas)
    J0, res = run_search(a.exe, A, sig, meas, use)
    print('full search (%d particles): %s' % (len(use), ['%08x %.1f' % r for r in res[:5]] or 'no survivors'))
    out = dict(clip=os.path.basename(a.clip), onset_frames=gnum[:3], geometry=dict(ax=ax, ay=ay, bx=bx, by=by, koff=koff),
               measured=len(meas), gains=gain.tolist(), full=[('%08x' % s, c) for s, c in res[:5]])
    if res:
        sJ = res[0][0]
        half = use[:len(use) // 2]; held = use[len(use) // 2:]
        _, rh = run_search(a.exe, A, sig, meas, half)
        print('half search (particles %d..%d): %s' % (half[0], half[-1], ['%08x %.1f' % r for r in rh[:5]]))
        ch = cost(A, sig, meas, sJ, held)
        rng = np.random.default_rng(0)
        rnd = np.array([cost(A, sig, meas, int(x), held) for x in rng.integers(0, 2 ** 32, 400)])
        print('held-out particles %d..%d: found seed cost %.1f; random seeds mean %.1f, min of 400 %.1f' % (held[0], held[-1], ch, rnd.mean(), rnd.min()))
        starts = backtrack(sJ, J0)
        for s0, n in starts:
            print('state before particle 0: %08x (%d draws before particle %d); +1 draw back (frame start if the shimmer is 1 draw into the frame as in the emulator): %08x' % (s0, n, J0, back(s0)))
        # seed-dependent calibration (for reuse on later clips) and residuals
        cols, _ = particles(sJ, 56 - J0)
        X = np.array([np.r_[centre_rgb(cols[j - J0]), 1] for j in use]); Mm = np.array([meas[j] for j in use])
        Af = np.linalg.lstsq(X, Mm, rcond=None)[0].T
        resid = (Mm - X @ Af.T).std(0)
        print('least-squares calibration with the found seed: residual std Y U V %.2f %.2f %.2f' % tuple(resid))
        out.update(seed_before_J0='%08x' % sJ, J0=J0, cost=res[0][1],
                   runner_up=('%08x %.1f' % res[1]) if len(res) > 1 else None,
                   half=[('%08x' % s, c) for s, c in rh[:5]], heldout_cost=ch, heldout_random_mean=float(rnd.mean()),
                   heldout_random_min=float(rnd.min()), starts=[('%08x' % s0, n) for s0, n in starts],
                   lsq_calibration=Af.tolist(), lsq_resid=resid.tolist())
    if a.out: json.dump(out, open(a.out, 'w'), indent=1)

if __name__ == '__main__':
    main()
