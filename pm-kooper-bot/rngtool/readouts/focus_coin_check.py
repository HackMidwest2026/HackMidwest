"""Independent check of a Focus-shimmer seed (focus_seed.py): step it forward through the following frames with the
status-bar coin model and compare the predicted coin shines with the shines seen in the same capture.

Model (rngtool README / pmrng_core.js): one LCG step per game frame; the coin draws rand_int(100) every 24 frames, 48
after a shine (value >= 70); the white flash shows on draw + 6/7. Nothing else draws while the bar sits on a menu.
Free parameters: the coin's phase (frame of its next draw after the shimmer, 0..47) and where the frame step and the
coin fall relative to the shimmer inside its frame (SC/CS order, step before/after) - 192 hypotheses, all scored.
Significance: the same hypothesis search run on random seeds.

usage: python3 focus_coin_check.py CLIP --frame C0 --seed S0 [--box x,y,w,h] [--random 3000] [--prev C,S]
  C0 = capture frame of the shimmer's first frame (focus_seed.py prints it), S0 = state before particle 0 (hex).
  --prev C,S: an earlier shimmer (capture frame, seed): prints the LCG distance between the two seeds.
  The default coin box is the one of the 1280x720 OBS layout used for the README clips."""
import argparse, os, random, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from focus_seed import particles, rand_int, adv

def coin_scan(clip, box):
    x0, y0, w, h = box
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', clip, '-vf', 'crop=%d:%d:%d:%d,format=rgb24' % (w, h, x0, y0),
                          '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    W, G = [], []
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3: break
        a = np.frombuffer(b, np.uint8).reshape(h, w, 3).astype(int); r, g, bb = a[..., 0], a[..., 1], a[..., 2]
        W.append(((r > 200) & (g > 200) & (bb > 190)).mean())                       # same colour tests as
        G.append(((r > 140) & (g > 95) & (bb < 120) & (r > bb + 60) & (g > 0.6 * r)).mean())   # shared/coin_detect
    return np.array(W), np.array(G)

def shines(W, G, c0, gpc):
    """1-based capture frames of shine onsets on the coin visible from c0 on, and the end of that visible stretch"""
    vis = G > 0.3
    end = c0 - 1
    while end < len(G) and vis[end]: end += 1
    thr = max(0.02, 4 * np.percentile(W[c0 - 1:end][vis[c0 - 1:end]], 97))
    out = []
    for i in range(c0 - 1, end):
        if W[i] > thr and W[i - 1] <= thr and (not out or (i + 1 - out[-1]) * gpc > 40): out.append(i + 1)
    return out, end, thr

def sim(s0, p, order, tail_step, nframes):
    _, s = particles(s0, 56)
    nxt = p; draws = []
    def coin(f, s):
        nonlocal nxt
        if f == nxt:
            s, v = rand_int(s, 100); sh = v >= 70; draws.append((f, sh, v)); nxt = f + (48 if sh else 24)
        return s
    if tail_step: s = adv(s)
    if p == 0: s = coin(0, s)
    for f in range(1, nframes):
        if order == 'SC': s = adv(s); s = coin(f, s)
        else: s = coin(f, s); s = adv(s)
    return draws

def score(draws, on, gmax, lag=(6, 7), tol=1.0):
    pred = [f for f, sh, v in draws if sh and f + lag[1] <= gmax]
    used, hits = set(), []
    for f in pred:
        m = [o for o in on if f + lag[0] - tol <= o <= f + lag[1] + tol and o not in used]
        if m: used.add(m[0]); hits.append((f, m[0]))
    return len(hits), len(pred) - len(hits), len(on) - len(used), hits

HYP = [(o, t, p) for o in ('SC', 'CS') for t in (0, 1) for p in range(48)]
def perfect(s0, on, gmax):
    out = []
    for o, t, p in HYP:
        d = sim(s0, p, o, t, int(gmax) + 2); h, fp, fn, hits = score(d, on, gmax)
        if fp == 0 and fn == 0 and h == len(on): out.append((o, t, p, d, hits))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('--frame', type=int, required=True); ap.add_argument('--seed', required=True)
    ap.add_argument('--box', default='1080,48,44,48'); ap.add_argument('--random', type=int, default=3000)
    ap.add_argument('--prev', default=None)
    a = ap.parse_args()
    fps = eval(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                        'stream=r_frame_rate', '-of', 'csv=p=0', a.clip]).decode().strip())
    gpc = 29.97 / fps                                                   # game frames per capture frame
    s0 = int(a.seed, 16); c0 = a.frame
    W, G = coin_scan(a.clip, [int(v) for v in a.box.split(',')])
    obs, end, thr = shines(W, G, c0, gpc)
    on = [(c - c0) * gpc for c in obs]; gmax = (end - c0) * gpc
    print('coin visible from capture frame %d to %d (%.0f game frames); flash threshold %.3f' % (c0, end, gmax, thr))
    print('observed shine onsets: capture %s = game frames %s after the shimmer' % (obs, [round(o, 1) for o in on]))
    P = perfect(s0, on, gmax)
    print('hypotheses (of %d) matching every shine with no false or missed shine: %d' % (len(HYP), len(P)))
    if P:
        o, t, p, d, hits = P[0]
        print('e.g. order %s, step after shimmer %d, coin phase %d:' % (o, t, p))
        for f, sh, v in d:
            if f + 7 > gmax: break
            hit = [h for h in hits if h[0] == f]
            print('  draw on game frame %3d: rand_int(100) = %2d %s' % (f, v, ('SHINE, predicted onset capture %d-%d, seen %d (lag %.1f)' %
                  (c0 + (f + 6) / gpc, c0 + (f + 7) / gpc, obs[on.index(hit[0][1])], hit[0][1] - f)) if sh else ''))
    if a.random:
        rnd = random.Random(1); n = 0
        for _ in range(a.random): n += bool(perfect(rnd.getrandbits(32), on, gmax))
        print('random seeds with a matching hypothesis: %d of %d' % (n, a.random))
    if a.prev:
        pc, ps = a.prev.split(','); ps = int(ps, 16); s = ps
        for n in range(1, 10 ** 7):
            s = adv(s)
            if s == s0: print('LCG distance from the earlier shimmer seed %08x (capture %s) to this one: %d draws over %.0f game frames' % (ps, pc, n, (c0 - int(pc)) * gpc)); break
        else: print('earlier seed not within 1e7 draws')

if __name__ == '__main__':
    main()
