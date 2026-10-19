"""kpa_62 RTA chain sensitivity: runs the chain (push right N, tap up-left K, walk raw stick WSTICK for M frames, settle
W, mount, ride R, B, hold down, C-down on frame 34) for variations given on the command line as key=value,...
usage: kpa62_chain_sens.py STATE 'N=90,M=7,WX=-57,WY=-57,R=40,W=40' ..."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcs%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, -440.0, -85.0); e.save('/dev/shm/pmbot/kcs%d.base' % os.getpid())
w0 = stick_for(135, 80)
for spec in sys.argv[2:]:
    c = dict(N=90, K=3, M=7, WX=w0[0], WY=w0[1], R=40, W=40, T=34)
    c.update({k: int(v) for k, v in (kv.split('=') for kv in spec.split(','))})
    e.load('/dev/shm/pmbot/kcs%d.base' % os.getpid())
    for i in range(c['N']): e.step(0, *stick_for(45, 80), 2)
    for i in range(10): e.step(0, 0, 0, 2)
    for i in range(c['K']): e.step(0, *stick_for(225, 80), 2)
    for i in range(15): e.step(0, 0, 0, 2)
    for i in range(c['M']): e.step(0, c['WX'], c['WY'], 2)
    for i in range(c['W']): e.step(0, 0, 0, 2)
    s = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(c['R']): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = stick_for(90, 80)
    for fr in range(1, c['T']): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2); ok = False
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
    print(spec, 'stand (%.3f %.2f)' % (s['x'], s['z']), 'CLIP' if ok else 'no', flush=True)
