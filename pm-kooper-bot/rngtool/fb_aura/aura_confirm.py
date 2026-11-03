"""Independent checks of an aura lock (README section 8): the status-bar coin shines and the lightning, same stretch.
The lock (aura_lock2.c) gives the state x after the anchor frame's aura draw and the sky / low bolt phases and the
coin's first draw frame, all chosen by the aura readings alone. From there the frame model (aura_model.py) predicts
every coin draw rand_int(100) (a shine when >= 70) and every bolt frame. Display lags in this pipeline's frame
indexing (a draw sits on the frame where the restarting star shows at t = 0), calibrated on the emulator capture
simulation (aura_capsim.py, known seed): coin flash onset = draw + 5 (4 of 4), lightning onset = draw + 4 (sky and
low bolts). Windows used: coin +4..6, bolts +3..5. (readouts/focus_coin_check.py's 6-7 counts from the shimmer.) Observed:
  coin: white-pixel fraction in the coin box (default 1080,48,44x48 of the 1280x720 OBS layout; colour tests of
        focus_coin_check.coin_scan) per capture frame -> per game frame (max over its copies); a shine onset is the
        first game frame over the threshold after a quiet one;
  bolts: purple-pixel fraction (clip_bolts.py thresholds) in the play area per game frame; onsets as above.
Baseline: the same comparison for random states (the coin's first-draw frame chosen to fit best, so it is a
conservative baseline), and for the bolts the predicted frames shifted by random phases.
usage: python3 aura_confirm.py CLIP T0 PRE LOCKLOG [--box x,y,w,h] [--random 2000] [--lag 6,7]"""
import sys, os, re, json, argparse, subprocess, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aura_model import rand_int, adv

M = 0xFFFFFFFF


def sky(f, p): return ((f - p) % 220) in (0, 60, 70, 160)
def low(f, p): return ((f - p) % 130) in (0, 5, 35, 40)


def simulate(x, FA, N, nf, p220, p130, coin):
    """from the state after the anchor draw: per frame f > FA: dict(sky, low, coin value or None); and end seeds"""
    s = adv(x); nc = coin; out = {}
    for f in range(FA + 1, N):
        r = dict(sky=sky(f, p220), low=low(f, p130), coin=None)
        if r['sky']: s, _ = rand_int(s, 359)
        if r['low']: s, _ = rand_int(s, 359)
        if f == nc:
            s, v = rand_int(s, 100); r['coin'] = v; nc = f + (48 if v >= 70 else 24)
        for _ in range(nf[f]): s, _ = rand_int(s, 359)
        s = adv(s); r['seed'] = s; out[f] = r
    return out


def scan(clip, t0, t1, crop, fmt='rgb24'):
    x0, y0, w, h = crop
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', clip, '-vf',
                        'crop=%d:%d:%d:%d' % (w, h, x0, y0), '-f', 'rawvideo', '-pix_fmt', fmt, '-'], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, h, w, 3).astype(np.int16)


LG = None      # footage game frame -> logic frame (aura_table.py steps: missing logic frames), set in main()


def per_game(vals, gidx):
    v = np.array([max(vals[i:i + c]) for i, c in gidx])
    if LG is None: return v
    out = np.zeros(LG[-1] + 1); out[LG] = v
    for f in range(1, len(out)):                              # a missing logic frame repeats the previous picture
        if f not in set(LG): out[f] = out[f - 1]
    return out


def onsets(v, thr, gap=8):
    out = []
    for k in range(1, len(v)):
        if v[k] > thr and v[k - 1] <= thr and (not out or k - out[-1] > gap): out.append(k)
    return out


def match(pred, obs, lo, hi):
    """pred frames vs observed onsets: onset expected in [p + lo, p + hi]"""
    used = set(); hits = 0
    for p in pred:
        m = [o for o in obs if p + lo <= o <= p + hi and o not in used]
        if m: used.add(m[0]); hits += 1
    return hits, len(pred) - hits, len(obs) - len(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('t0', type=float); ap.add_argument('pre'); ap.add_argument('lock')
    ap.add_argument('--box', default='1080,48,44,48'); ap.add_argument('--random', type=int, default=2000)
    ap.add_argument('--lag', default='4,6'); ap.add_argument('--blag', default='3,5')
    a = ap.parse_args()
    lag = [int(v) for v in a.lag.split(',')]; blag = [int(v) for v in a.blag.split(',')]
    L = open(a.lock).read()
    mt = re.search(r'TOP score (\d+) / (\d+) reads .*state after anchor draw ([0-9a-f]{8})\s+sky (\d+)\s+low (\d+)\s+coin (\d+)', L)
    FA = int(re.search(r'anchor frame (\d+)', L).group(1))
    score, nreads, x, p220, p130, coin = int(mt.group(1)), int(mt.group(2)), int(mt.group(3), 16), int(mt.group(4)), int(mt.group(5)), int(mt.group(6))
    gidx = [tuple(v) for v in np.load(a.pre + '_gidx.npy')]
    global LG
    if os.path.exists(a.pre + '_map.json'): LG = json.load(open(a.pre + '_map.json'))['lg']
    P = json.load(open(a.pre + '_parts.json')); N = P['n']
    nf = [sum(1 for p in P['parts'] if p['phase'] % 20 == f % 20) for f in range(N)]
    sim = simulate(x, FA, N, nf, p220, p130, coin)
    t1 = a.t0 + (gidx[-1][0] + gidx[-1][1] + 2) / 60.0
    # ---- coin
    box = [int(v) for v in a.box.split(',')]
    C = scan(a.clip, a.t0, t1, box)
    r, g, b = C[..., 0], C[..., 1], C[..., 2]
    Wc = ((r > 200) & (g > 200) & (b > 190)).mean((1, 2)); Gc = ((r > 140) & (g > 95) & (b < 120) & (r > b + 60) & (g > 0.6 * r)).mean((1, 2))
    Wg = per_game(Wc, gidx); Gg = per_game(Gc, gidx)
    vis = np.nonzero(Gg > 0.3)[0]
    thr = max(0.02, 4 * np.percentile(Wg[vis], 90)) if len(vis) else 0.05
    obs = [k for k in onsets(Wg, thr) if k > FA + lag[1]]
    draws = [(f, r_['coin']) for f, r_ in sorted(sim.items()) if r_['coin'] is not None]
    pred = [f for f, v in draws if v >= 70 and f + lag[1] < N]
    h, fp, fn = match(pred, obs, lag[0], lag[1])
    print('coin box visible on %d / %d game frames; flash threshold %.3f' % (len(vis), N, thr))
    print('coin draws predicted (game frame: value):', ' '.join('%d:%d' % d for d in draws))
    print('predicted shine draws %s -> flash expected at +%d..%d' % (pred, lag[0], lag[1]))
    print('observed shine onsets (game frames after the anchor + %d): %s' % (lag[1], obs))
    print('COIN: %d of %d predicted shines seen at +%d..%d, %d false, %d unexplained onsets' % (h, len(pred), lag[0], lag[1], fp, fn))
    # random baseline: random state after the anchor, best first-coin frame
    rnd = random.Random(1); perfect = 0; best_h = []
    nfa = nf
    for _ in range(a.random):
        xs = rnd.getrandbits(32); bh = None
        for c in range(FA + 1, FA + 49):
            s = adv(xs); nc = c; d = []
            for f in range(FA + 1, N):
                if sky(f, p220): s, _ = rand_int(s, 359)
                if low(f, p130): s, _ = rand_int(s, 359)
                if f == nc: s, v = rand_int(s, 100); d.append((f, v)); nc = f + (48 if v >= 70 else 24)
                for _q in range(nfa[f]): s, _ = rand_int(s, 359)
                s = adv(s)
            pr = [f for f, v in d if v >= 70 and f + lag[1] < N]
            hh, ff, nn = match(pr, obs, lag[0], lag[1])
            if bh is None or (hh - ff - nn) > (bh[0] - bh[1] - bh[2]): bh = (hh, ff, nn)
        best_h.append(bh); perfect += bh[1] == 0 and bh[2] == 0
    sc0 = h - fp - fn; scr = np.array([q[0] - q[1] - q[2] for q in best_h])
    print('COIN baseline: %d random states (best coin phase each): all shines explained with no false one in %d; '
          'median hits %.0f; score (hits - false - unexplained) lock %d, random median %.0f, P(random >= lock) = %.4f' % (
          a.random, perfect, np.median([q[0] for q in best_h]), sc0, np.median(scr), np.mean(scr >= sc0)))
    # ---- bolts
    G = scan(a.clip, a.t0, t1, (320, 30, 950, 640))[:, ::4, ::4]
    pr_ = (G[..., 0] > 150) & (G[..., 2] > 170) & (G[..., 1] < np.minimum(G[..., 0], G[..., 2]) - 40)
    Pv = per_game(pr_.mean((1, 2)), gidx)
    bobs = onsets(Pv, 0.003, gap=3)
    skyf = [f for f in range(N) if sky(f, p220)]; lowf = [f for f in range(N) if low(f, p130)]
    print('purple onsets (game frames):', bobs)
    print('predicted sky bolt frames:', skyf, ' low bolt frames:', lowf)
    hs = match(skyf, bobs, blag[0], blag[1]); hl = match(lowf, bobs, blag[0], blag[1])
    print('SKY: %d of %d predicted sky bolts have an onset at +%d..%d; LOW: %d of %d' % (hs[0], len(skyf), blag[0], blag[1], hl[0], len(lowf)))
    rr = random.Random(2); sk = []
    for _ in range(2000):
        q = rr.randrange(220); sk.append(match([f for f in range(N) if sky(f, q)], bobs, blag[0], blag[1])[0])
    print('SKY baseline: random sky phases: hits median %.0f, P(>= %d) = %.4f' % (np.median(sk), hs[0], np.mean(np.array(sk) >= hs[0])))
    lw = []
    for _ in range(2000):
        q = rr.randrange(130); lw.append(match([f for f in range(N) if low(f, q)], bobs, blag[0], blag[1])[0])
    both = match(sorted(set(skyf + lowf)), bobs, blag[0], blag[1])
    print('LOW baseline: random low phases: hits median %.0f, P(>= %d) = %.4f; onsets explained by sky or low bolts: %d of %d'
          % (np.median(lw), hl[0], np.mean(np.array(lw) >= hl[0]), len(bobs) - both[2], len(bobs)))
    json.dump(dict(x='%08x' % x, FA=FA, p220=p220, p130=p130, coin=coin, draws=draws, shine_obs=obs, bolt_onsets=bobs,
                   seed_end={f: '%08x' % r_['seed'] for f, r_ in sim.items()}), open(a.pre + '_confirm.json', 'w'))


if __name__ == '__main__':
    main()
