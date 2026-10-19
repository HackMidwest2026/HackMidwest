"""kpa_62 mount-target map (RAM): Mario standing at (x, 50, z) on the y-50 ledge beside the tower (collider 23), Laki's
moveSpeed forced to S until RIDE_STATE_MOUNT_1 runs (the frame Mario's action becomes RIDE). Records Laki's moveToPos,
which is where Mario lands, and whether it is inside the tower outline.
usage: kpa62_mount_map.py STATE PART NPARTS OUT.jsonl   env: XR, ZR, SR as start,stop,step"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = lambda k, d: (lambda a, b, c: [a + i * c for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS, SS = rng('XR', '-400,-360,1'), rng('ZR', '-10,40,1'), rng('SR', '4,40,1')
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kmm%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/kmm%d.st' % os.getpid(); e.save(base)
fo = open(out, 'a'); n = hits = 0
for (x, z) in [(x, z) for x in XS for z in ZS if not inside_tower(x, z)][PART::NP]:
    row = []
    for S in SS:
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 50.0); e.wf32(PLAYER + PS_POS + 8, z)
        e.step(0, 0, 0, 2)
        p = player(e)
        if abs(p['y'] - 50) > 1 or e.s16(COLLISION + 2) != 23 or abs(p['x'] - x) > .01 or abs(p['z'] - z) > .01: break
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2); t = None
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: t = (e.f32(a + 0x60), e.f32(a + 0x68)); break
            e.wf32(a + 0x18, S); e.step(0, 0, 0, 2)
        n += 1
        if t is None: continue
        ins = inside_tower(*t); hits += ins
        row.append([S, round(t[0], 2), round(t[1], 2), int(ins)])
    if row: fo.write(json.dumps({'x': x, 'z': z, 'r': row}) + '\n'); fo.flush()
print('done part', PART, n, 'mounts', hits, 'inside')
