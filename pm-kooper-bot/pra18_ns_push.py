"""pra_18 north->south with a Lakilester push (user's idea): start with Mario and Laki in the north side's bottom-right
corner (east wall / mirror), stop-and-go push Laki up-left (stick angle A, walk 1 frame / stand 2) for C cycles, so
Laki's follow history freezes near the corner while Laki ends far up-left. Then walk to the clip spot west of the
pillar (x 570..574, z -13..-17) and press C-down on a frame while Laki dashes back toward the frozen spot.
DIAGNOSTIC SETUP: Mario placed at (725, -25), mounts and dismounts facing right (fresh follow history, Laki to his
left); everything after is real input; Laki's speed is never written. usage: pra18_ns_push.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/np%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 700.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(30): e.step(0, 80, -40, 2)                                              # ride into the corner
e.step(D_CBUTTON, 80, 0, 2)                                                             # get off facing right
for i in range(60): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/np%d_0.st' % os.getpid(); e.save(b0)
p = player(e); print('corner start mario (%.1f, %.1f) laki %s' % (p['x'], p['z'], [round(v, 1) for v in L()]), flush=True)
cur = '/dev/shm/pmbot/np%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for j in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    r = player(e); e.load(cur); return r['action'] == 33 and r['z'] > 0, sp
TARGETS = [(574, -14), (572, -15), (570, -16)]
jobs = list(itertools.product(range(200, 271, 10), range(10, 141, 10), ((80, 1, 2), (55, 2, 2), (35, 2, 2))))[part::nparts]
fo = open(out, 'a'); hits = 0; top = 0
for A, C, pat in jobs:
    mag, wlk, stand = pat
    e.load(b0)
    for k in range(C):
        for i in range(wlk): e.step(0, *st(A, mag), 2)
        for i in range(stand): e.step(0, 0, 0, 2)
    p = player(e); lx, lz, _ = L()
    after = '/dev/shm/pmbot/np%d_a.st' % os.getpid(); e.save(after)
    for T in TARGETS:
        e.load(after)
        log = []
        for f in range(70):
            q = player(e)
            if math.hypot(q['x'] - T[0], q['z'] - T[1]) > 1.2:
                ang = math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x']))
                e.step(0, *st(ang, 80 if math.hypot(q['x'] - T[0], q['z'] - T[1]) > 6 else 25), 2)
            else:
                e.step(0, 0, 0, 2)
            q = player(e); sp_now = L()[2]
            if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
                top = max(top, sp_now)
                ok, sp = try_clip()
                if ok:
                    hits += 1
                    rec = {'A': A, 'C': C, 'pattern': pat, 'T': T, 'after_push': {'mario': [round(p['x'], 1), round(p['z'], 1)], 'laki': [round(lx, 1), round(lz, 1)]},
                           'frame': f, 'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': round(sp, 2)}
                    fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    print('A %d C %d pat %s: after push mario (%.0f,%.0f) laki (%.0f,%.0f); top laki speed at the clip spot so far %.1f' % (A, C, pat, p['x'], p['z'], lx, lz, top), flush=True)
print('done', hits)
