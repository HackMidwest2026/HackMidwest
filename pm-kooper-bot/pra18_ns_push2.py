"""pra_18 north->south with a Lakilester push, steered: from the north side's bottom-right corner, Mario is steered
every frame to sit just behind Lakilester (on the corner side) so he keeps bumping him up-left; the history freezes
near the corner while Laki is carried far up-left. Push for C frames toward direction A, then walk to the clip spot
(x 570..574, z -13..-17) and try C-down on every grounded frame there.
DIAGNOSTIC SETUP: Mario placed at (700, -25), mounts, rides into the corner, gets off facing right (fresh history);
everything after is stick input; Laki's speed is never written. usage: pra18_ns_push2.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nq%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 700.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(30): e.step(0, 80, -40, 2)
e.step(D_CBUTTON, 80, 0, 2)
for i in range(60): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/nq%d_0.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/nq%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for j in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    r = player(e); e.load(cur); return r['action'] == 33 and r['z'] > 0, sp
def push(A, C, gap):
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A))     # push direction in world (z down = +)
    moved = 0
    for f in range(C):
        p = player(e); lx, lz, _ = L()
        tx, tz = lx - gap * ux, lz - gap * uz                          # spot just behind Laki
        d = math.hypot(tx - p['x'], tz - p['z'])
        if d > 0.8:
            ang = math.degrees(math.atan2(tz - p['z'], tx - p['x']))
            e.step(0, *st(ang, max(18, min(80, int(d * 8)))), 2)
        else:
            e.step(0, 0, 0, 2)
TARGETS = [(574, -14), (572, -15), (570, -16)]
jobs = list(itertools.product((180, 190, 200, 215), range(40, 301, 20), (4, 8), (0, 45)))[part::nparts]
fo = open(out, 'a'); hits = 0; top = 0
for A, C, gap, W in jobs:
    e.load(b0)
    for i in range(W):                                   # freeze the history in the corner: tiny moves
        e.step(0, *((14, 0) if i % 2 else (0, 14)), 2); e.step(0, 0, 0, 2)
    push(A, C, gap)
    p = player(e); lx, lz, _ = L()
    after = '/dev/shm/pmbot/nq%d_a.st' % os.getpid(); e.save(after)
    for T in TARGETS:
        e.load(after)
        for f in range(80):
            q = player(e); dd = math.hypot(q['x'] - T[0], q['z'] - T[1])
            if dd > 1.2:
                ang = math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x']))
                e.step(0, *st(ang, 80 if dd > 6 else 25), 2)
            else:
                e.step(0, 0, 0, 2)
            q = player(e); sp_now = L()[2]
            if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
                top = max(top, sp_now)
                ok, sp = try_clip()
                if ok:
                    hits += 1
                    rec = {'A': A, 'C': C, 'gap': gap, 'wiggle': W, 'T': T, 'after_push': {'mario': [round(p['x'], 1), round(p['z'], 1)], 'laki': [round(lx, 1), round(lz, 1)]},
                           'frame': f, 'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': round(sp, 2)}
                    fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    print('A %d C %d gap %d W %d: after push mario (%.0f,%.0f) laki (%.0f,%.0f); top laki speed at clip spot %.1f' % (A, C, gap, W, p['x'], p['z'], lx, lz, top), flush=True)
print('done', hits)
