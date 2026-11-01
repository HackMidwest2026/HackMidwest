# (run from the emulator working dir, bot1/) """Fit the Super Charge energy_in_out model to logged runs (with per-frame seeds). Model per instance: created on
frame c (draws: rand(360), then per part rand(10), rand(period)); parts update every frame from frame c+u (u=0/1):
counter++, on reaching `period` reset and draw rand(359); removed on frame r (no updates from then on).
Effect updates run after the coin draw. Instances update in creation order unless rev."""
import json, glob, sys, itertools
from rngsim import *
def sim(seed, coin_frames, end, model):
    (cA, cB, u, rA, rB, rev) = model
    s = seed; toks = {}; inst = []
    for f in range(end):
        out = []
        for c in (cA, cB):
            if f == c:
                s, _ = rand_int(s, 360); out.append(360); parts = []
                for i in range(10):
                    s, _ = rand_int(s, 10); out.append(10); s, v = rand_int(s, 10); out.append(10); parts.append(-v)
                inst.append({'c': c, 'r': rA if c == cA else rB, 'p': parts})
        if f in coin_frames: s, _ = rand_int(s, 100); out.append('C')
        order = inst[::-1] if rev else inst
        for I in order:
            if f >= I['c'] + u and f < I['r']:
                for i in range(10):
                    I['p'][i] += 1
                    if I['p'][i] >= 10: I['p'][i] = 0; s, _ = rand_int(s, 359); out.append(359)
        s = adv(s)
        if out: toks[f] = out
    return s, toks
runs = []
for fn in sorted(glob.glob('data/jrs_*.json')):
    r = json.load(open(fn)); C = dict((n, f) for f, n in r['confirms']); f0 = C['T5 Charge']; N = 80
    log = {f - f0: ['C' if t == 'C' else t[0] for t in r['log'][f]] for f in range(f0, f0 + N) if r['log'][f]}
    coin = {f for f, t in log.items() if 'C' in t}
    runs.append((r['seeds'][f0], coin, log, r['seeds'][f0 + N], fn))
best = []
for model in itertools.product([13], [16], [0, 1], range(40, 70), range(40, 70), [0, 1]):
    ok = 0
    for seed, coin, log, s_end, fn in runs:
        s, toks = sim(seed, coin, 80, model)
        if s == s_end and toks == log: ok += 1
    if ok: best.append((ok, model))
best.sort(reverse=True); print('runs', len(runs), 'best models (matched runs, (cA, cB, firstUpdate, removeA, removeB, reversed)):', best[:8])
