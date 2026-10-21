"""kmr_11 (after the Goomba King; Goombario, normal boots, normal spin, no badges): try to clip through the fence of
one-sided walls by the right-side bush (colliders 13 + 29, polyline (290,-225) (373,-210) (457,-210) (509,-200)
(587,-218)). Mario is placed d units north of the fence at x, settles, then for each stick angle runs one mode:
walk / spin (Z) / jump (A) / spin-jump (Z then A after s game frames: the spin jump land). Reports runs that end
south of the fence or below the floor. usage: kmr11_fence_scan.py PART NPARTS OUT.jsonl [XLO XHI XSTEP]"""
import json, math, sys
from emu import *
from pm import *

part, nparts, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
xlo, xhi, xst = (int(a) for a in sys.argv[4:7]) if len(sys.argv) > 6 else (290, 590, 15)
FENCE = [(290, -225), (373, -210), (457, -210), (509, -200), (587, -218)]
def fence_z(x):
    for (x0, z0), (x1, z1) in zip(FENCE, FENCE[1:]):
        if x0 <= x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return None
def south(x, z):
    fz = fence_z(x)
    return fz is not None and z > fz + 1
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fence%d' % part)
e.load('states/kmr11_e0_kingdone.st')
e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/fence_base%d.st' % part
e.save(base)
modes = [('walk', None), ('spin', None), ('jump', None)] + [('spinjump', s) for s in (1, 2, 3, 4, 5, 6)]
starts = [(x, d) for x in range(xlo, xhi + 1, xst) for d in (20, 40)][part::nparts]
f = open(outp, 'a')
for x, d in starts:
    e.load(base); e.step(0, 0, 0, 1)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, fence_z(x) - d)
    e.step(0, 0, 0, 40)
    p0 = player(e)
    if abs(p0['y']) > 1 or p0['action'] != 0: continue
    e.step(0, 0, 0, 1); st = '/dev/shm/pmbot/fence_st%d.st' % part; e.save(st)
    for a in range(120, 241, 4):          # stick angle: 180 = straight down = +z (toward the fence)
        sx, sy = round(80 * math.sin(math.radians(a))), round(80 * math.cos(math.radians(a)))
        for mode, s in modes:
            e.load(st)
            low, maxy, crossed = 1e9, -1e9, False
            for i in range(110):
                g = i // 2                 # game frame
                b = 0
                if mode in ('spin', 'spinjump') and g == 2: b |= Z
                if mode == 'jump' and 2 <= g < 14: b |= A
                if mode == 'spinjump' and 2 + s <= g < 14 + s: b |= A
                e.step(b, sx, sy, 1)
                p = player(e)
                low = min(low, p['y']); maxy = max(maxy, p['y'])
                if south(p['x'], p['z']): crossed = True
            p = player(e)
            r = {'x0': round(p0['x'], 1), 'z0': round(p0['z'], 1), 'a': a, 'stick': (sx, sy), 'mode': mode, 's': s,
                 'end': (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)), 'low': round(low, 1), 'maxy': round(maxy, 1),
                 'crossed': crossed, 'act': p['action']}
            f.write(json.dumps(r) + '\n')
            if crossed or low < -10: print('HIT', r, flush=True)
    f.flush()
print('done part', part)
