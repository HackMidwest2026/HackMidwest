"""Corner state + rev_ledge4 plan -> top-right start: load CORNER, step 1, U frames up, the plan's jumps, stop-and-go
right (go G / stop 2) along the top wall until Laki x >= 984 or 110 cycles, 30 neutral frames, step 1, save OUT.
With AIM=TH set, the top-wall push aims the stick at Laki rotated by TH degrees (go G / stop S=2, env S) and stops
when Laki x >= 983 or Mario passes him.
usage: make_topright_from_corner.py CORNER '<plan json [U, [[W,H,D],...], G]>' OUT"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
CORNER, (U, jumps, G), OUT = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mtc%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load(CORNER); e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR); tgt = (e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12))
for i in range(U): e.step(0, *stick_for(270, 80), 2)
for W, H, D in jumps:
    s = stick_for(D, 80)
    for i in range(W): e.step(0, *s, 2)
    for i in range(24):
        e.step(0x80 if i < 8 else 0, *(s if i < H else (0, 0)), 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(3): e.step(0, 0, 0, 2)
rx, ry = stick_for(0, 80)
if os.environ.get('AIM') is not None:
    S = int(os.environ.get('S', 2))
    for c in range(200):
        p, l = player(e), laki()
        s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + float(os.environ['AIM'])) % 360, 80)
        for i in range(G): e.step(0, *s, 2)
        for i in range(S): e.step(0, 0, 0, 2)
        p, l = player(e), laki()
        if l['x'] >= 983 or p['x'] > l['x'] + 5: break
else:
    for c in range(110):
        for i in range(G): e.step(0, rx, ry, 2)
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if laki()['x'] > 984: break
for i in range(30): e.step(0, 0, 0, 2)
p, l = player(e), laki()
ok = e.u32(PTR) == ptr0 and (e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)) == tgt and (e.u32(STATE) >> 16) == 5
print('M (%.1f, %.1f, %.1f) L (%.1f, %.1f, %.1f) target (%.1f, %.1f) intact %s, Laki-target %.1f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], tgt[0], tgt[1], ok, math.hypot(l['x'] - tgt[0], l['z'] - tgt[1])))
if ok: e.step(0, 0, 0, 2); e.save(OUT); print('saved', OUT)
