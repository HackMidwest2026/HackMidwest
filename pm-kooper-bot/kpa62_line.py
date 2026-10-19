"""kpa_62: the dismount -> hold down -> remount clip from Mario standing on the y-60 platform with Laki settled
beside him (kpa62_place.place). For each spot: mount (C-down), ride idle 40 frames, dismount (B = frame 0), hold notch D,
press C-down on frame T (every T in TS). A hit = Mario ends inside the tower outline at y > 40.
usage: kpa62_line.py STATE PART NPARTS OUT.jsonl   env: XR, ZR (start,stop,step), D, TS (a,b), RIDE"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = lambda k, d: (lambda a, b, c: [round(a + i * c, 4) for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS = rng('XR', '-446,-436,0.25'), rng('ZR', '-60,-30,2')
D = int(os.environ.get('D', '90')); T0, T1 = (int(v) for v in os.environ.get('TS', '20,45').split(','))
RIDE = int(os.environ.get('RIDE', '40'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kln%d' % os.getpid())
tmp = '/dev/shm/pmbot/kln%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.base')
fo = open(out, 'a'); hits = 0; n = 0
for (x, z) in [(x, z) for z in ZS for x in XS][PART::NP]:
    e.load(tmp + '.base'); place(e, x, z)
    s = player(e)
    if abs(s['y'] - 60) > .5 or abs(s['x'] - x) > .01: continue
    e.step(0x400, 0, 0, 2)
    for i in range(RIDE): e.step(0, 0, 0, 2)
    r = player(e)
    e.step(0x40, 0, 0, 2)
    st = stick_for(D, 80); win = []; n += 1
    for fr in range(1, T1 + 1):
        if fr >= T0:
            e.save(tmp + '.h')
            e.step(0x400, *st, 2); ok = False
            for f in range(30):
                e.step(0, *st, 2); q = player(e)
                if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
            if ok: win.append(fr)
            e.load(tmp + '.h')
        e.step(0, *st, 2)
    if win:
        hits += 1
        rec = {'spot': [x, z], 'ride': [r['x'], r['z']], 'D': D, 'T': win}
        fo.write(json.dumps(rec) + '\n'); fo.flush(); print(rec, flush=True)
print('done part', PART, n, 'spots', hits, 'hits')
