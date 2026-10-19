"""kpa_17 jail: RAM brute force of the Laki mount "teleport". Mario is placed at (x, y, z) inside the cell, Laki's
moveSpeed is set to S on the C-down frame, and the mount is played out. The mount target is Mario's position moved by
S along -z, +x, +z, -x in turn, each move stopped by walls (RIDE_STATE_MOUNT_1), so the end point depends on where
walls block. Hit = Mario on the exit floor (collider 14), east of the doorway face (x > 1200), or a map change.
usage: kpa17_mount_grid.py STATE PART NPARTS OUT.jsonl"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kmg%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/kmg%d.st' % os.getpid(); e.save(base)
jobs = []
for x in range(1100, 1189, 4):
    for z in range(-640, -509, 5):
        for y in (30, 60, 95, 130):
            jobs.append((x, y, z))
jobs = jobs[PART::NP]
speeds = list(range(10, 100, 10)) + list(range(100, 420, 25))
fo = open(out, 'a'); n = 0; hits = 0
for (x, y, z) in jobs:
    for S in speeds:
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2)
        why = None; ex = None
        for i in range(30):
            e.wf32(a + 0x18, S) if i < 4 else None
            e.step(0, 0, 0, 2)
            if e.s16(GAME_MODE) != GM_WORLD: why = 'map change %s' % (where(e),); break
            p = player(e); fl = e.s16(COLLISION + 2)
            if fl == 14: why = 'exit floor'; break
            if p['x'] > 1200.5 and -600 < p['z'] < -550: why = 'past doorway face x %.1f' % p['x']; break
        n += 1
        if why:
            p = player(e); hits += 1
            fo.write(json.dumps({'x': x, 'y': y, 'z': z, 'S': S, 'why': why, 'end': [p['x'], p['y'], p['z']]}) + '\n'); fo.flush()
print('done part', PART, n, 'tries', hits, 'hits')
