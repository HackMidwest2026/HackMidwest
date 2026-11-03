"""Still-stretch aura readout from a capture (README section 8): camera fit, restart likelihood table, 16-part table,
per-restart angle readings.

  python3 aura_table.py prep  CLIP T0 T1 PRE         game frames + kNN background (aura_mf.prep / background)
  python3 aura_table.py cam   PRE [K0 K1]            camera fit from matched-filter peaks (tracks, joint fit)
  python3 aura_table.py table PRE                    restart log-likelihood table LL[f0, v, size, A]
  python3 aura_table.py refine PRE                   camera refinement from the part table (then rerun table, parts)
  python3 aura_table.py terms PRE                    store the per-frame terms (PRE_F.npy) for the numbering fit
  python3 aura_table.py steps PRE [auto|S1,S2,..]    missing logic frames: fit, rebuild the table on logic frames
  python3 aura_table.py parts PRE                    16-part table + readings -> PRE_parts.json
  python3 aura_table.py obs PRE OUT [MARGIN=8 TOL=3 ANCHOR=0 RANDOM=0]   readings -> aura_lock2.c input

PRE is a path prefix in /dev/shm (arrays are large: about 2.5 GB per 18 s of capture).

Restart table: every hypothesis "a star of size s and speed v restarted on game frame f0 with draw A" is scored by the
summed matched-filter log-likelihood ratio over its visible frames t = 1..19 (aura_mf docstring; per-frame terms are
clipped to [-CLIPLO, CLIPHI] so a single overlapped or occluded frame cannot dominate). The table holds every f0 in
-19..n-1, v in 0.6..2.6 (11 values), the 3 sizes, A in 0..359.

Part table: a part is (phase = f0 mod 20, v, size); its restarts are f0 = phase + 20 c. Each hypothesis is scored by
the median over its cycles of the best restart score (max over A). Parts are taken greedily, best first; after each
pick, every A of every other hypothesis whose path overlaps a picked restart's path (mean distance < OVL px over the
shared frames) is masked out, so one star cannot be explained twice. The sizes are fixed by the decomp (part index
i has scale 1 - (i mod 3) x 0.3: 5 x 1.0, 6 x 0.7, 5 x 0.4); a size whose quota is full is not picked again.
Readings: per picked part and cycle, the best A, its score and the margin to the best A more than 4 deg away."""
import sys, os, json, math, time
import numpy as np
from scipy import optimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aura_mf as m

VS = 0.6 + 0.2 * np.arange(11)
CLIPHI, CLIPLO, KAPPA = 400.0, 6.0, 2.0
AMIN, AMAX = 0.4, 1.6
OVL = 12.0
QUOTA = {1.0: 5, 0.7: 6, 0.4: 5}          # parts per size: scale = 1 - (index mod 3) * 0.3, indices 1..16


def load(pre):
    L = np.load(pre + '_L.npy', mmap_mode='r'); B = np.load(pre + '_B.npy', mmap_mode='r'); sig = np.load(pre + '_sig.npy')
    return L, B, sig


def mf_for(pre, cam, white, L=None, B=None, sig=None):
    cov = m.load_cov()
    T, T2 = m.templates(cov, cam[2], cam[3])
    mf = m.MF(T, T2, (m.CH, m.CW))
    if L is not None:
        sc = [mf.calibrate(L[k].astype(np.float32) - B[k].astype(np.float32), B[k].astype(np.float32), sig, white)
              for k in np.linspace(0, len(L) - 1, 5).astype(int)]
        mf.scale = float(np.median(sc))
        print('noise scale (null calibration): %.2f' % mf.scale, flush=True)
    return mf


def frame_maps(mf, L, B, sig, k, white):
    Lk = L[k].astype(np.float32); Bk = B[k].astype(np.float32)
    return mf.maps(Lk - Bk, Bk, sig, white)


# ------------------------------------------------------------------ camera
def link(P, lo=2.0, hi=30.0):
    tracks = []
    for k, pk in enumerate(P):
        for x, y, snr, s, rot in pk:
            best = None
            for t in tracks:
                if t[-1][0] == k - 1:
                    d = math.dist(t[-1][1:3], (x, y))
                    if lo < d < hi and (best is None or d < best[0]): best = (d, t)
            if best: best[1].append((k, x, y, snr, s))
            else: tracks.append([(k, x, y, snr, s)])
    return tracks


def fit1(t, cam):
    """one track (crop px) -> (f0, A, v) continuous, rms px; the track's size from its peaks; camera homography with
    the default shear / pitch when cam has 4 entries"""
    sz = min(m.SIZES, key=lambda s: abs(s - float(np.median([q[4] for q in t]))))
    K = np.array([q[0] for q in t], float); X = np.array([q[1] for q in t]); Y = np.array([q[2] for q in t])
    def res(p):
        f0, A, v = p
        x, y, _ = m.star_xy(cam, A, v, K - f0, sz)
        return np.r_[x - X, y - Y]
    best = None; k, x, y = t[0][:3]
    cx, cy = cam[0] - m.X0, cam[1] - m.Y0
    for v0 in (0.8, 1.6, 2.4):
        r = math.hypot((x - cx) / cam[2], (y - cy) / cam[3]); n0 = max(1, (r - 10) / v0)
        p0 = [min(max(k - n0 + 1, k - 39), k + 4), math.degrees(math.atan2(-(y - cy) / cam[3], (x - cx) / cam[2])) + 2 * n0, v0]
        so = optimize.least_squares(res, p0, bounds=([k - 40, -1e4, 0.5], [k + 5, 1e4, 2.7]))
        if best is None or so.cost < best.cost: best = so
    r = np.array(best.fun).reshape(2, -1)
    return best.x, math.sqrt((r ** 2).sum(0).mean())


def fit_camera(tracks, cam0, maxrms=3.0):
    """initial camera (cx, cy, kx, ky; shear and pitch at the route camera's values) from peak tracks"""
    cam = list(cam0[:4])
    for it in range(3):
        good = [t for t in tracks if fit1(t, cam)[1] < maxrms * (2 if it == 0 else 1)]
        if len(good) < 4: break
        so = optimize.least_squares(lambda c: [fit1(t, c)[1] for t in good], cam, diff_step=[1e-3] * 4, loss='soft_l1',
                                    bounds=([900, 250, 3.5, 3.5], [1150, 450, 7.0, 7.0]))
        cam = list(so.x)
    return cam + [m.CAM_SH, m.CAM_H], good


def refine_camera(pre, P, cam, white, step=2, minmargin=20.0, win=7):
    """camera refinement from the part table: for every well-read restart (margin >= minmargin, whole life seen) the
    sprite is located on frames t = 3..16 (every `step`-th game frame) as the matched-filter SNR peak (its size and
    rotation bin) within +-win px of the prediction (parabolic sub-pixel); then (cx, cy, kx, ky, sh, h) and one A per
    restart are fitted by robust least squares with f0, v, size held at the table's discrete values."""
    L, B, sig = load(pre)
    mf = mf_for(pre, cam, white, L, B, sig)
    n = len(L)
    R = [(p, r) for p in P['parts'] for r in p['restarts'] if r['margin'] >= minmargin and r['cnt'] >= 17]
    pts = []
    for k in range(0, n, step):
        act = [(j, p, r) for j, (p, r) in enumerate(R) if 3 <= k - r['f0'] <= 16]
        if not act: continue
        N, D = frame_maps(mf, L, B, sig, k, white)
        for j, p, r in act:
            t = k - r['f0']; s = p['size']
            x, y, th = m.star_xy(cam, r['A'], p['v'], t, s)
            rb = int(round((th % 72) / m.ROT)) % m.NROT
            xi, yi = int(round(x)), int(round(y))
            if not (win + 1 <= xi < m.CW - win - 1 and win + 1 <= yi < m.CH - win - 1): continue
            S = N[s][rb, yi - win:yi + win + 1, xi - win:xi + win + 1] / np.sqrt(np.maximum(D[s][yi - win:yi + win + 1, xi - win:xi + win + 1], 1e-6))
            a, b = np.unravel_index(np.argmax(S), S.shape)
            if not (0 < a < 2 * win and 0 < b < 2 * win) or S[a, b] < 6: continue
            dy = 0.5 * (S[a - 1, b] - S[a + 1, b]) / (S[a - 1, b] - 2 * S[a, b] + S[a + 1, b] + 1e-9)
            dx = 0.5 * (S[a, b - 1] - S[a, b + 1]) / (S[a, b - 1] - 2 * S[a, b] + S[a, b + 1] + 1e-9)
            pts.append((j, t, xi - win + b + float(np.clip(dx, -1, 1)), yi - win + a + float(np.clip(dy, -1, 1)),
                        float(N[s][rb, yi - win + a, xi - win + b] / max(D[s][yi - win + a, xi - win + b], 1e-6) / m.alpha(t))))
    pts = np.array(pts)
    J = pts[:, 0].astype(int); Tt = pts[:, 1]; V = np.array([R[j][0]['v'] for j in J]); Sz = np.array([R[j][0]['size'] for j in J])
    uj = sorted(set(J)); col = {j: i for i, j in enumerate(uj)}
    def res(q):
        c = q[:6]; A = q[6:][[col[j] for j in J]]
        out = []
        for s in m.SIZES:
            u = Sz == s
            if u.any():
                x, y, _ = m.star_xy(c, A[u], V[u], Tt[u], s)
                out.append(np.r_[x - pts[u, 2], y - pts[u, 3]])
        return np.concatenate(out)
    q0 = np.r_[np.array(cam, float), [R[j][1]['A'] for j in uj]]
    so = optimize.least_squares(res, q0, loss='soft_l1', f_scale=1.5, x_scale=np.r_[[1, 1, 0.01, 0.01, 0.01, 1e-4], np.ones(len(uj))])
    rr = np.abs(so.fun)
    print('camera refinement: %d restarts, %d sprite positions; residual median %.2f px, 90%% %.2f px' % (len(uj), len(pts), np.median(rr), np.percentile(rr, 90)))
    gains = {s: float(np.median(pts[Sz == s, 4])) if (Sz == s).sum() >= 10 else 1.0 for s in m.SIZES}
    print('amplitude gains (sprite contrast / template, median over the located sprites):', gains)
    return list(so.x[:6]), gains


# ------------------------------------------------------------------ restart table
def frame_terms(N, D, cam, rmax_t=19, gains=None):
    """per-frame LLR terms for every (t, v, size, A): array (19, 11, 3, 360). The star's amplitude is free within
    [AMIN, AMAX] x alpha(t) x gain(size) (bounded GLRT): the sprite's effective contrast after the capture blur is
    not known exactly (gain calibrated by refine_camera), and a fixed amplitude would penalise the right hypothesis
    whenever it is off; the bounds keep the alpha ramp and the negative evidence of an empty path."""
    gains = gains or {s: 1.0 for s in m.SIZES}
    t = np.arange(1, rmax_t + 1)[:, None, None]; v = VS[None, :, None]; A = np.arange(360)[None, None, :]
    al = m.alpha(t)
    out = np.empty((rmax_t, 11, 3, 360), np.float32)
    H, W = N[m.SIZES[0]].shape[-2:]
    for si, s in enumerate(m.SIZES):
        x, y, th = m.star_xy(cam, A, v, t, s)
        rb = (np.round((th % 72) / m.ROT).astype(int)) % m.NROT
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
        ok = (x0 >= 0) & (y0 >= 0) & (x0 < W - 1) & (y0 < H - 1)
        x0 = np.clip(x0, 0, W - 2); y0 = np.clip(y0, 0, H - 2)
        Ns, Ds = N[s], D[s]
        def bil(M, idx=None):
            g = (lambda yy, xx: M[rb, yy, xx]) if idx else (lambda yy, xx: M[yy, xx])
            return (g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy)
        n_ = bil(Ns, True); d_ = np.maximum(bil(Ds), 1e-6)
        g = al * gains[s]
        a = np.clip(n_ / d_, AMIN * g, AMAX * g)
        ll = a * n_ - 0.5 * a * a * d_
        ll = np.minimum(ll, KAPPA * 0.5 * g * g * d_ + 2.0)            # at most KAPPA x a perfect star's expected term
        out[:, :, si, :] = np.where(ok, np.clip(ll, -CLIPLO, CLIPHI), 0.0)
    return out


def build_table(pre, cam, white, frames=None, log=True, gains=None):
    L, B, sig = load(pre)
    n = len(L)
    mf = mf_for(pre, cam, white, L, B, sig)
    TAB = np.zeros((n + 19, 11, 3, 360), np.float32)       # index f0 + 19
    CNT = np.zeros(n + 19, np.int16)                         # visible frames counted per f0
    T0 = time.time()
    for k in (frames if frames is not None else range(n)):
        N, D = frame_maps(mf, L, B, sig, k, white)
        F = frame_terms(N, D, cam, gains=gains)
        for t in range(1, 20):
            TAB[k - t + 19] += F[t - 1]; CNT[k - t + 19] += 1
        if log and k % 50 == 0: print('  frame %d / %d  %.0f s' % (k, n, time.time() - T0), flush=True)
    return TAB, CNT


# ------------------------------------------------------------------ parts
def path_xy(cam, A, v, t):
    x, y, _ = m.star_xy(cam, A, v, t)
    return x, y


def pick_parts(TAB, CNT, cam, n, npart=16, mincnt=12):
    """greedy part selection with explaining-away; returns list of dict(phase, vi, si, score, restarts=[(f0, A, s, margin)])"""
    F0 = np.arange(-19, n)
    full = CNT >= mincnt                                     # restarts seen over at least mincnt frames
    mask = np.zeros(TAB.shape, bool)                         # masked (f0, vi, si, A)
    parts = []
    tt = np.arange(3, 17)
    # precomputed paths: (11, 360, len(tt)) per v
    PX = np.empty((3, 11, 360, len(tt))); PY = np.empty_like(PX)       # sprite positions per size
    for si, sz in enumerate(m.SIZES):
        PX[si], PY[si], _ = m.star_xy(cam, np.arange(360)[None, :, None], VS[:, None, None], tt[None, None, :], sz)
    while len(parts) < npart:
        best = None
        T = np.where(mask, -1e9, TAB)
        for si, sz in enumerate(m.SIZES):
            if sum(1 for p in parts if p['size'] == sz) >= QUOTA[sz]: T[:, :, si, :] = -1e9
        mx = T.max(-1)                                       # (f0, vi, si)
        for ph in range(20):
            idx = [i for i in range(len(F0)) if (F0[i] - ph) % 20 == 0 and full[i]]
            if not idx: continue
            sc = np.median(mx[idx], 0)                       # (vi, si)
            vi, si = np.unravel_index(np.argmax(sc), sc.shape)
            if best is None or sc[vi, si] > best[0]: best = (sc[vi, si], ph, vi, si, idx)
        sc, ph, vi, si, idx = best
        rs = []
        for i in [i for i in range(len(F0)) if (F0[i] - ph) % 20 == 0]:
            row = T[i, vi, si]; A = int(np.argmax(row))
            far = np.abs(((np.arange(360) - A + 180) % 360) - 180) > 4
            rs.append(dict(f0=int(F0[i]), A=A, s=float(row[A]), margin=float(row[A] - row[far].max()), cnt=int(CNT[i])))
            # mask every hypothesis whose path overlaps this restart's path (shared frames)
            ax, ay = PX[si, vi, A], PY[si, vi, A]
            for dt in range(-6, 7):                          # other f0 = f0 + dt: shared frames tt (this) = tt - dt (other)
                j = i + dt
                if j < 0 or j >= len(F0): continue
                ts = tt - dt; okk = (ts >= 3) & (ts <= 16)
                if okk.sum() < 5: continue
                bx = PX[:, :, :, ts[okk] - 3]; by = PY[:, :, :, ts[okk] - 3]
                d = np.hypot(bx - ax[okk], by - ay[okk]).mean(-1)            # (3, 11, 360)
                mask[j] |= (d < OVL).transpose(1, 0, 2)
        parts.append(dict(phase=int(ph), v=float(VS[vi]), vi=int(vi), size=m.SIZES[si], score=float(sc), restarts=rs))
        print('part %2d: phase %2d v %.1f size %.1f score %.1f  restarts (A, score):' % (len(parts), ph, VS[vi], m.SIZES[si], sc),
              ' '.join('%d:%d/%.0f' % (r['f0'], r['A'], r['s']) for r in rs[:6]), flush=True)
    return parts


# ------------------------------------------------------------------ missing logic frames
# On the console stretch the 20-frame star cycle spans about 19.8 footage game frames: now and then a logic frame never
# shows as its own picture (about 1 per 90-110 footage frames in clip C). The per-frame terms do not depend on the frame
# numbering, so they are stored once (PRE_F.npy, float16) and the table is re-accumulated for any numbering
# lg[k] = logic frame of footage frame k (lg[k] = k + number of missing logic frames before k).
def dump_terms(pre, cam, white, gains=None):
    L, B, sig = load(pre)
    mf = mf_for(pre, cam, white, L, B, sig)
    n = len(L)
    F = np.lib.format.open_memmap(pre + '_F.npy', mode='w+', dtype=np.float16, shape=(n, 19, 11, 3, 360))
    for k in range(n):
        N, D = frame_maps(mf, L, B, sig, k, white)
        F[k] = frame_terms(N, D, cam, gains=gains)
    F.flush()


def table_from_terms(F, lg):
    """restart table indexed by logic frame (f0 + 19) for the numbering lg"""
    nl = int(lg[-1]) + 1
    TAB = np.zeros((nl + 19, 11, 3, 360), np.float32); CNT = np.zeros(nl + 19, np.int16)
    for k in range(len(F)):
        Fk = F[k].astype(np.float32)
        for t in range(1, 20):
            TAB[lg[k] - t + 19] += Fk[t - 1]; CNT[lg[k] - t + 19] += 1
    return TAB, CNT


def numbering(n, steps):
    """lg for missing logic frames inserted before the footage frames in `steps`"""
    lg = np.arange(n)
    for s_ in steps: lg[s_:] += 1
    return lg


def proxy(TAB, CNT):
    """mean over restart frames seen on >= 17 frames of the best hypothesis (a mean: a missing logic frame leaves the
    restarts around it with 18 frames, which a sum over whole lives would drop and so penalise)"""
    ok = CNT >= 17
    return float(TAB[ok].reshape(ok.sum(), -1).max(1).mean())


def initial_steps(P, TAB, minscore=3000.0):
    """first guess of the missing-frame positions from a part table built without them: per strong restart the
    restart-frame shift d in -4..4 that scores best; a missing logic frame makes d drop by one for every later restart.
    Monotone (non-increasing) integer step function fitted by dynamic programming; returns the step positions."""
    n = len(TAB) - 19; pts = []
    for p in P['parts']:
        si = m.SIZES.index(p['size'])
        for r in p['restarts']:
            sc = [(TAB[r['f0'] + d + 19, p['vi'], si].max(), d) for d in range(-4, 5) if 19 <= r['f0'] + d + 19 < n]
            if sc and max(sc)[0] > minscore: pts.append((r['f0'] + max(sc)[1], max(sc)[1]))
    pts.sort()
    if not pts: return []
    lv = list(range(4, -9, -1)); NL = len(lv)
    S = np.full((len(pts) + 1, NL), -1e9); S[0] = 0; bk = np.zeros((len(pts) + 1, NL), int)
    for i, (f, d) in enumerate(pts):
        for j in range(NL):
            jj = int(np.argmax(S[i, :j + 1])); S[i + 1, j] = S[i, jj] + (d == lv[j]) - 0.02 * (jj != j); bk[i + 1, j] = jj
    j = int(np.argmax(S[-1])); lab = [0] * len(pts)
    for i in range(len(pts), 0, -1): lab[i - 1] = j; j = bk[i, j]
    out = []
    for i in range(1, len(pts)):
        for q in range(lab[i] - lab[i - 1]): out.append((pts[i - 1][0] + pts[i][0]) // 2)
    return out


def fit_steps(F, steps, win=30, rounds=2):
    """coordinate search of the missing-frame positions on the proxy evidence; also tries dropping each step and
    adding one in every gap"""
    n = len(F)
    def score(st):
        T, C = table_from_terms(F, numbering(n, sorted(st))); return proxy(T, C)
    steps = sorted(steps); best = score(steps)
    print('  start %s: %.0f' % (steps, best), flush=True)
    for r in range(rounds):
        for i in range(len(steps)):
            for cand in range(max(1, steps[i] - win), min(n - 1, steps[i] + win) + 1, 3):
                st = steps[:i] + [cand] + steps[i + 1:]
                sc = score(st)
                if sc > best: best, steps = sc, sorted(st)
            print('  round %d step %d -> %s: %.0f' % (r, i, steps, best), flush=True)
        for i in range(len(steps)):                       # fine: +-2 around each
            for cand in range(steps[i] - 2, steps[i] + 3):
                st = sorted(steps[:i] + [cand] + steps[i + 1:]); sc = score(st)
                if sc > best: best, steps = sc, st
    for s_ in list(steps):                                # keep a step only if it adds evidence
        st = [q for q in steps if q != s_]; sc = score(st)
        print('  without step %d: %.0f (with %.0f)%s' % (s_, sc, best, ' -> dropped' if sc >= best else ''))
        if sc >= best: steps, best = st, sc
    return steps, best


def scale_scan(pre, cam, white, rhos, k0=0, k1=150, gains=None):
    """camera scale vs restart-frame degeneracy: a camera that is a few % too small fits every star with its restart
    one frame early and a faster speed nearly as well. For each scale factor rho (kx, ky x rho, centre fixed) the
    restart table is accumulated over frames k0..k1 (matched-filter maps computed once per frame) and scored by
    sum over restart frames f0 (whole life inside) of max over (v, size, A); the right scale has integer restart
    frames and grid speeds for every part at once, so it explains the stars best."""
    L, B, sig = load(pre)
    mf = mf_for(pre, cam, white, L, B, sig)
    n = k1 - k0
    TABS = [np.zeros((n + 19, 11, 3, 360), np.float32) for _ in rhos]
    cams = [[cam[0], cam[1], cam[2] * r, cam[3] * r] + list(cam[4:]) for r in rhos]
    for k in range(k0, k1):
        N, D = frame_maps(mf, L, B, sig, k, white)
        for T, c in zip(TABS, cams):
            F = frame_terms(N, D, c, gains=gains)
            for t in range(1, 20):
                T[k - k0 - t + 19] += F[t - 1]
    out = []
    for r, T in zip(rhos, TABS):
        sc = float(T[19:n].reshape(n - 19 + 19 - 19, -1).max(1)[:n - 19].sum()) if n > 38 else 0.0
        out.append((r, sc))
        print('  scale x %.3f (kx %.3f): evidence %.0f' % (r, cam[2] * r, sc), flush=True)
    return out


def make_obs(P, margin=8.0, tol=3, anchor=0, rnd=0, K=8, MK=6, M0=6, sky=(0, 219)):
    """frames 0..n-1: per frame the restarts of the part table (phase = f mod 20), read when the restart's whole life
    is inside the stretch (cnt >= 17) and its margin >= `margin`. rnd > 0: every read angle replaced by a random one
    (seeded): the null baseline. anchor: index among the frames with one read restart."""
    n = P['n']; rng = np.random.default_rng(rnd)
    rows = []
    for f in range(n):
        r = []
        for p in P['parts']:
            if p['phase'] % 20 != f % 20: continue
            q = [x for x in p['restarts'] if x['f0'] == f]
            if q and q[0]['cnt'] >= 17 and q[0]['margin'] >= margin:
                a = int(rng.integers(0, 360)) if rnd else q[0]['A']
                r.append((a, tol))
            else: r.append((-1, 0))
        rows.append(r)
    singles = [f for f in range(n) if len(rows[f]) == 1 and rows[f][0][0] >= 0]
    FA = singles[anchor]
    lines = ['%d %d %d %d %d %d %d' % (n, FA, sky[0], sky[1], K, MK, M0)]
    lines += [' '.join([str(len(r))] + ['%d %d' % x for x in r]) for r in rows]
    nread = sum(1 for r in rows for x in r if x[0] >= 0)
    return '\n'.join(lines) + '\n', FA, nread, sum(len(r) for r in rows)


if __name__ == '__main__':
    cmd, pre = sys.argv[1], sys.argv[-1] if sys.argv[1] in ('table', 'parts') else None
    if cmd == 'terms':
        pre = sys.argv[2]; C = json.load(open(pre + '_cam.json'))
        g = C.get('gains'); g = {float(k): v for k, v in g.items()} if g else None
        dump_terms(pre, C['cam'], C['white'], g)
    if cmd == 'steps':
        pre = sys.argv[2]; arg = sys.argv[3] if len(sys.argv) > 3 else 'auto'
        F = np.asarray(np.load(pre + '_F.npy', mmap_mode='r'))
        if arg == 'auto':
            import io, contextlib
            T0, C0 = table_from_terms(F, np.arange(len(F)))
            with contextlib.redirect_stdout(io.StringIO()):
                P0 = pick_parts(T0, C0, json.load(open(pre + '_cam.json'))['cam'], len(F))
            init = initial_steps(dict(parts=P0), T0)
            print('initial missing-frame guess (restart-shift drift):', init, flush=True)
        else: init = [int(v) for v in arg.split(',')] if arg else []
        steps, sc = fit_steps(F, init)
        lg = numbering(len(F), steps)
        json.dump(dict(steps=steps, lg=lg.tolist(), proxy=sc), open(pre + '_map.json', 'w'))
        TAB, CNT = table_from_terms(F, lg)
        np.save(pre + '_tab.npy', TAB); np.save(pre + '_cnt.npy', CNT)
        print('missing logic frames before footage frames', steps, '; table rebuilt on', len(CNT) - 19, 'logic frames')
    if cmd == 'scan':
        pre = sys.argv[2]; k0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0; k1 = int(sys.argv[4]) if len(sys.argv) > 4 else 150
        C = json.load(open(pre + '_cam.json'))
        g = C.get('gains'); g = {float(k): v for k, v in g.items()} if g else None
        rhos = np.round(np.arange(0.88, 1.121, 0.02), 3)
        res = scale_scan(pre, C['cam'], C['white'], rhos, k0, k1, g)
        r = max(res, key=lambda q: q[1])[0]
        C['scan'] = res; C['cam_prescan'] = C['cam']; C['cam'] = [C['cam'][0], C['cam'][1], C['cam'][2] * r, C['cam'][3] * r] + C['cam'][4:]
        print('best scale x %.3f -> camera %s' % (r, np.round(C['cam'], 4).tolist()))
        json.dump(C, open(pre + '_cam.json', 'w'))
    if cmd == 'refine':
        pre = sys.argv[2]
        C = json.load(open(pre + '_cam.json')); P = json.load(open(pre + '_parts.json'))
        cam, gains = refine_camera(pre, P, C['cam'], C['white'])
        print('camera: centre (%.1f, %.1f), kx %.3f ky %.3f, shear %.3f, pitch %.2e' % tuple(cam))
        C['cam_prev'] = C['cam']; C['cam'] = cam; C['gains'] = gains
        json.dump(C, open(pre + '_cam.json', 'w'))
    if cmd == 'obs':
        pre, out = sys.argv[2], sys.argv[3]
        a = [float(x) for x in sys.argv[4:]] + [None] * 4
        P = json.load(open(pre + '_parts.json'))
        txt, FA, nr, nt = make_obs(P, margin=a[0] if a[0] is not None else 8.0, tol=int(a[1]) if a[1] is not None else 3,
                                   anchor=int(a[2]) if a[2] is not None else 0, rnd=int(a[3]) if a[3] is not None else 0)
        open(out, 'w').write(txt)
        print('frames %d, restarts %d, read %d (%.0f%%), anchor frame %d' % (P['n'], nt, nr, 100.0 * nr / nt, FA))
    if cmd == 'prep':
        clip, t0, t1, pre = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        G, idx = m.prep(clip, t0, t1, pre)
        print('game frames', len(G), 'capture copies per game frame', np.bincount([c for i, c in idx]), flush=True)
        L, B, sig, nb, dist = m.background(G)
        del G
        np.save(pre + '_L.npy', L); np.save(pre + '_B.npy', B); np.save(pre + '_sig.npy', sig); np.save(pre + '_nb.npy', nb)
        os.remove(pre + '_G.npy')
        print('background done; sigma percentiles 10/50/90/99:', np.percentile(sig, [10, 50, 90, 99]).round(1))
    elif cmd == 'cam':
        pre = sys.argv[2]; k0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0; k1 = int(sys.argv[4]) if len(sys.argv) > 4 else 120
        cam0 = json.load(open(pre + '_cam.json'))['cam'] if os.path.exists(pre + '_cam.json') else [1026.0, 360.0, 5.0, 5.0]
        white = 235.0
        L, B, sig = load(pre)
        mf = mf_for(pre, cam0, white, L, B, sig)
        pk = pre + '_peaks_%d_%d.json' % (k0, k1)
        if os.path.exists(pk): P = json.load(open(pk))
        else:
            P = []
            for k in range(k0, k1):
                N, D = frame_maps(mf, L, B, sig, k, white)
                P.append([p for p in m.peaks(N, D, thr=7.0)])
            json.dump(P, open(pk, 'w'))
        T = [t for t in link(P) if len(t) >= 6]
        cam, good = fit_camera(T, cam0)
        json.dump(dict(cam=cam, white=white, k0=k0, k1=k1), open(pre + '_cam.json', 'w'))
        rows = [(fit1(t, cam), t) for t in good]
        print('peaks/frame %.1f; tracks >= 6 frames: %d; fitted < 3 px: %d' % (np.mean([len(p) for p in P]), len(T), len(good)))
        print('camera: centre (%.1f, %.1f), kx %.3f ky %.3f px/unit (shear, pitch fixed)' % tuple(cam[:4]))
        for (p, r), t in sorted(rows, key=lambda z: z[0][0][0]):
            print('  f0 %7.2f A %6.1f v %.2f rms %.2f n %d snr %.0f size %.1f' % (p[0] + k0, p[1] % 360, p[2], r, len(t),
                  np.median([q[3] for q in t]), np.median([q[4] for q in t])))
    elif cmd == 'table':
        C = json.load(open(pre + '_cam.json'))
        g = C.get('gains'); g = {float(k): v for k, v in g.items()} if g else None
        print('camera', C['cam'], 'gains', g, flush=True)
        TAB, CNT = build_table(pre, C['cam'], C['white'], gains=g)
        np.save(pre + '_tab.npy', TAB); np.save(pre + '_cnt.npy', CNT)
    elif cmd == 'parts':
        C = json.load(open(pre + '_cam.json'))
        TAB = np.load(pre + '_tab.npy'); CNT = np.load(pre + '_cnt.npy')
        n = len(CNT) - 19
        parts = pick_parts(TAB, CNT, C['cam'], n)
        sz = [p['size'] for p in parts]
        print('sizes picked: 1.0 x %d, 0.7 x %d, 0.4 x %d (expected 5 / 6 / 5)' % (sz.count(1.0), sz.count(0.7), sz.count(0.4)))
        ph = [0] * 20
        for p in parts: ph[p['phase']] += 1
        print('restarts per phase:', ''.join(str(c) for c in ph))
        json.dump(dict(cam=C['cam'], n=n, parts=parts), open(pre + '_parts.json', 'w'))
