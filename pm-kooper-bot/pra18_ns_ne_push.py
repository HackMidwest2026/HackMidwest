"""pra_18 north->south, RIGHT SIDE, frozen-history + touching-push attempt.
Setup (real input after a diagnostic start): Mario mounts/dismounts in the NE pocket north of statue 3, walks out and
back so Laki's history pointer leaves 0, then wiggles (4-frame up/down taps) beside Laki until the 40-entry history is
full and frozen; the trail ends ~(733,-120), ~190 units from the clip spot. Then a steered TOUCHING push (Mario kept
`gap` units behind Laki along angle A every frame; push frames counted) for C frames, then Mario goes to the clip spot
T via waypoint WP (run, or Speedy-Spin dash with Z), stands, then nudges. C-down is tried on every grounded frame in
the clip zone. DIAGNOSTIC: start (715,-125) placed in RAM. usage: pra18_ns_ne_push.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
PTR, STATE, HIST = 0x8010D17C, 0x8010D188, 0x8010CEF8
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ne%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def L(): l = laki(); return (e.f32(l['addr'] + 0x38), e.f32(l['addr'] + 0x40), e.f32(l['addr'] + 0x18))
fstate = lambda: e.u32(STATE) >> 16
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 715.0); e.wf32(PLAYER + PS_POS + 8, -125.0)                     # DIAGNOSTIC
for i in range(20): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(20): e.step(0, 80, -40, 2)
e.step(D_CBUTTON, 80, 0, 2)
for i in range(60): e.step(0, 0, 0, 2)
if os.environ.get('CORNER') == '1':                       # lead Laki into the NE corner along the north wall
    for i in range(20): e.step(0, *st(180, 80), 2)
    for i in range(30): e.step(0, 0, 0, 2)
    for i in range(10): e.step(0, *st(270, 80), 2)
    for i in range(30): e.step(0, *st(0, 80), 2)
    for i in range(int(os.environ.get('DOWNF', 8))): e.step(0, *st(90, 80), 2)
    for i in range(30): e.step(0, 0, 0, 2)
else:
    for i in range(int(os.environ.get("OUTF", 18))): e.step(0, *st(170, 80), 2)
    for i in range(40): e.step(0, 0, 0, 2)
    for i in range(int(os.environ.get("BACKF", os.environ.get("OUTF", 18)))): e.step(0, *st(350, 80), 2)
    for i in range(10): e.step(0, 0, 0, 2)
for i in range(30):
    for j in range(4): e.step(0, *st(90 if i % 2 else 270, 30), 2)
    e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/ne%d_0.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/ne%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for j in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    r = player(e); e.load(cur); return r['action'] == 33 and r['z'] > 0, sp
def push(A, C, gap):
    ux, uz = math.cos(math.radians(A)), math.sin(math.radians(A)); touched = 0
    for f in range(C):
        p = player(e); lx, lz, _ = L()
        tx, tz = lx - gap * ux, lz - gap * uz
        d = math.hypot(tx - p['x'], tz - p['z'])
        s = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
        e.step(0, *s, 2); nx, nz, _ = L()
        if fstate() == 5 and math.hypot(nx - lx, nz - lz) > 0.5: touched += 1
    return touched
def go(tx, tz, maxf, log, spin):
    for f in range(maxf):
        q = player(e); dd = math.hypot(q['x'] - tx, q['z'] - tz)
        if dd <= 1.5: return
        s = st(math.degrees(math.atan2(tz - q['z'], tx - q['x'])), 80 if dd > 8 else 25)
        e.step(Z if (spin and f == 0) else 0, *s, 2); log()
TARGETS = [(574, -15), (572, -15), (570, -15)]
WPS = [None, (640, -100), (650, -80), (660, -60), (620, -90)]
jobs = list(itertools.product((180, 170, 190), list(range(0, 41, 5)) + list(range(50, 131, 10)), (4,)))[part::nparts]
fo = open(out, 'a')
for A, C, gap in jobs:
    e.load(b0)
    touched = push(A, C, gap) if C else (e.step(0, 0, 0, 2) or 0)
    p = player(e); lx, lz, _ = L()
    after = '/dev/shm/pmbot/ne%d_a.st' % os.getpid(); e.save(after)
    for WP, T, spin in itertools.product(WPS, TARGETS, (False, True)):
        e.load(after); best = [0, None]; trace = []
        def log():
            q = player(e); sp = L()[2]; trace.append(round(sp, 1))
            if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
                need = 616 - q['x']
                if sp > best[0]: best[0] = sp; best[1] = (round(q['x'], 2), round(sp, 2), round(need, 2))
                if abs(sp - need) < 3:
                    ok, s2 = try_clip()
                    if ok:
                        rec = {'A': A, 'C': C, 'WP': WP, 'T': T, 'spin': spin, 'touched': touched, 'at': [q['x'], q['z']], 'speed': s2}
                        fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
        if WP: go(*WP, 80, log, spin)
        go(*T, 80, log, spin and not WP)
        for f in range(40):
            e.step(0, *((0, 0) if f < 20 else st(270 if f % 2 else 90, 30)), 2); log()
        print(json.dumps({'A': A, 'C': C, 'touched': touched, 'mario': [round(p['x']), round(p['z'])], 'laki': [round(lx), round(lz)],
                          'WP': WP, 'T': T, 'spin': spin, 'best': best, 'maxspeed_any': max(trace) if trace else 0}), flush=True)
print('done')
