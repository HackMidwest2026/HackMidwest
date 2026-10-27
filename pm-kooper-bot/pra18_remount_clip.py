"""pra_18: mirror clip with the remount speed technique (user's method): ride Lakilester (direction D0 for r frames),
dismount (C-down) holding D, spin (Z) on landing and let the spin run its full length (optionally chain a buffered
second spin), optionally jump, steer toward the clip spot; try C-down on every frame. Success = riding on the other
side 30 frames later. Logs every clip with its inputs and the mount speed.
DIAGNOSTIC SETUP: Mario placed at START on foot (Clubba 3 parked = already defeated), then mounts and rides 40 frames
(resets Laki's follow history); everything after is real input. usage: pra18_remount_clip.py MODE SEED EPISODES OUT.jsonl"""
import os, sys, json, math, random
from emu import *
from pm import *
mode, seed, EP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rc%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
START = (650.0, 45.0) if mode == 'sn' else (600.0, -60.0)
crossed = (lambda q: q['z'] < 0) if mode == 'sn' else (lambda q: q['z'] > 0)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC: Clubba 3 defeated
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, START[0]); e.wf32(PLAYER + PS_POS + 8, START[1])               # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, START[0] - 20); e.wf32(L['addr'] + 0x40, START[1])  # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33
base = '/dev/shm/pmbot/rc%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/rc%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and crossed(q); e.load(cur); return ok, sp
fo = open(out, 'a'); hits = 0
for ep in range(EP):
    e.load(base); seq = []
    def go(b, a, m, n):
        for i in range(n):
            bb = b if i == 0 else (A if b == A and i < 6 else 0)
            e.step(bb, *st(a, m) if m else (0, 0), 2); seq.append((bb, a, m))
    go(0, rng.choice(range(0, 360, 15)), 80, rng.randint(0, 30))        # ride somewhere
    D = rng.choice(range(0, 360, 15))
    go(D_CBUTTON, D, 80, 1)                                              # dismount holding D
    land = 0
    for i in range(30):
        go(0, D, 80, 1)
        if player(e)['action'] in (0, 1, 2) and i > 3: break
    go(Z, D, 80, 1)                                                      # spin on landing
    spin_len = rng.randint(1, 24)
    a2 = (D + rng.choice((0, 0, 15, -15, 30, -30, 180))) % 360
    for i in range(spin_len):
        go(0, a2, 80, 1)
        ok, sp = try_clip()
        if ok:
            hits += 1; p = player(e)
            rec = {'mode': mode, 'seq': seq[:], 'at': [round(p['x'], 2), round(p['z'], 2)], 'speed': sp, 'phase': 'spin'}
            fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec['at'], 'speed', sp, 'len', len(seq), flush=True)
    if rng.random() < 0.3:                                               # chained second spin
        go(Z, a2, 80, 1)
        for i in range(rng.randint(1, 20)): go(0, a2, 80, 1)
    if rng.random() < 0.6:                                               # jump, then maybe reverse
        go(A, a2, 80, 1)
        rev = rng.choice((None, 0, 3, 6))
        for i in range(rng.randint(1, 25)):
            a3 = (a2 + 180) % 360 if (rev is not None and i >= rev) else a2
            go(A if i < 5 else 0, a3, 80, 1)
            ok, sp = try_clip()
            if ok:
                hits += 1; p = player(e)
                rec = {'mode': mode, 'seq': seq[:], 'at': [round(p['x'], 2), round(p['z'], 2)], 'speed': sp, 'phase': 'jump'}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec['at'], 'speed', sp, 'len', len(seq), flush=True)
    if ep % 50 == 0: print('ep', ep, 'hits', hits, flush=True)
print('done', hits)
