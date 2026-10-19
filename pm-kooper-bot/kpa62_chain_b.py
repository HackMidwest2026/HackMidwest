"""kpa_62 RTA chain B: Mario placed with Laki settled at START, push up-left (stick 225, world -x) into the raised
platform's (c21) east face for N frames, release 10, run K frames with raw stick TX,TY (default down-right notch = world
+x), release, settle 40, mount, ride 40, B, hold down, C-down on frame 34. Prints the standing spot and the result.
usage: kpa62_chain_b.py STATE 'N=..,K=..,TX=..,TY=..' ...   env: START (x,z)"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
SX, SZ = (float(v) for v in os.environ.get('START', '-470,-60').split(','))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcb%d' % os.getpid())
base = '/dev/shm/pmbot/kcb%d.base' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, SX, SZ); e.save(base)
t0 = stick_for(45, 80)
for spec in sys.argv[2:]:
    c = dict(N=10, K=9, TX=t0[0], TY=t0[1], T=34)
    c.update({k: int(v) for k, v in (kv.split('=') for kv in spec.split(','))})
    e.load(base)
    for i in range(c['N']): e.step(0, *stick_for(225, 80), 2)
    for i in range(10): e.step(0, 0, 0, 2)
    w = player(e)
    for i in range(c['K']): e.step(0, c['TX'], c['TY'], 2)
    for i in range(55): e.step(0, 0, 0, 2)
    s = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = stick_for(90, 80)
    for fr in range(1, c['T']): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2); ok = False
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
    print(spec, 'wall (%.3f %.2f) stand (%.3f %.2f)' % (w['x'], w['z'], s['x'], s['z']), 'CLIP' if ok else 'no', flush=True)
