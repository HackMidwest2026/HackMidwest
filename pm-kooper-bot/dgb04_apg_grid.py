"""APG at the Super Block in Tubba Blubba's castle (dgb_04, block at (500, -360, 110), bottom floor y -420), with
Goompa as the only partner. From a state on the bottom floor (warped in as setup), walk D steps away in direction
DIR, come back under the block, wait W steps, jump into it, A through the text, and log the partner menu fields
(id +0x108, enabled +0x18C, icon +0x0, description +0x294) and the effect instance at menu+0x100.
usage: dgb04_apg_grid.py STATE D0 D1 OUT.jsonl"""
import json, os, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
st, d0, d1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/dg%d' % os.getpid())
POP = 0x8010D85C; BX, BZ = 500.0, 110.0
fo = open(out, 'a')
def popup():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0 else None
DIRS = {'e': (60, 0), 'w': (-60, 0), 'n': (0, -60), 's': (0, 60)}
for D in range(d0, d1):
    for dn, (dx, dz) in DIRS.items():
        for W in range(6):
            e.load(st); e.step(0, 0, 0, 2)
            go_to(e, BX, BZ, maxf=200, tol=1.5)
            for k in range(D):
                p = player(e); e.step(0, *stick_world(e, world_yaw_to(p, BX + dx * 10, BZ + dz * 10)), 2)
            go_to(e, BX, BZ, maxf=200, tol=1.5)
            for i in range(1 + W): e.step(0, 0, 0, 2)
            for i in range(6): e.step(A, 0, 0, 2)
            p = None
            for f in range(900):
                p = popup()
                if p: break
                e.step(A if f % 8 == 0 else 0, 0, 0, 2)
            r = {'D': D, 'dir': dn, 'W': W, 'ok': bool(p), 'pos': [round(player(e)['x']), round(player(e)['y']), round(player(e)['z'])]}
            if p:
                r.update(addr=hex(p), id=e.u32(p + 0x108), en=e.u32(p + 0x18C), icon0=hex(e.u32(p)), desc0=hex(e.u32(p + 0x294)),
                         inst=[e.u32(p + 0x100), e.u32(p + 0x104), e.u32(p + 0x108)])
            fo.write(json.dumps(r) + '\n'); fo.flush()
