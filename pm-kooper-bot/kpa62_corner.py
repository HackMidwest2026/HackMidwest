"""kpa_62: setups from the corner fixed point on the tower's west face. Base: full jump off the y-35 ledge holding
screen-right (A held 6+ frames), keep holding right: Mario always stops at (-429.263, -90.233). From there, try two-leg walks (8 notch directions x 1..25 frames each),
keep the ones whose standing spot is near the clip line, and verify them with the full mount / dismount / C-down 34.
usage: kpa62_corner.py check | kpa62_corner.py search OUT.jsonl"""
import itertools, json, os, sys
from emu import *
from pm import *
from kpa62_place import place
from kpa62_runner import run, clip, stick, start as ledge_start
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kc%d' % os.getpid())
BASE = '/dev/shm/pmbot/kc%d_base.st' % os.getpid()
def hold_right(n=60):
    for i in range(n): e.step(0, *stick(0), 2)
    for i in range(20): e.step(0, 0, 0, 2)
    return player(e)
if sys.argv[1] == 'check':
    for sx, sz in ((-430, -50), (-440, -70), (-450, -40), (-425, -60)):
        e.load('states/kpa62_e1.st'); e.step(0, 0, 0, 2); place(e, sx, sz, y=60.0)
        p = hold_right(); print('from platform (%d, %d) -> corner (%.4f, %.4f)' % (sx, sz, p['x'], p['z']))
    for jump_hold in (16, 20, 24):
        ledge_start(e, 'states/kpa62_e1.st'); run(e, 'W:17 J:0:3:%d' % jump_hold)
        p = hold_right(80); print('from the ledge, jump holding right %d -> corner (%.4f, %.4f)' % (jump_hold, p['x'], p['z']))
    sys.exit()
out = open(sys.argv[2], 'a')
ledge_start(e, 'states/kpa62_e1.st'); run(e, 'W:1 J:0:10:25')      # full jump off the ledge holding right
c = hold_right(80); e.save(BASE); e.step(0, 0, 0, 1)                # keep holding right: stops at (-429.263, -90.233)
print('corner', c, flush=True)
DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
def stand(prog):
    e.load(BASE)
    for d, n in prog:
        for i in range(n): e.step(0, *stick(d), 2)
    for i in range(14): e.step(0, 0, 0, 2)
    return player(e)
near = []
D1 = [int(x) for x in os.environ.get('D1', ','.join(map(str, DIRS))).split(',')]
for d1, d2 in itertools.permutations(DIRS, 2):
    if d1 not in D1: continue
    for n1 in range(1, 26):
        for n2 in range(1, 26):
            p = stand([(d1, n1), (d2, n2)])
            if -441.5 < p['x'] < -440.0 and -62 < p['z'] < -38:
                near.append(((d1, n1), (d2, n2), round(p['x'], 4), round(p['z'], 4)))
print('near the line:', len(near), flush=True)
for (a, b, x, z) in near:
    e.load(BASE)
    for d, n in (a, b):
        for i in range(n): e.step(0, *stick(d), 2)
    for i in range(14): e.step(0, 0, 0, 2)
    s, ok, q = clip(e, 18, 34)
    r = {'leg1': a, 'leg2': b, 'stand': [x, z], 'clip': ok}
    out.write(json.dumps(r) + '\n'); out.flush()
    if ok: print('CLIP', r, flush=True)
