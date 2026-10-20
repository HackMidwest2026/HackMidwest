"""dgb_01: full-mount clip map. For each spot and Laki speed S (forced until the mount reads it), the mount plays out
for 40 frames; out of bounds = Mario below y -30 or past the outer walls. Slower than dgb01_mount_map.py but it
includes Laki's flight to the target, which can push Mario back inside.
usage: dgb01_full_map.py STATE PART NPARTS OUT.jsonl   env: XR, ZR, SR (start,stop,step)"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = lambda k, d: (lambda a, b, c: [a + i * c for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS, SS = rng('XR', '-340,-40,10'), rng('ZR', '340,490,10'), rng('SR', '150,400,5')
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/dfm%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/dfm%d.st' % os.getpid(); e.save(base)
fo = open(out, 'a'); n = hits = 0
for (x, z) in [(x, z) for x in XS for z in ZS][PART::NP]:
    row = []
    for S in SS:
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
        for i in range(3): e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] != 0 or abs(p['y']) > 1 or abs(p['x'] - x) > .01: break
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2)
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: break
            e.wf32(a + 0x18, S); e.step(0, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        q = player(e); n += 1
        o = q['y'] < -30 or abs(q['x']) > 500 or abs(q['z']) > 500; hits += o
        row.append([S, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), int(o)])
    if row: fo.write(json.dumps({'x': x, 'z': z, 'r': row}) + '\n'); fo.flush()
print('done part', PART, n, 'mounts', hits, 'out of bounds')
