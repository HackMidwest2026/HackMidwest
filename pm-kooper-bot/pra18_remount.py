"""pra_18: user's Lakilester speed technique. Ride Laki, dismount (C-down) holding direction D, spin (Z) on landing,
jump (A) J frames after the spin, hold the OPPOSITE direction from frame O after the jump, C-down K frames after the
jump. Records the speed the mount reads (Laki's moveSpeed when Mario's action becomes RIDE) and Mario's position at
the C-down. DIAGNOSTIC SETUP: Mario placed at START on foot; he then mounts and rides 40 frames (this resets Laki's
follow history, so no stale-history speed); everything after is real input.
usage: pra18_remount.py START_X START_Z OUT.json   env DIRS='0,90,...' (world stick angles to test)"""
import os, sys, json, math, itertools
from emu import *
from pm import *
sx, sz, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rm%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC: keep Clubba 3 asleep
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, sx); e.wf32(PLAYER + PS_POS + 8, sz)                           # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, sx - 20); e.wf32(L['addr'] + 0x40, sz)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33
base = '/dev/shm/pmbot/rm%d_b.st' % os.getpid(); e.save(base)
DIRS = [int(v) for v in os.environ.get('DIRS', '0,45,90,135,180,225,270,315').split(',')]
res = []; best = (0,)
for D in DIRS:
    e.load(base)
    for i in range(8): e.step(0, *st(D, 80), 2)          # ride a little in direction D
    e.step(D_CBUTTON, *st(D, 80), 2)                     # dismount holding D
    land = None
    for i in range(40):
        e.step(0, *st(D, 80), 2); a = player(e)['action']
        if land is None and a in (0, 1, 2) and i > 3: land = i; break
    if land is None: continue
    s_land = e.f32(laki()['addr'] + 0x18)
    lst = '/dev/shm/pmbot/rm%d_l.st' % os.getpid(); e.save(lst)
    for s0, J, O, K in itertools.product((0, 1, 2), (2, 4, 6, 8, 10, 12), (0, 3, 6, 10, 99), range(1, 25)):
        if O != 99 and O >= K: continue
        e.load(lst)
        for i in range(s0): e.step(0, *st(D, 80), 2)
        e.step(Z, *st(D, 80), 2)                          # spin
        for i in range(J - 1): e.step(0, *st(D, 80), 2)
        e.step(A, *st(D, 80), 2)                          # jump
        for k in range(1, K):
            d = D + 180 if (O != 99 and k >= O) else D
            e.step(A if k < 6 else 0, *st(d, 80), 2)
        p = player(e)
        e.step(D_CBUTTON, 0, 0, 2); sp = []
        for i in range(12):
            sp.append(e.f32(laki()['addr'] + 0x18))
            if player(e)['action'] == 33: break
            e.step(0, 0, 0, 2)
        mount_speed = sp[-1] if player(e)['action'] == 33 else None
        r = [D, s0, J, O, K, round(p['x'], 1), round(p['z'], 1), p['action'], None if mount_speed is None else round(mount_speed, 2), round(s_land, 2)]
        res.append(r)
        if mount_speed and mount_speed > best[0]: best = (mount_speed, r); print('best', r, flush=True)
    print('dir', D, 'done; best so far', best, flush=True)
json.dump(res, open(out, 'w')); print('done', best)
