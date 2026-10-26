"""tik_23 random search: ride Lakilester near the Super Hammer block with a random stick sequence (K segments of random
direction/length), optionally a 1-2 frame facing tap, then swap partners while riding (C-right, cursor, A). Logs runs
where Mario ends standing at y >= 25 (on the block). Inputs only after states/tik23_westzone.st.
usage: tik23_swap_random.py SEED N OUT.jsonl"""
import os, sys, json, random, math
from emu import *
from pm import *
from nav import go_to
seed, N, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sr%d' % os.getpid())
e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
STARTS = [(-280, 40), (-225, -20), (-280, -80), (-235, 25), (-235, -65)]
for s in STARTS:     # one mounted state per start
    e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
    go_to(e, *s, maxf=200, tol=2)
    for i in range(10): e.step(0, 0, 0, 2)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.save('/dev/shm/pmbot/sr%d_%d_%d.st' % (os.getpid(), s[0], s[1])); e.step(0, 0, 0, 1)
fo = open(out, 'a')
for n in range(N):
    s = rng.choice(STARTS)
    e.load('/dev/shm/pmbot/sr%d_%d_%d.st' % (os.getpid(), s[0], s[1])); e.step(0, 0, 0, 2)
    # aim roughly at the block centre (-280, -20), then random segments
    segs = []
    for k in range(rng.randint(1, 3)):
        a = rng.uniform(0, 2 * math.pi); m = rng.choice((30, 50, 80))
        segs.append((int(m * math.cos(a)), int(m * math.sin(a)), rng.randint(1, 14)))
    for sx, sy, d in segs:
        for i in range(d): e.step(0, sx, sy, 2)
    wait = rng.choice((0, 0, 1, 3))
    for i in range(wait): e.step(0, 0, 0, 2)
    p = player(e); pre = [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)]
    if not (-330 < p['x'] < -225 and -75 < p['z'] < 35):
        continue
    e.step(R_CBUTTON, 0, 0, 2)
    for i in range(20): e.step(0, 0, 0, 2)
    e.step(0, 0, 80, 2)
    for i in range(6): e.step(0, 0, 0, 2)
    e.step(A, 0, 0, 2)
    top = False
    for i in range(70):
        e.step(0, 0, 0, 2)
        q = player(e)
        if q['y'] > 25 and q['action'] in (0, 1, 2, 10): top = True
    q = player(e)
    r = {'start': s, 'segs': segs, 'wait': wait, 'pre': pre, 'after': [round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']], 'top': top}
    fo.write(json.dumps(r) + '\n'); fo.flush()
    if top or q['y'] > 25:
        print('ON TOP', r, flush=True)
        e.save('states/tik23_ontop_rand_%d_%d.st' % (seed, n)); e.step(0, 0, 0, 1)
