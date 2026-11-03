"""Odds with a seed lock vs blind for the Jr. Troopa route's rolls (jc_model.py, emulator-exact model).
Per gate: a random RNG state at the window's first frame (random seed, random coin phase); w(d) = the route outcome if
the deciding confirm lands on frame d. Plan (locked): the frame f in the window (WIN frames) that maximises
P(hit) with a press 50% on f, 25% one early, 25% one late (+-1) -- or exactly on f (EXACT). Blind: frame 0.
usage: python3 jc_odds.py TRIALS [WIN]"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc_model as JM
TR = int(sys.argv[1]) if len(sys.argv) > 1 else 1000; WIN = int(sys.argv[2]) if len(sys.argv) > 2 else 30
rnd = random.Random(12345)
GATES = {   # confirm event, frames to simulate after the confirm, outcome classes
    'T3 Bomb -> Close Call':        ('bomb_cc', 180, lambda R: R['cc'] < 30),
    'T4 Maple Syrup -> Close Call': ('syrup_cc', 164, lambda R: R['cc'] < 30),
    'T5 do nothing -> Close Call':  ('nothing_cc', 27, lambda R: R['cc'] < 30),
    'T6 Power Bounce':              ('pb', 160, lambda R: JM.pb_hits(R)),
}
def table(s, nc, ev, H):
    base = JM.Sim(s, nc); out = []
    for d in range(-1, WIN + 1):
        m = base.copy().add(d, ev); m.run(d, d + H); out.append(m.rolls); base.frame(d)
    return out          # index d+1
def plan(vals, score):
    best = (-1, 0)
    for f in range(WIN):
        p = 0.5 * score(vals[f + 1]) + 0.25 * score(vals[f]) + 0.25 * score(vals[f + 2])
        if p > best[0] + 1e-12: best = (p, f)
    return best
res = {}
for name, (ev, H, cls) in GATES.items():
    acc = {'blind': 0, 'pm1': 0, 'exact': 0, 'wait_pm1': 0, 'wait_exact': 0, 'none_in_window': 0}
    if ev == 'pb': acc.update({'blind5': 0, 'blind6': 0, 'pm1_5': 0, 'pm1_6': 0, 'ex5': 0, 'ex6': 0})
    for t in range(TR):
        s = rnd.getrandbits(32); nc = rnd.randrange(0, 48)
        R = table(s, nc, ev, H); v = [cls(r) for r in R]
        if ev == 'pb':
            # lexicographic: 5+ first (5 leaves 4 HP for Bombette's Bomb), then 6+ (kills him in the bounce)
            sc = lambda h: (1.0 if h >= 5 else 0.0) + (0.01 if h >= 6 else 0.0)
            p, f = plan(v, sc)
            acc['blind5'] += v[1] >= 5; acc['blind6'] += v[1] >= 6
            acc['pm1_5'] += 0.5 * (v[f + 1] >= 5) + 0.25 * (v[f] >= 5) + 0.25 * (v[f + 2] >= 5)
            acc['pm1_6'] += 0.5 * (v[f + 1] >= 6) + 0.25 * (v[f] >= 6) + 0.25 * (v[f + 2] >= 6)
            acc['wait_pm1'] += f
            ex = next((d for d in range(WIN) if v[d + 1] >= 6), None) or next((d for d in range(WIN) if v[d + 1] >= 5), None)
            ex = ex if ex is not None else 0
            acc['ex5'] += v[ex + 1] >= 5; acc['ex6'] += v[ex + 1] >= 6; acc['wait_exact'] += ex
        else:
            p, f = plan(v, float)
            acc['blind'] += v[1]; acc['pm1'] += p; acc['wait_pm1'] += f
            ex = next((d for d in range(WIN) if v[d + 1]), None)
            acc['exact'] += ex is not None; acc['wait_exact'] += ex or 0; acc['none_in_window'] += ex is None
    res[name] = {k: round(x / TR, 4) for k, x in acc.items()}
    print(name, res[name], flush=True)
json.dump({'trials': TR, 'win': WIN, 'res': res}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odds_w%d.json' % WIN), 'w'), indent=1)
