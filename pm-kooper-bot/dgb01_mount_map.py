"""dgb_01 (Tubba's Castle main hall, bridges smashed): mount-target map. Mario is placed at (x, Y, z), Laki's moveSpeed
is forced to S until RIDE_STATE_MOUNT_1 runs (Mario's action becomes RIDE), and Laki's moveToPos (where the mount
puts Mario) is recorded. A target past the outer walls (|x| or |z| > 500, not inside a door alcove) is out of bounds.
usage: dgb01_mount_map.py STATE PART NPARTS OUT.jsonl   env: XR, ZR, SR (start,stop,step), Y (floor height, 0)"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = lambda k, d: (lambda a, b, c: [a + i * c for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS, SS = rng('XR', '-490,490,10'), rng('ZR', '-490,490,10'), rng('SR', '4,60,2')
Y = float(os.environ.get('Y', '0'))
ALCOVES = [(-65, 65, 500, 600), (-600, -500, -65, 65), (500, 600, -65, 65), (-65, 65, -600, -500)]
def oob(x, z):
    if -500 <= x <= 500 and -500 <= z <= 500: return False
    return not any(x0 <= x <= x1 and z0 <= z <= z1 for x0, x1, z0, z1 in ALCOVES)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/dmm%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/dmm%d.st' % os.getpid(); e.save(base)
fo = open(out, 'a'); n = hits = 0
for (x, z) in [(x, z) for x in XS for z in ZS][PART::NP]:
    row = []
    for S in SS:
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, Y); e.wf32(PLAYER + PS_POS + 8, z)
        for i in range(3): e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] != 0 or abs(p['y'] - Y) > 1 or abs(p['x'] - x) > .01 or abs(p['z'] - z) > .01: break   # no floor here
        a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2); t = None
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: t = (e.f32(a + 0x60), e.f32(a + 0x64), e.f32(a + 0x68)); break
            e.wf32(a + 0x18, S); e.step(0, 0, 0, 2)
        n += 1
        if t is None: continue
        o = oob(t[0], t[2]); hits += o
        row.append([S, round(t[0], 1), round(t[1], 1), round(t[2], 1), int(o)])
    if row: fo.write(json.dumps({'x': x, 'z': z, 'r': row}) + '\n'); fo.flush()
print('done part', PART, n, 'mounts', hits, 'out of bounds')
