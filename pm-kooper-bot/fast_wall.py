"""Fastest top-wall push from a corner state + ledge plan: stop-and-go aimed at Laki (rotated TH) with go G and stop
S, until Laki x >= 983 or Mario passes him. Reports frames used and whether Laki is pinned with the stale target and
ring intact; saves the fastest good one (+ WAIT neutral frames, + 1) as OUT with its parameters in OUT_wall.json.
usage: fast_wall.py CORNER '<plan json>' OUT [WAIT=0]"""
import itertools, json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
CORNER, (U, jumps, _), OUT = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
WAIT = int(sys.argv[4]) if len(sys.argv) > 4 else 0
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/fw%d' % os.getpid())
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
w = '/dev/shm/pmbot/fw%d/l.st' % os.getpid(); e.save(w)
res = []
for th, G, S in itertools.product((0, -10, 10, 20, -20), (1, 2, 3, 4, 6), (1, 2)):
    e.load(w); n = 0
    for c in range(300):
        p, l = player(e), laki()
        s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(G): e.step(0, *s, 2); n += 1
        for i in range(S): e.step(0, 0, 0, 2); n += 1
        p, l = player(e), laki()
        if l['x'] >= 983 or p['x'] > l['x'] + 5: break
    ok = l['x'] >= 983 and p['x'] < l['x'] and e.u32(PTR) == ptr0 and e.u32(IDX) == idx0 and (e.u32(STATE) >> 16) == 5
    res.append((n, ok, th, G, S, round(p['x'], 1), round(l['x'], 1)))
    print('th %3d G %d S %d: %3d frames  M x %.1f  L x %.1f  %s' % (th, G, S, n, p['x'], l['x'], 'OK' if ok else '-'), flush=True)
good = sorted(r for r in res if r[1])
if good:
    n, ok, th, G, S = good[0][:5]
    e.load(w)
    for c in range(300):
        p, l = player(e), laki()
        s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(G): e.step(0, *s, 2)
        for i in range(S): e.step(0, 0, 0, 2)
        p, l = player(e), laki()
        if l['x'] >= 983 or p['x'] > l['x'] + 5: break
    for i in range(WAIT): e.step(0, 0, 0, 2)
    e.step(0, 0, 0, 2); e.save(OUT)
    json.dump({'plan': [U, jumps, 1], 'aim': th, 'G': G, 'S': S, 'wait': WAIT}, open(OUT[:-3] + '_wall.json', 'w'))
    print('fastest good: th %d G %d S %d, %d frames -> saved %s' % (th, G, S, n, OUT))
