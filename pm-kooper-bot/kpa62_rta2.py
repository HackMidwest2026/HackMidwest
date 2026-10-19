"""kpa_62 RTA search, version 2. Walk from the seed at stick angle WA for WK frames (start spot), mount, ride idle RF frames
(or at stick angle R, R = -1: idle), dismount (B), wait W frames, then hold stick angle A at magnitude M; on every frame h where Mario stands on the y-50 ledge (collider 23) with x in
[-388, -372] (Mario still moves on the C-down frame), try C-down there (keep holding A) and check whether Mario ends inside the tower. Prints the working h.
usage: kpa62_rta2.py STATE PART NPARTS OUT.jsonl   env: STARTS (WA:WK;...), RFS, RIDES, WAITS, ANGS, MAGS, HMAX"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ev = lambda k, d: [int(v) for v in os.environ.get(k, d).split(',')]
RIDES, ANGS, MAGS = ev('RIDES', '-1'), ev('ANGS', ','.join(str(a) for a in range(0, 360, 15))), ev('MAGS', '80,45')
HMAX = int(os.environ.get('HMAX', '90'))
RFS, WAITS = ev('RFS', '20,30,40,50,60'), ev('WAITS', '0,3,6,10')
STARTS = [tuple(int(v) for v in t.split(':')) for t in os.environ.get('STARTS', '0:0;90:6').split(';')]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62b%d' % os.getpid())
tmp = '/dev/shm/pmbot/k62b%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.seed')
L = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(out, 'a'); tot = 0
for (WA, WK, RF, R, W) in [(a, k, rf, r, w) for (a, k) in STARTS for rf in RFS for r in RIDES for w in WAITS][PART::NP]:
    e.load(tmp + '.seed')
    for i in range(WK): e.step(0, *stick_for(WA, 80), 2)
    for i in range(6): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(RF): e.step(0, *(stick_for(R, 80) if R >= 0 else (0, 0)), 2)
    e.step(0x40, 0, 0, 2)
    for i in range(W): e.step(0, 0, 0, 2)
    d = player(e); e.save(tmp + '.dis')
    for A in ANGS:
        for M in MAGS:
            e.load(tmp + '.dis'); st = stick_for(A, M); win = []
            for h in range(HMAX):
                e.step(0, *st, 2); p = player(e)
                if os.environ.get("DBG"): print(h, round(p["x"], 1), round(p["y"], 1), round(p["z"], 1), e.s16(COLLISION + 2))
                if not (abs(p["y"] - 50) < .5 and e.s16(COLLISION + 2) == 23 and -388 <= p["x"] <= -372): continue
                e.save(tmp + '.h'); l = L()
                e.step(0x400, *st, 2); ok = False
                for f in range(30):
                    e.step(0, *st, 2); q = player(e)
                    if f > 18 and inside_tower(q['x'], q['z']): ok = True; break
                if ok:
                    win.append(h + 1)
                    fo.write(json.dumps({'WA': WA, 'WK': WK, 'RF': RF, 'W': W, 'R': R, 'dis': [d['x'], d['z']], 'A': A, 'M': M, 'h': h + 1, 'at': [p['x'], p['z']], 'laki': [l['x'], l['y'], l['z']]}) + '\n'); fo.flush()
                e.load(tmp + '.h')
            tot += len(win)
            if win: print('start %d:%d ride %d/%d W %d dis (%.1f %.1f) A %d M %d -> C-down on hold frame %s' % (WA, WK, RF, R, W, d['x'], d['z'], A, M, win), flush=True)
print('done part', PART, tot, 'hits')
