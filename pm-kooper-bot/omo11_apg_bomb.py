"""APG Bombette search from right after the two hammer swings on block 22 (states/omo11_apg_after_hammers22.st):
walk to (X, ZW), face the back wall (z -150) or the open front edge, swing the hammer (a hit on the wall makes a
3-particle smoke_impact = 3 parts; a swing at nothing makes 6), wait T, walk under the Super Block, wait W, jump.
Logs the menu, the effect instance at menu+0x100 and the fields that must be sane (icon +0x0, description +0x294).
usage: omo11_apg_bomb.py FACE X0 X1 XSTEP OUT.jsonl   FACE: back | front"""
import json, os, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
face, x0, x1, xs, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bomb%d' % os.getpid())
POP = 0x8010D85C; TX, TZ = -115, -112
ZW = -138 if face == 'back' else -86
FACE_Z = -200 if face == 'back' else 0
fo = open(out, 'a')
def popup():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0 else None
def effects():
    """live effect instances (0x20 blocks with a plausible effect index and part count)"""
    from omo11_heapwalk import walk
    return [(bk, e.u32(bk + 4), e.u32(bk + 8)) for n, bk, ln, al, mid in walk(e)
            if al and ln == 0x20 and e.u32(bk) & 1 and 0 < e.u32(bk + 4) < 140 and 0 < e.u32(bk + 8) < 40]
def run(X, T, W):
    e.load('states/omo11_apg_after_hammers22.st')
    go_to(e, X, ZW, maxf=120, tol=3)
    p = player(e)
    for i in range(2): e.step(0, *stick_world(e, world_yaw_to(p, p['x'], FACE_Z), 30), 2)   # turn to face
    before = set(effects())
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(16): e.step(0, 0, 0, 2)
    new = [x for x in effects() if x not in before]
    for i in range(T): e.step(0, 0, 0, 2)
    go_to(e, TX, TZ, maxf=150, tol=1.5)
    if player(e)['y'] < 200: return {'fell': True}
    for i in range(1 + W): e.step(0, 0, 0, 2)
    for i in range(6): e.step(A, 0, 0, 2)
    p = None
    for f in range(900):
        p = popup()
        if p: break
        e.step(A if f % 8 == 0 else 0, 0, 0, 2)
    if not p: return {'ok': False}
    inst = p + 0x100
    return {'ok': True, 'addr': hex(p), 'id': e.u32(p + 0x108), 'en': e.u32(p + 0x18C), 'icon0': hex(e.u32(p)),
            'desc0': hex(e.u32(p + 0x294)), 'inst': [e.u32(inst), e.u32(inst + 4), e.u32(inst + 8)],
            'hammer_fx': [(hex(a), i, n) for a, i, n in new]}
for X in range(x0, x1, xs):
    for T in (0, 4, 8, 14, 22):
        for W in (0, 1, 2, 3):
            r = run(X, T, W); r.update(face=face, X=X, T=T, W=W)
            fo.write(json.dumps(r) + '\n'); fo.flush()
