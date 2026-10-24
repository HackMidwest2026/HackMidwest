"""At the moment the APG menu is allocated, list every other free general-heap hole that could hold it (>= 0x330)
with the values its +0x108 (partner id) and +0x18C (enabled) would read. Same approach/wait grid as
omo11_apg_grid.py. usage: omo11_apg_holes.py DIR D0 D1 WMAX OUT.jsonl"""
import json, os, sys
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
from omo11_heapwalk import walk
from nav import go_to, stick_world, world_yaw_to
from emu import A
e = P.e
d, d0, d1, wmax, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
fo = open(out, 'a')
for D in range(d0, d1):
    for W in range(wmax):
        P.setup()
        for i in range(D):
            p = P.player(e); e.step(0, *stick_world(e, world_yaw_to(p, -115 + d * 200, -112)), 2)
        go_to(e, -115, -112, maxf=120, tol=1.5)
        for i in range(W): e.step(0, 0, 0, 2)
        for i in range(6): e.step(A, 0, 0, 2)
        p = None
        for f in range(900):
            p = P.popup()
            if p: break
            e.step(A if f % 8 == 0 else 0, 0, 0, 2)
        if not p: continue
        holes = []
        for n, bk, ln, al, mid in walk(e):
            for off in range(0, max(0, ln - 0x330) + 1, 0x10):       # menu would sit at the hole start; offsets
                if off: break                                          # only the start is reachable by best fit
                if not al and ln >= 0x330:
                    holes.append([hex(bk), hex(ln), e.u32(bk + 0x108), e.u32(bk + 0x18C)])
        fo.write(json.dumps({'dir': d, 'D': D, 'W': W, 'menu': [hex(p), P.dump(p)['userIndex[0] (+0x108)'],
                             P.dump(p)['enabled[0] (+0x18C)']], 'holes': holes}) + '\n'); fo.flush()
