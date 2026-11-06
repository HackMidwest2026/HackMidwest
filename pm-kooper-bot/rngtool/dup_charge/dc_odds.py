"""Odds with a Charge-ray lock vs blind for the Duplighost copies (dc_model.py, emulator-checked model).
Per trial: a random RNG state at the window's first frame (random seed, next coin 0..47 frames ahead; the rays are
long over by then: they end at Charge +61, the earliest Do Nothing confirm is ~+120). c(d) = copies if the Do Nothing
confirm lands on frame d (2 = 2 or fewer).
  blind:  frame 0 (any frame: each frame is a fresh draw).
  locked: the frame f in the WIN-frame window chosen for the target, pressed 50% on f, 25% one early, 25% one late
          (PM1) or exactly (EXACT).  Targets: 'all4' = max P(4), ties -> P(3+);  'safe3' = max P(3+), ties -> P(4).
Also: the per-frame rates, run lengths of all-4 frames, the chosen frame's mean offset into the window (added wait).
usage: python3 dc_odds.py TRIALS [WIN ...]   -> prints, and writes odds.json next to this file"""
import sys, os, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dc_model as DM
TR = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
WINS = [int(x) for x in sys.argv[2:]] or [30, 60, 120]
WMAX = max(WINS)
rnd = random.Random(240224)
def pick(c, W, key):
    best = None
    for f in range(W):
        n = (c[f], c[f + 1], c[f + 2])        # f-1, f, f+1 (c is indexed from frame -1)
        p4 = 0.25 * (n[0] == 4) + 0.5 * (n[1] == 4) + 0.25 * (n[2] == 4)
        p3 = 0.25 * (n[0] >= 3) + 0.5 * (n[1] >= 3) + 0.25 * (n[2] >= 3)
        k = (p4, p3) if key == 'all4' else (p3, p4)
        if best is None or k > best[0]: best = (k, f, p4, p3)
    return best
acc = {W: {'all4': [0, 0, 0], 'safe3': [0, 0, 0], 'ex4': [0, 0], 'ex3': [0, 0], 'none4': 0} for W in WINS}
blind4 = blind3 = 0; runs = {}; per4 = per3 = nfr = 0
for t in range(TR):
    s = rnd.getrandbits(32); nc = rnd.randrange(0, 48)
    c = DM.table(s, nc, -1, WMAX + 2)
    blind4 += c[1] == 4; blind3 += c[1] >= 3
    per4 += sum(x == 4 for x in c[1:61]); per3 += sum(x >= 3 for x in c[1:61]); nfr += 60
    r = 0
    for x in c[1:61] + [0]:
        if x == 4: r += 1
        elif r: runs[r] = runs.get(r, 0) + 1; r = 0
    for W in WINS:
        a = acc[W]
        for key in ('all4', 'safe3'):
            k, f, p4, p3 = pick(c, W, key); a[key][0] += p4; a[key][1] += p3; a[key][2] += f
        e4 = next((f for f in range(W) if c[f + 1] == 4), None); e3 = next((f for f in range(W) if c[f + 1] >= 3), None)
        a['ex4'][0] += e4 is not None; a['ex4'][1] += e4 if e4 is not None else W; a['none4'] += e4 is None
        a['ex3'][0] += e3 is not None; a['ex3'][1] += e3 if e3 is not None else W
res = {'trials': TR, 'blind': {'p4': blind4 / TR, 'p3plus': blind3 / TR}, 'per_frame': {'p4': per4 / nfr, 'p3plus': per3 / nfr},
       'all4_run_lengths': {str(k): v for k, v in sorted(runs.items())}, 'windows': {}}
for W in WINS:
    a = acc[W]
    res['windows'][str(W)] = {
        'pm1_target_all4': {'p4': a['all4'][0] / TR, 'p3plus': a['all4'][1] / TR, 'mean_offset_frames': a['all4'][2] / TR},
        'pm1_target_safe3': {'p4': a['safe3'][0] / TR, 'p3plus': a['safe3'][1] / TR, 'mean_offset_frames': a['safe3'][2] / TR},
        'exact_all4': {'p4': a['ex4'][0] / TR, 'mean_offset_frames': a['ex4'][1] / TR},
        'exact_3plus': {'p3plus': a['ex3'][0] / TR, 'mean_offset_frames': a['ex3'][1] / TR}}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(HERE, 'odds.json'), 'w'), indent=1)
