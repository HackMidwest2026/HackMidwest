"""APG grid at the omo_11 Super Block from the real route state: walk away along x (DIR=+1 east / -1 west) for D
steps, walk back to the hit spot, wait W frames, jump. usage: omo11_apg_grid.py DIR D0 D1 WMAX OUT.jsonl"""
import json, os, sys
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
from nav import go_to, stick_world, world_yaw_to
from emu import A
from omo11_find_sparkle import sparkle
e = P.e
d, d0, d1, wmax, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
fo = open(out, 'a')
SP = {}
def track():
    for inst, data in sparkle(e):                          # last sparkle seen alive, and its part 0/4 counters
        SP.update(data=data, c0=e.u32(data + 0x28), c4=e.u32(data + 0xB0 + 0x28))
def text():
    for f in range(900):
        p = P.popup()
        if p: return p
        track(); e.step(A if f % 8 == 0 else 0, 0, 0, 2)
for D in range(d0, d1):
    for W in range(wmax):
        P.setup()
        for i in range(D):
            p = P.player(e); e.step(0, *stick_world(e, world_yaw_to(p, -115 + d * 200, -112)), 2)
        go_to(e, -115, -112, maxf=120, tol=1.5)
        SP.clear()
        for i in range(W): e.step(0, 0, 0, 2)
        for i in range(6): track(); e.step(A, 0, 0, 2)
        p = text(); r = {'dir': d, 'D': D, 'W': W, 'ok': bool(p), 'y': P.player(e)['y']}
        if p:
            r.update(P.dump(p))
            if SP: r.update(sparkle=hex(SP['data']), c0=SP['c0'], c4=SP['c4'],
                            aligned={SP['data'] - 0x30: 'part4', SP['data'] - 0xE0: 'part0'}.get(p))
        fo.write(json.dumps(r) + '\n'); fo.flush()
