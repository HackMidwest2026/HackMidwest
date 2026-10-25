"""Random runner-style action sequences on top of block 22 (from states/omo11_apg_top22.st, right after hopping
onto it in the save-block rush), then walk under the Super Block, wait W, jump. Actions: walk to a spot (x along
the block, z in the middle lane / by the back wall / by the front edge), turn to a side, hammer, short hop, full
jump, wait. Logs every menu with the effect instance at menu+0x100 and the fields that must be sane.
usage: omo11_apg_random22.py SEED N OUT.jsonl"""
import json, os, random, sys
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
seed, N, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
R = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/r22_%d' % os.getpid())
POP = 0x8010D85C; TX, TZ = -115, -112
fo = open(out, 'a')
def popup():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0 else None
MAXA = int(os.environ.get('MAXA', '5'))
def act():
    k = R.random()
    if os.environ.get('JUMPY') and k < 0.35: return R.choice([('jump', 0), ('hop', 3), ('spin', 0), ('walkjump', R.choice(range(-205, -95, 10)))])
    if k < 0.3: return ('walk', R.choice(range(-205, -95, 10)), R.choice([-140, -125, -112, -100, -88]))
    if k < 0.55: return ('hammer', R.choice(['back', 'front', 'left', 'right', 'none']))
    if k < 0.7: return ('hop', R.choice([1, 2, 3]))
    if k < 0.8: return ('jump', 0)
    return ('wait', R.choice([2, 5, 10, 20]))
FACE = {'back': (0, -1), 'front': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
def do(a):
    if a[0] == 'walk': go_to(e, a[1], a[2], maxf=120, tol=3)
    elif a[0] == 'hammer':
        if a[1] != 'none':
            p = player(e); dx, dz = FACE[a[1]]
            for i in range(2): e.step(0, *stick_world(e, world_yaw_to(p, p['x'] + dx * 50, p['z'] + dz * 50), 30), 2)
        for i in range(2): e.step(B, 0, 0, 2)
        for i in range(20): e.step(0, 0, 0, 2)
    elif a[0] == 'hop':
        for i in range(a[1]): e.step(A, 0, 0, 2)
        for i in range(25): e.step(0, 0, 0, 2)
    elif a[0] == 'jump':
        for i in range(8): e.step(A, 0, 0, 2)
        for i in range(25): e.step(0, 0, 0, 2)
    elif a[0] == 'spin':
        for i in range(2): e.step(Z, 0, 0, 2)
        for i in range(20): e.step(0, 0, 0, 2)
    elif a[0] == 'walkjump':                       # full jump while walking along the middle lane (landing dust)
        p = player(e)
        for i in range(8): e.step(A, *stick_world(e, world_yaw_to(p, a[1], -112), 50), 2)
        for i in range(25): e.step(0, 0, 0, 2)
    elif a[0] == 'wait':
        for i in range(a[1]): e.step(0, 0, 0, 2)
for n in range(N):
    seq = [act() for i in range(R.randint(1, MAXA))]; W = R.choice([0, 1, 2, 3, 4, 6, 8, 12])
    e.load(os.environ.get('START22', 'states/omo11_apg_top22.st'))
    for a in seq: do(a)
    go_to(e, TX, TZ, maxf=150, tol=1.5)
    r = {'seq': seq, 'W': W}
    if player(e)['y'] < 200: r['fell'] = True
    else:
        for i in range(1 + W): e.step(0, 0, 0, 2)
        for i in range(6): e.step(A, 0, 0, 2)
        p = None; LD = []
        from omo11_heapwalk import walk as hwalk
        for f in range(900):
            p = popup()
            if p: break
            if f < 60:                                   # landing dust from the hit (effect 6, 3 parts) instances
                for nd, bk, ln, al, mid in hwalk(e):
                    if al and ln == 0x20 and e.u32(bk + 4) == 6 and e.u32(bk + 8) == 3 and bk not in LD: LD.append(bk)
            e.step(A if f % 8 == 0 else 0, 0, 0, 2)
        if p:
            inst = p + 0x100
            r.update(ld=[hex(x) for x in LD], ld_off=[hex(x - p) for x in LD])
            r.update(ok=True, addr=hex(p), id=e.u32(p + 0x108), en=e.u32(p + 0x18C), icon0=hex(e.u32(p)), desc0=hex(e.u32(p + 0x294)),
                     inst=[e.u32(inst), e.u32(inst + 4), e.u32(inst + 8)])
    fo.write(json.dumps(r) + '\n'); fo.flush()
