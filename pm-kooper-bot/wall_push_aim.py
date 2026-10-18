"""Top-wall push variants from a corner state + ledge plan: stop-and-go (go G, stop S) with the stick aimed at
Lakilester rotated by TH degrees (or fixed angle when FIXED=1), until Laki x >= 984, Mario passes him, or 200
cycles. Reports Laki's final x, Mario's x, and whether the stale target and idx are intact.
usage: wall_push_aim.py CORNER '<plan json>'"""
import json, math, os, sys, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
CORNER, (U, jumps, _) = sys.argv[1], json.loads(sys.argv[2])
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/wpa%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load(CORNER); e.step(0, 0, 0, 2)
ptr0, idx0 = e.u32(PTR), e.u32(IDX)
for i in range(U): e.step(0, *stick_for(270, 80), 2)
for W, H, D in jumps:
    s = stick_for(D, 80)
    for i in range(W): e.step(0, *s, 2)
    for i in range(24):
        e.step(0x80 if i < 8 else 0, *(s if i < H else (0, 0)), 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(3): e.step(0, 0, 0, 2)
e.save('/dev/shm/pmbot/wpa_l.st')
for fixed, th, G, S in itertools.product((0, 1), (-20, -10, 0, 10, 20), (1, 2), (2, 4)):
    e.load('/dev/shm/pmbot/wpa_l.st')
    for c in range(200):
        p, l = player(e), laki()
        deg = th if fixed else math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th
        s = stick_for(deg % 360, 80)
        for i in range(G): e.step(0, *s, 2)
        for i in range(S): e.step(0, 0, 0, 2)
        p, l = player(e), laki()
        if l['x'] >= 984 or p['x'] > l['x'] + 5: break
    for i in range(30): e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    ok = e.u32(PTR) == ptr0 and e.u32(IDX) == idx0 and (e.u32(STATE) >> 16) == 5
    print('%s th %3d G %d S %d -> M (%.1f, %.1f, %.1f) L (%.1f, %.1f) %s' % ('fixed' if fixed else 'aimed', th, G, S, p['x'], p['y'], p['z'], l['x'], l['z'], 'INTACT' if ok else '-'), flush=True)
