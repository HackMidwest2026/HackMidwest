"""pra_03 (save block + red X room): place Mario at (x, 0, z), C-down with Laki's speed forced to S during the mount,
then 40 frames of riding and a dismount (C-down again) + 40 frames. Records where Mario ends (riding and after the
dismount): anything outside the room (x beyond -250..250, z beyond -150..0) or below the floor (y < -10) is a clip.
usage: pra03_force_map.py OUT.jsonl"""
import itertools, json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p3f%d' % os.getpid())
w = '/dev/shm/pmbot/p3f%d' % os.getpid()
e.load(os.environ.get('START', 'states/pra03_e1.st')); e.step(0, 0, 0, 2); e.save(w + '/b.st')
part, nparts = int(os.environ.get('PART', 0)), int(os.environ.get('NPARTS', 1))
grid = ([(x, z, S) for x in range(-240, 245, 20) for z in range(-140, -5, 10) for S in (40, 80, 120, 160, 200, 260)] if not os.environ.get('HIGH') else [(x, z, S) for x in range(-240, 245, 40) for z in range(-140, -5, 20) for S in (400, 700, 1000, 1500, 2000)])[part::nparts]
with open(sys.argv[1], 'w') as f:
    for x, z, S in grid:
        e.load(w + '/b.st')
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
        for i in range(12): e.step(0, 0, 0, 2)
        p0 = player(e)
        e.step(CD, 0, 0, 2)
        for i in range(40):
            for n in npcs(e):
                if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, float(S))
            e.step(0, 0, 0, 2)
        p1 = player(e)
        e.step(CD, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        p2 = player(e)
        r = dict(x=x, z=z, S=S, start=[round(p0['x'], 1), round(p0['y'], 1), round(p0['z'], 1)], ride=[round(p1['x'], 1), round(p1['y'], 1), round(p1['z'], 1), p1['action']],
                 end=[round(p2['x'], 1), round(p2['y'], 1), round(p2['z'], 1), p2['action']], map=list(where(e)[:2]))
        f.write(json.dumps(r) + '\n'); f.flush()
