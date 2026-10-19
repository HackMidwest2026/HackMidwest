"""kpa_62 RTA setup search for the Laki remount clip into the tower. From the seed spot, walk at stick angle D1 for
N1 frames (a wall / corner gives a repeatable spot), mount (C-down), ride idle 40 frames, dismount (B), wait W frames,
then hold stick angle D2 and press C-down after h frames (h = 0..HMAX), keep holding 25 frames. Hit = Mario inside the
tower outline in the last 12 frames. Each (start, W, D2) prints its window of working h.
usage: kpa62_rta.py STATE PART NPARTS OUT.jsonl
env: D1S, N1S, WAITS, D2S, HMAX"""
import json, os, sys
os.environ.setdefault('ROOM', 'kpa62')
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ev = lambda k, d: [int(v) for v in os.environ.get(k, d).split(',')]
D1S, N1S, WAITS, D2S = ev('D1S', '0,45,90,135,180,225,270,315'), ev('N1S', '0,60'), ev('WAITS', '0,5'), ev('D2S', ','.join(str(a) for a in range(0, 181, 15)))
HMAX = int(os.environ.get('HMAX', '60'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62rta%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
tmp = '/dev/shm/pmbot/k62rta%d' % os.getpid(); e.save(tmp + '.base')
jobs = [(d1, n1, w, d2) for d1 in D1S for n1 in N1S for w in WAITS for d2 in D2S if not (n1 == 0 and d1 != D1S[0])][PART::NP]
fo = open(out, 'a'); hits = 0
for (d1, n1, w, d2) in jobs:
    e.load(tmp + '.base')
    for i in range(n1): e.step(0, *stick_for(d1, 80), 2)
    for i in range(6): e.step(0, 0, 0, 2)
    s = player(e)
    if abs(s['y'] - 60) > 2: continue
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for i in range(w): e.step(0, 0, 0, 2)
    st = stick_for(d2, 80); win = []
    for h in range(HMAX + 1):
        e.save(tmp + '.h')
        p = player(e)
        e.step(0x400, *st, 2); ok = False
        for f in range(35):
            e.step(0, *st, 2) if f < 25 else e.step(0, 0, 0, 2)
            q = player(e)
            if f >= 23 and inside_tower(q['x'], q['z']): ok = True; break
        if ok: win.append(h); fo.write(json.dumps({'start': [s['x'], s['z']], 'D1': d1, 'N1': n1, 'W': w, 'D2': d2, 'h': h, 'at': [p['x'], p['y'], p['z']], 'end': [q['x'], q['y'], q['z']]}) + '\n'); fo.flush()
        e.load(tmp + '.h'); e.step(0, *st, 2)
    hits += len(win)
    if win: print('start (%.1f %.1f) D1 %d N1 %d W %d D2 %d -> h %s' % (s['x'], s['z'], d1, n1, w, d2, win), flush=True)
print('done part', PART, len(jobs), 'jobs', hits, 'hits')
