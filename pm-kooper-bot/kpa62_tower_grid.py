"""kpa_62 tower clip map (RAM): Mario at (x, 50, z) on the y-50 ledge beside the tower (collider 23), Laki's moveSpeed
forced to S on the C-down frame; does the mount end with Mario inside the tower outline (collider 1)?
usage: kpa62_tower_grid.py STATE PART NPARTS OUT.jsonl"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
TOWER = [(-365, -5), (-394, -29), (-409, -55), (-414, -75), (-415, -96), (-408, -108), (-390, -112), (-376, -103),
         (-357, -79), (-341, -48), (-340, -20), (-348, -4)]
def inside(x, z, poly=TOWER):
    c = False
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0): c = not c
    return c
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ktg%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/ktg%d.st' % os.getpid(); e.save(base)
jobs = [(x, z) for x in range(-428, -363, 3) for z in range(-46, 31, 3) if not inside(x, z)][PART::NP]
fo = open(out, 'a'); n = hits = 0
for (x, z) in jobs:
    for S in range(4, 44, 2):
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 50.0); e.wf32(PLAYER + PS_POS + 8, z)
        e.step(0, 0, 0, 2)
        if abs(player(e)['y'] - 50) > 1 or e.s16(COLLISION + 2) != 23: break
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2)
        for i in range(24):
            # hold the speed until the mount has read it (RIDE_STATE_MOUNT_1 runs ~5 frames after the C-down)
            if e.u8(PLAYER + PS_ACTION) != 33 or i < 6: e.wf32(a + 0x18, S)
            e.step(0, 0, 0, 2)
        p = player(e); n += 1
        ok = inside(p['x'], p['z'])
        fo.write(json.dumps({'x': x, 'z': z, 'S': S, 'end': [p['x'], p['y'], p['z']], 'in': ok}) + '\n'); hits += ok
print('done part', PART, n, 'mounts', hits, 'inside tower')
