"""kpa_62 remount clip, two-notch programs. Dismount spots: ride Laki from the seed at stick angle RA for RK frames, then
dismount (B = frame 0). Program: from frame 1 hold notch D1 for N1 frames, then hold notch D2 (e.g. 'right' into the
tower's south-west face, where Mario creeps toward the corner), press C-down on frame T. Records every working T.
usage: kpa62_rta5.py STATE PART NPARTS OUT.jsonl   env: RIDES (RA:RK;...), TS (a,b)"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
T0, T1 = (int(v) for v in os.environ.get('TS', '26,46').split(','))
RIDES = [tuple(int(v) for v in t.split(':')) for t in os.environ['RIDES'].split(';')] if os.environ.get('RIDES') else \
        [(-1, 0)] + [(a, k) for a in range(0, 360, 45) for k in (5, 10, 15, 20, 30)]
NOTCH = list(range(0, 360, 45))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62e%d' % os.getpid())
tmp = '/dev/shm/pmbot/k62e%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.seed')
def near(p): return abs(p['y'] - 50) < 3 and -392 <= p['x'] <= -370 and -10 <= p['z'] <= 30
def try_cdown(st):
    e.step(0x400, *st, 2)
    for f in range(30):
        e.step(0, *st, 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
fo = open(out, 'a'); seen = set(); good = 0
for (ra, rk) in RIDES[PART::NP]:
    e.load(tmp + '.seed')
    e.step(0x400, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    for i in range(rk): e.step(0, *stick_for(ra, 80), 2)
    for i in range(8): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)                                   # dismount = frame 0
    d = player(e); key = (round(d['x'] / 3), round(d['z'] / 3))
    if key in seen: continue
    seen.add(key); e.save(tmp + '.dis')
    for D1 in NOTCH:
        for N1 in range(0, 31):
            for D2 in NOTCH:
                if N1 == 0 and D1 != NOTCH[0]: continue
                if D2 == D1 and N1 > 0: continue
                e.load(tmp + '.dis'); win = []; reached = False
                for fr in range(1, T1 + 1):
                    st = stick_for(D1 if fr <= N1 else D2, 80)
                    if fr >= T0 and near(player(e)):
                        reached = True; e.save(tmp + '.h')
                        if try_cdown(st): win.append(fr)
                        e.load(tmp + '.h')
                    e.step(0, *st, 2)
                if win:
                    good += 1
                    rec = {'ride': [ra, rk], 'dis': [d['x'], d['y'], d['z']], 'D1': D1, 'N1': N1, 'D2': D2, 'T': win}
                    fo.write(json.dumps(rec) + '\n'); fo.flush()
                    if len(win) > 1: print(rec, flush=True)
print('done part', PART, len(seen), 'dismount spots', good, 'programs with hits')
