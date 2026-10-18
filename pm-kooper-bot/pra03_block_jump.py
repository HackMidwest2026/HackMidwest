"""pra_03: from on top of the save block (height 85), full jumps in 8 directions (stick held, A held 12); records the
apex height and where Mario lands. Also tries C-down on every frame of the jump with Laki's speed forced to S, then
rides 40 frames, dismounts and waits 40: anything ending outside the room box (x -250..250, z -150..0) or below the
floor counts. usage: pra03_block_jump.py OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p3j')
w = '/dev/shm/pmbot/p3j'
e.load('states/pra03_e0.st'); e.step(0, 0, 0, 2); e.save(w + '/b.st')
def laki(): return [n for n in npcs(e) if n['id'] == -4][0]
out = open(sys.argv[1], 'w')
for x, z in ((-212, -87), (-212, -63), (-188, -87), (-188, -63), (-200, -75)):
    for ang in range(0, 360, 45):
        e.load(w + '/b.st')
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 115.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(30): e.step(0, 0, 0, 2)
        if player(e)['y'] < 80: continue
        e.save(w + '/t.st'); s = stick_for(ang, 80)
        # plain jump
        apex, k = -999, 0
        for i in range(60):
            e.step(0x80 if i < 12 else 0, *s, 2); p = player(e); apex = max(apex, p['y'])
            if i > 3 and p['action'] in (0, 1, 2): break
        p = player(e)
        rec = dict(x=x, z=z, ang=ang, apex=round(apex, 1), land=[round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], cd=[])
        # C-down on each jump frame with forced speeds
        for f in range(1, 24):
            for S in (60, 120, 200, 400, 1000):
                e.load(w + '/t.st')
                for i in range(f): e.step(0x80 if i < 12 else 0, *s, 2)
                e.step(CD, *s, 2)
                for i in range(40):
                    if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
                    e.step(0, 0, 0, 2)
                rode = player(e)['action'] == 33
                e.step(CD, 0, 0, 2)
                for i in range(40): e.step(0, 0, 0, 2)
                q = player(e)
                outside = not (-251 <= q['x'] <= 251 and -151 <= q['z'] <= 1 and q['y'] > -10)
                if rode or outside: rec['cd'].append((f, S, rode, [round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)], outside))
        out.write(json.dumps(rec) + '\n'); out.flush()
        print(x, z, ang, 'apex', rec['apex'], 'land', rec['land'], 'mounts', sum(1 for c in rec['cd'] if c[2]), 'outside', sum(1 for c in rec['cd'] if c[4]), flush=True)
