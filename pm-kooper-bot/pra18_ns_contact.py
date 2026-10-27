"""pra_18 north->south, RIGHT SIDE ONLY, with a real touching Lakilester push.
1. Mario + Laki in the north side's SE corner (fresh follow history from a dismount).
2. Optional freeze: W tiny moves while Laki hovers (follow state 5), so the 40-entry history fills and freezes there.
3. Steered contact push: every frame Mario is steered to a spot `gap` units behind Laki along push angle A, so their
   colliders overlap and the game's push (1 unit away from Mario + 2 units north) moves him. Push frames are counted
   (frames where Laki is in follow state 5 and his x/z changed).
4. Mario walks to the clip spot T (x 570..574, z -13..-17), optionally via a waypoint WP first, then stands there.
   On every grounded frame in the clip zone, C-down is tried (savestate) and Laki's speed is logged.
DIAGNOSTIC SETUP: Mario placed at (700, -25) before mounting; everything after is real input; Laki's speed is never
written. usage: pra18_ns_contact.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
PTR, STATE = 0x8010D17C, 0x8010D188
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nk%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
fstate = lambda: e.u32(STATE) >> 16
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 700.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(30): e.step(0, 80, -40, 2)
e.step(D_CBUTTON, 80, 0, 2)
for i in range(60): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/nk%d_0.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/nk%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for j in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    r = player(e); e.load(cur); return r['action'] == 33 and r['z'] > 0, sp
def push(A, C, gap):
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A))
    touched = 0
    for f in range(C):
        p = player(e); lx, lz, _ = L()
        tx, tz = lx - gap * ux, lz - gap * uz
        d = math.hypot(tx - p['x'], tz - p['z'])
        s = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
        e.step(0, *s, 2)
        nx, nz, _ = L()
        if fstate() == 5 and math.hypot(nx - lx, nz - lz) > 0.5: touched += 1
    return touched
def go(tx, tz, maxf, log):
    for f in range(maxf):
        q = player(e); dd = math.hypot(q['x'] - tx, q['z'] - tz)
        if dd <= 1.2: return
        e.step(0, *st(math.degrees(math.atan2(tz - q['z'], tx - q['x'])), 80 if dd > 6 else 25), 2); log()
TARGETS = [(574, -15), (572, -15), (570, -15)]
WPS = [None, (650, -60), (660, -100), (640, -30), (690, -30)]
jobs = list(itertools.product((180, 200, 215), (60, 120, 180, 240), (4, 8), (0, 45)))[part::nparts]
fo = open(out, 'a'); hits = 0
for A, C, gap, W in jobs:
    e.load(b0)
    for i in range(W):
        e.step(0, *((14, 0) if i % 2 else (0, 14)), 2); e.step(0, 0, 0, 2)
    touched = push(A, C, gap)
    p = player(e); lx, lz, _ = L()
    after = '/dev/shm/pmbot/nk%d_a.st' % os.getpid(); e.save(after)
    for WP, T in itertools.product(WPS, TARGETS):
        e.load(after); best = [0, None]
        def log():
            q = player(e); sp = L()[2]
            if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
                need = 616 - q['x']
                if sp > best[0]: best[0] = sp; best[1] = (round(q['x'], 2), round(sp, 2), round(need, 2))
                if abs(sp - need) < 3:
                    ok, s2 = try_clip()
                    if ok:
                        rec = {'A': A, 'C': C, 'gap': gap, 'W': W, 'WP': WP, 'T': T, 'touched': touched, 'at': [q['x'], q['z']], 'speed': s2}
                        fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
        if WP: go(*WP, 80, log)
        go(*T, 80, log)
        for f in range(40):                     # stand on the spot, then tiny nudges (each records a history point)
            e.step(0, *((0, 0) if f < 20 else st(270 if f % 2 else 90, 14)), 2); log()
        print(json.dumps({'A': A, 'C': C, 'gap': gap, 'W': W, 'touched': touched, 'mario': [round(p['x']), round(p['z'])],
                          'laki': [round(lx), round(lz)], 'WP': WP, 'T': T, 'best': best}), flush=True)
print('done')
