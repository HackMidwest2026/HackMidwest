"""APG variants from right after the two hammer swings on block 22 (states/omo11_apg_after_hammers22.st):
walk to (-115,-112) like the route, doing one extra action at walk step J (jump: A held H steps; hammer: B), then
wait W and jump into the Super Block. Logs the menu, the effect instance at menu+0x100 (its part count is the
partner id). Selecting is done separately (omo11_apg_variant_select.py) since a junk id can hang the core.
usage: omo11_apg_variant.py MODE J0 J1 OUT.jsonl   MODE: none | jump | jump2 | hammer | jog (J = jog steps under the block)"""
import json, os, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
mode, j0, j1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/var%d' % os.getpid())
POP = 0x8010D85C; TX, TZ = -115, -112
fo = open(out, 'a')
def popup():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0 else None
def dist():
    p = player(e); return ((p['x'] - TX) ** 2 + (p['z'] - TZ) ** 2) ** 0.5
def run(J, H, W):
    """go_to-style walk (full stick, stop within 1.5) with the extra action at step J, then 1 + W idle steps and
    the jump, exactly like omo11_route3.py + omo11_apg_finish.py"""
    e.load('states/omo11_apg_after_hammers22.st')
    n = 0 if mode in ('none', 'jog') else (H if mode in ('jump', 'jump2') else 2)
    if mode == 'jump2': n = H + J2OFF + 2
    for k in range(300):
        p = player(e)
        if dist() < 1.5 and k >= J + n and p['action'] in (0, 1, 2): break
        b = (A if mode in ('jump', 'jump2') else B) if J <= k < J + (H if mode == 'jump2' else n) else 0
        if mode == 'jump2' and J + H + J2OFF <= k < J + H + J2OFF + 2: b = A
        e.step(b, *stick_world(e, world_yaw_to(p, TX, TZ)), 2)
        if player(e)['y'] < 200: return {'fell': True}
    if mode == 'jog':                        # keep running in place (left/right along x) for J steps, end under the block
        for k in range(J):
            tx = TX + (12 if (k // 3) % 2 == 0 else -12)
            p = player(e); e.step(0, *stick_world(e, world_yaw_to(p, tx, TZ)), 2)
        go_to(e, TX, TZ, maxf=40, tol=1.5)
    for i in range(1 + W): e.step(0, 0, 0, 2)
    for i in range(6): e.step(A, 0, 0, 2)
    p = None
    for f in range(900):
        p = popup()
        if p: break
        e.step(A if f % 8 == 0 else 0, 0, 0, 2)
    if not p: return {'ok': False, 'pos': player(e)}
    inst = p + 0x100
    return {'ok': True, 'addr': hex(p), 'id': e.u32(p + 0x108), 'en': e.u32(p + 0x18C), 'hitx': round(player(e)['x'], 1),
            'icon0': hex(e.u32(p)), 'desc0': hex(e.u32(p + 0x294)),
            'inst': [e.u32(inst), e.u32(inst + 4), e.u32(inst + 8), hex(e.u32(inst + 0xC))]}
J2OFF = int(os.environ.get('J2_OFF', '12'))
def select():
    """menu open: down, A, A through prompts; returns curPartner 2 s after it changes"""
    p0 = e.s8(PLAYER_DATA + 0x12)
    for i in range(40): e.step(0, 0, 0, 2); print('wait', i, flush=True) if i % 10 == 0 else None
    for i in range(2): e.step(0, 0, -80, 1)
    print('down', flush=True)
    for i in range(10): e.step(0, 0, 0, 2)
    for i in range(2): e.step(A, 0, 0, 1)
    print('A', flush=True)
    for f in range(400):
        if e.s8(PLAYER_DATA + 0x12) != p0: break
        e.step(A if (f > 20 and f % 30 == 0) else 0, 0, 0, 2)
        if f % 10 == 0: print('after A', f, 'curPartner', e.s8(PLAYER_DATA + 0x12), flush=True)
    for i in range(30): e.step(0, 0, 0, 2)
    return e.s8(PLAYER_DATA + 0x12)
HS = [int(os.environ['H_ONLY'])] if os.environ.get('H_ONLY') else ((2, 3, 4, 6) if mode in ('jump', 'jump2') else (0,))
WS = [int(os.environ['W_ONLY'])] if os.environ.get('W_ONLY') else (0, 1, 2, 3, 4)
for J in range(j0, j1):
    for H in HS:
        for W in WS:
            r = run(J, H, W); r.update(mode=mode, J=J, H=H, W=W)
            fo.write(json.dumps(r) + '\n'); fo.flush()
            if os.environ.get('DUMP') and r.get('ok'):
                p = int(r['addr'], 16)
                print({n: hex(e.u32(p + o)) for n, o in (('ptrIcon[-1]', -4), ('nameMsg[-1]', 0x80), ('userIndex[-1]', 0x104), ('enabled[-1]', 0x188),
                       ('value[-1]', 0x20C), ('descMsg[-1]', 0x290), ('descMsg[0]', 0x294), ('nameMsg[0]', 0x84), ('ptrIcon[0]', 0))}, flush=True)
            if os.environ.get('SELECT') and r.get('ok'):
                for kv in filter(None, os.environ.get('DIAG_ZERO', '').split(',')):   # DIAGNOSTIC ONLY: clear a menu field
                    e.w32(int(r['addr'], 16) + int(kv, 16), 0)
                print('menu', r, flush=True); print('SELECTED -> curPartner', select(), 'alive', flush=True)
