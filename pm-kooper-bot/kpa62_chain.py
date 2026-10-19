"""kpa_62 RTA chain test. Start: Mario placed with Laki settled (kpa62_place) at START. Then all inputs:
  1. hold down-right (stick 45, world +x) for N frames into the tower's west face, release 10 frames;
  2. tap up-left (stick 225, world -x) for K frames at magnitude MAG, release 15 frames;
  3. hold down-left (stick 135, world +z) for M frames, release;
  4. wait W frames (Laki settles), C-down (mount), ride idle 40, B (frame 0), hold down, C-down on frame T.
Reports which (N, M) clip, and Mario's x before mounting.
usage: kpa62_chain.py STATE OUT.jsonl   env: START (x,z), NS, MS, K, MAG, TS, W"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
st0, out = sys.argv[1], sys.argv[2]
ev = lambda k, d: [int(v) for v in os.environ.get(k, d).split(',')]
SX, SZ = (float(v) for v in os.environ.get('START', '-440,-85').split(','))
NS, MS, TS = ev('NS', '10,20,30,40,60,80'), ev('MS', '0,2,4,6,8'), ev('TS', '33,34,35')
K, MAG, W = int(os.environ.get('K', '3')), int(os.environ.get('MAG', '80')), int(os.environ.get('W', '40'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kch%d' % os.getpid())
tmp = '/dev/shm/pmbot/kch%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, SX, SZ); e.save(tmp + '.base')
fo = open(out, 'a')
for N in NS:
    for M in MS:
        e.load(tmp + '.base')
        for i in range(N): e.step(0, *stick_for(45, 80), 2)
        for i in range(10): e.step(0, 0, 0, 2)
        pw = player(e)
        for i in range(K): e.step(0, *stick_for(225, MAG), 2)
        for i in range(15): e.step(0, 0, 0, 2)
        for i in range(M): e.step(0, *stick_for(135, 80), 2)
        for i in range(W): e.step(0, 0, 0, 2)
        s = player(e)
        e.step(0x400, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        e.step(0x40, 0, 0, 2)
        dn = stick_for(90, 80); win = []
        for fr in range(1, max(TS) + 1):
            if fr in TS:
                e.save(tmp + '.h'); e.step(0x400, *dn, 2); ok = False
                for f in range(30):
                    e.step(0, *dn, 2); q = player(e)
                    if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
                if ok: win.append(fr)
                e.load(tmp + '.h')
            e.step(0, *dn, 2)
        rec = {'N': N, 'M': M, 'wall': [round(pw['x'], 3), round(pw['z'], 2)], 'stand': [round(s['x'], 3), round(s['z'], 2)], 'T': win}
        fo.write(json.dumps(rec) + '\n'); fo.flush(); print(rec, flush=True)
