"""kpa_133 (Bowser's Castle flood room, left): RAM brute force of the Laki mount "teleport" from the front floor.
Mario is placed at (x, y, z), Laki's moveSpeed is set to S on the C-down frame, the mount plays out, and Mario's final
position is logged. Mount target = Mario's position moved by S along -z, +x, +z, -x (each move a single ray at y+10
that stops at the first wall). Interesting = ends behind the front faces of the back blocks (z < 45), out of the room
(|x| > 400 away from the exit floors, z > 205), or anywhere with y >= 100.
usage: kpa133_mount_grid.py STATE PART NPARTS OUT.jsonl"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k3g%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/k3g%d.st' % os.getpid(); e.save(base)
y0 = player(e)['y']
jobs = [(x, y0 + dy, z) for x in range(-390, 391, 10) for z in range(55, 196, 10) for dy in (0, 14, 27)][PART::NP]
speeds = [10, 20, 30, 45, 60, 80, 100, 130, 160, 200, 250, 300, 400]
fo = open(out, 'a'); n = hits = 0
for (x, y, z) in jobs:
    for S in speeds:
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2)
        for i in range(24):
            if i < 4: e.wf32(a + 0x18, S)
            e.step(0, 0, 0, 2)
            if e.s16(GAME_MODE) != GM_WORLD: break
        n += 1
        if e.s16(GAME_MODE) != GM_WORLD: continue
        p = player(e)
        why = []
        if p['z'] < 45: why.append('behind back faces')
        if p['y'] >= 100: why.append('high')
        if abs(p['x']) > 400.5 and not (75 < p['z'] < 160): why.append('outside x')
        if p['z'] > 205: why.append('outside z')
        if why:
            hits += 1
            fo.write(json.dumps({'start': [x, y, z], 'S': S, 'end': [p['x'], p['y'], p['z']], 'act': p['action'], 'floor': e.s16(COLLISION + 2), 'why': why}) + '\n'); fo.flush()
print('done part', PART, n, 'mounts', hits, 'interesting')
