# (run from the emulator working dir, bot1/) """Build per-action schedules from run 0 (draw ranges per frame after the confirm; effect-overlay callers (0xE0...)
run after the coin, everything else before) plus the Super Charge energy_in_out model, then simulate every run from
the seed at the T3 Bomb confirm through T6's confirm using only the confirm frames, and compare with the game."""
import json, glob
from rngsim import *
runs = [json.load(open(f)) for f in sorted(glob.glob('data/jrs_*.json'))]
def segment(r, name):
    C = r['confirms']; i = [n for _, n in C].index(name); f0 = C[i][0]; f1 = C[i + 1][0] if i + 1 < len(C) else len(r['log'])
    return f0, f1
SCHED = {}
for name in ['T3 Bomb', 'T4 Bomb', 'T4 Maple', 'T5 Nothing']:
    f0, f1 = segment(runs[0], name); ev = {}
    for f in range(f0, f1):
        toks = [t for t in runs[0]['log'][f] if t != 'C']
        if toks: ev[f - f0] = {'all': [t[0] for t in toks], 'split': None}
    # where a coin fell on that frame in some run, the coin's position gives the split (draws before the coin)
    for r in runs:
        g0, g1 = segment(r, name)
        for f in range(g0, g1):
            toks = r['log'][f]
            if 'C' in toks and (f - g0) in ev: ev[f - g0]['split'] = toks.index('C')
    for o, d in ev.items():
        k = d['split'] if d['split'] is not None else len(d['all'])     # default: creation draws, before the coin
        d['pre'], d['post'] = d['all'][:k], d['all'][k:]
    SCHED[name] = ev
    print(name, 'frames with draws', len(ev), 'order seen for', sum(1 for d in ev.values() if d['split'] is not None), 'post-coin draws at', [(o, len(d['post'])) for o, d in ev.items() if d['post']][:10])
def check(r):
    C = r['confirms']; f0 = C[0][0]; fT6 = [f for f, n in C if n == 'T6 Bounce'][0]; writes = [f for f, n in C if n in ('T4 Maple', 'T5 Nothing')]
    nc = next(f for f in range(f0, len(r['log'])) if 'C' in r['log'][f]); s = r['seeds'][f0]; inst = []; evs = {}
    for g0, name in C:
        if name in SCHED:
            for o, d in SCHED[name].items(): e = evs.setdefault(g0 + o, {'pre': [], 'post': []}); e['pre'] += d['pre']; e['post'] += d['post']
        if name == 'T5 Charge':
            for c, rm in ((13, 58), (16, 61)): evs.setdefault(g0 + c, {'pre': [], 'post': []}).setdefault('eio', []).append(g0 + rm)
    for f in range(f0, fT6):
        if s != r['seeds'][f]:
            if any(0 <= w - f <= 45 for w in writes): s = r['seeds'][f]
            else: return 'MISMATCH +%d (%s)' % (f - f0, [n for g, n in C if g <= f][-1])
        if 'C' in r['log'][f] and f != nc: return 'coin timing differs at +%d (sim expected +%d) in %s' % (f - f0, nc - f0, [n for g, n in C if g <= f][-1])
        e = evs.get(f, {})
        for mx in e.get('pre', []): s, _ = rand_int(s, mx)
        for rm in e.get('eio', []):
            s, _ = rand_int(s, 360); p = []
            for i in range(10): s, _ = rand_int(s, 10); s, v = rand_int(s, 10); p.append(-v)
            inst.append([f, rm, p])
        if f == nc: s, v = rand_int(s, 100); nc = f + (48 if v >= 70 else 24)
        for mx in e.get('post', []): s, _ = rand_int(s, mx)
        for c, rm, p in inst:
            if c <= f < rm:
                for i in range(10):
                    p[i] += 1
                    if p[i] >= 10: p[i] = 0; s, _ = rand_int(s, 359)
        s = adv(s)
    return 'all frames match to the T6 confirm' + (' (end seed match)' if s == r['seeds'][fT6] else ' (end differs)')
if __name__ == '__main__':
    for r in runs: print('%08x d%d' % (r['seed'], r['dseed']), check(r))
