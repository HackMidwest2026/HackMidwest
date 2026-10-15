"""how forgiving is the Go-Explore approach? replay it to the frame before the jump (end of the spin), then vary
the jump: raw stick x/y over a grid, A hold length, and the jump frame (spin length). Count wall-face landings."""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_explore import BASES
from pm import *
A_, Z_ = 0x80, 0x20
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/house_wallface_approach.json')))
H.init()
e = H.W['e']
inputs = []
for b, deg, mag, n in V['seq']:
    from corner_sweep import stick_for
    sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
    for i in range(n):
        inputs.append(({'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0), sx, sy))
# frames 0..32: approach + spin (spin starts at 25); jump starts at 33
res = {}
for spin_end in (30, 31, 32, 33, 34):
    e.load(H.base(*BASES[V['bi']]))
    for b, sx, sy in inputs[:spin_end + 1]:
        e.step(b, sx, sy, 2)
    p0 = player(e)
    sp = os.path.join(H.W['d'], 'sens.st'); e.save(sp)
    n = 0
    hits = []
    for sx in range(-40, 1, 2):
        for sy in range(-30, 11, 2):
            for hold in (12, 8, 5):
                e.load(sp)
                air = False
                for f in range(45):
                    st = (sx, sy) if f < 12 else (0, 0)
                    e.step(A_ if f < hold else 0, st[0], st[1], 2)
                    q = player(e)
                    if q['action'] in (3, 4, 5, 8, 13):
                        air = True
                    elif air:
                        if e.s16(COLLISION + 2) == 45 and q['y'] > 25:
                            hits.append((sx, sy, hold))
                        break
                n += 1
    print('jump after spin frame', spin_end, 'from', round(p0['x'], 1), round(p0['z'], 1), ':', len(hits), 'of', n, 'land on the wall face', hits[:12], flush=True)
