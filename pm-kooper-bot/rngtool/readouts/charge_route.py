"""Route clip end to end, with a clock that may slip between windows (console lag frames during loads):
each window where the status-bar coin is on screen gets its own offset d (game frames, -3..+3) between the capture
clock and the model's frames; the predicted coin draws (shine / normal) must explain every flash and every
non-flash in the window. The Time Out confirm frame is read in the T2-menu window's clock.
usage: charge_route.py HUD.npz V0 SEEDHEX Q|Q1,Q2|QLO-QHI CAP_SPINY_A CAP_TIMEOUT_A [R=2.0058]   (env IMPLO/IMPHI, F2D: Spiny confirm offsets)"""
import sys, json, subprocess, numpy as np, os
from collections import defaultdict
hud, V0, seed = sys.argv[1], int(sys.argv[2]), sys.argv[3]
qs = [int(x) for x in sys.argv[4].split(',')] if '-' not in sys.argv[4] else list(range(int(sys.argv[4].split('-')[0]), int(sys.argv[4].split('-')[1]) + 1))
sa, ta = int(sys.argv[5]), int(sys.argv[6]); Rr = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0058
h = np.load(hud); white, gold = h['white'], h['gold']
g = lambda i: (i - V0) / Rr
present = gold > 0.3; flash = present & (white > 0.03)
def runs(m):
    out = []; i = 0
    while i < len(m):
        if m[i]:
            j = i
            while j + 1 < len(m) and m[j + 1]: j += 1
            out.append((i, j)); i = j + 1
        else: i += 1
    return out
fl = [g((a + b) / 2) for a, b in runs(flash)]
wins = [(g(a) + 1, g(b) - 1) for a, b in runs(present) if b - a > 6]
F3c = g(ta)
wins = [w for w in wins if w[0] > 0 and w[0] < F3c]            # windows after the Charge, up to the Time Out confirm
print('windows', [(round(a, 1), round(b, 1)) for a, b in wins], 'flashes', [round(x, 1) for x in fl if 0 < x < F3c], 'TO confirm (raw clock) %.2f' % F3c)
res = defaultdict(list)
for f2d in [int(x) for x in os.environ.get('F2D', '-1,0,1').split(',')]:
    F2 = round(g(sa)) + f2d
    arg = json.dumps({'seed': seed, 'qs': qs, 'spiny': F2, 'timeout': round(F3c) + 3, 'near': 15,
                      'impLo': int(os.environ.get('IMPLO', 40)), 'impHi': int(os.environ.get('IMPHI', 175))})
    out = json.loads(subprocess.run(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charge_carry.js'), arg], capture_output=True, text=True, check=True).stdout)
    for o in out:
        if 'draws' not in o: continue
        offs = []
        for a, b in wins:
            best = None
            for d in range(-3, 4):
                ok = True; n = 0
                for f, sh in o['draws']:
                    m = f + 6.5 + d
                    if a <= m - 1.5 and m + 1.5 <= b:
                        n += 1
                        if sh != any(abs(m - x) <= 1.5 for x in fl): ok = False
                for x in fl:
                    if a <= x <= b and not any(sh and abs(f + 6.5 + d - x) <= 1.5 for f, sh in o['draws']): ok = False
                if ok and (best is None or abs(d) < abs(best[0])): best = (d, n)
            offs.append(best)
        if all(offs):
            dT2 = offs[-1][0]; F3 = round(F3c - dT2)    # model frame of the confirm, in the last window's clock
            base = round(F3c) + 3
            wk = o['workingOffsets']; okF3 = (F3 - base) in wk
            key = (tuple(f for f, sh in o['draws'] if sh), o['branch'], o['guard'], tuple(x[0] for x in offs), F3, okF3, tuple(base + x - F3 for x in wk))
            res[key].append((F2, o['imp'], o['q']))
print('distinct RNG outcomes that fit every window:', len(res))
for k, v in res.items():
    print('  shine draws %s | Bowser %s guard %s | window offsets %s | Time Out confirm frame %d -> %s | working frames rel. confirm: %s | %d hypotheses, (Spiny confirm, impact, q) e.g. %s' % (
        list(k[0]), k[1], k[2], list(k[3]), k[4], 'WORKS' if k[5] else 'fails', list(k[6]), len(v), v[:3]))
