"""APG Bombette attempt: from right after the two hammer swings on block 22 (states/omo11_apg_after_hammers22.st),
walk J steps toward the Super Block, then jump straight up with the stick released (A held H steps) so the landing
makes landing dust (3 parts), then walk under the block and jump into it W steps after arriving. Logs the menu,
the 3-part instances created and their offset from the menu, and the fields a working switch needs.
usage: omo11_apg_neutraljump.py J0 J1 OUT.jsonl   (env FINE=1: J/H/W in frames)"""
import json, os, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
from omo11_heapwalk import walk
j0, j1, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nj%d' % os.getpid())
POP = 0x8010D85C; TX, TZ = -115, -112
fo = open(out, 'a')
def popup():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0 else None
def three():
    return [bk for n, bk, ln, al, mid in walk(e) if al and ln == 0x20 and e.u32(bk + 4) == 6 and e.u32(bk + 8) == 3]
def track(seen):
    for b in three():
        if b not in seen: seen.append(b)
FINE = os.environ.get('FINE')            # J, H, W in single frames instead of 2-frame steps
HS = (6, 10, 16) if FINE else (3, 5, 8)
WS = range(9) if FINE else range(5)
U = 1 if FINE else 2
for J in range(j0, j1):
    for H in HS:
        for W in WS:
            e.load('states/omo11_apg_after_hammers22.st'); seen = []
            for k in range(J):
                p = player(e); e.step(0, *stick_world(e, world_yaw_to(p, TX, TZ)), U); track(seen)
            for k in range(H): e.step(A, 0, 0, U); track(seen)
            for k in range(40):
                e.step(0, 0, 0, 2); track(seen)
                if player(e)['action'] in (0, 1, 2) and k > 3: break
            landed_dust = list(seen)
            go_to(e, TX, TZ, maxf=150, tol=1.5)
            for i in range(1 + W): e.step(0, 0, 0, U)
            for i in range(6): e.step(A, 0, 0, 2); track(seen)
            p = None
            for f in range(900):
                p = popup()
                if p: break
                if f < 60: track(seen)
                e.step(A if f % 8 == 0 else 0, 0, 0, 2)
            r = {'J': J, 'H': H, 'W': W, 'ok': bool(p), 'y': player(e)['y'], 'jump_dust': [hex(b) for b in landed_dust]}
            if p:
                r.update(addr=hex(p), id=e.u32(p + 0x108), en=e.u32(p + 0x18C), icon0=hex(e.u32(p)), desc0=hex(e.u32(p + 0x294)),
                         off=[hex(b - p) for b in seen])
            fo.write(json.dumps(r) + '\n'); fo.flush()
