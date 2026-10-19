"""kpa_62 remount clip: scan start spots along walls Mario can push against on the y-60 platform (a wall fixes one
coordinate, so only the position along the wall needs a landmark). For each spot: place Mario near the wall, push into
it with notch P for 15 frames, wait 60 frames (Laki catches up), mount Laki, ride idle 40, dismount (B = frame 0), hold notch D, C-down on frame T.
usage: kpa62_wallscan.py STATE PART NPARTS OUT.jsonl   env: STEP (spacing along the wall), DS, TS"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
STEP = float(os.environ.get('STEP', '0.25'))
DS = [int(v) for v in os.environ.get('DS', '0,45,90,135,180,225,270,315').split(',')]
TS = [int(v) for v in os.environ.get('TS', '32,33,34,35,36').split(',')]
# (name, start point, end point, outward offset of the spot to place Mario at, push notch)
WALLS = [('tower W face', (-427.0, -95.0), (-427.0, -76.0), 45),
         ('c21 E face', (-480.0, -89.0), (-480.0, -56.0), 225),
         ('castle wall', (-466.0, -91.0), (-428.0, -91.0), 315),
         ('c4 diagonal', (-447.0, -96.0), (-470.0, -140.0), 270)]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kws%d' % os.getpid())
tmp = '/dev/shm/pmbot/kws%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.base')
spots = []
for (name, a, b, push) in WALLS:
    n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / STEP) + 1
    spots += [(name, a[0] + (b[0] - a[0]) * i / (n - 1), a[1] + (b[1] - a[1]) * i / (n - 1), push) for i in range(n)]
fo = open(out, 'a'); hits = 0
for (name, x, z, push) in spots[PART::NP]:
    e.load(tmp + '.base')
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(3): e.step(0, 0, 0, 2)
    for i in range(15): e.step(0, *stick_for(push, 80), 2)
    for i in range(60): e.step(0, 0, 0, 2)          # let Laki catch up, as in a real run
    s = player(e)
    if abs(s['y'] - 60) > .5: continue
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2); e.save(tmp + '.dis')
    for D in DS:
        e.load(tmp + '.dis'); st = stick_for(D, 80); win = []
        for fr in range(1, max(TS) + 1):
            if fr in TS:
                e.save(tmp + '.h')
                e.step(0x400, *st, 2); ok = False
                for f in range(30):
                    e.step(0, *st, 2); q = player(e)
                    if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
                if ok: win.append(fr)
                e.load(tmp + '.h')
            e.step(0, *st, 2)
        if win:
            hits += 1
            rec = {'wall': name, 'spot': [s['x'], s['z']], 'push': push, 'D': D, 'T': win}
            fo.write(json.dumps(rec) + '\n'); fo.flush(); print(rec, flush=True)
print('done part', PART, len(spots[PART::NP]), 'spots', hits, 'hits')
