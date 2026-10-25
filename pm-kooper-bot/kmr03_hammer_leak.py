"""Hammer the unbreakable (Hammer2) stone block in kmr_03 (230, 0, 310) with the basic hammer, N swings, and track
the general heap after each swing: used/free bytes, node count, and (debugger core) every malloc/free with its caller,
so allocations that are never freed show up with the code that made them.
usage: kmr03_hammer_leak.py STATE N OUT.json   (env STAND_Z: where Mario stands, default 268 = just in front)"""
import json, os, sys
os.environ['M64P_DBG'] = '1'
from emu import *
from pm import *
from nav import go_to, stick_world, world_yaw_to
from heapsim import Heap, MALLOC, MALLOC_TAIL, FREE, REALLOC, HEAD_GENERAL
from pmsyms import name

st, N, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
BX, BZ = 230, 310
SZ = float(os.environ.get('STAND_Z', '268'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hk%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
print('loaded', player(e), flush=True)
if not os.environ.get('NONAV'):          # (the debugger core hangs walking this route; use a state already in place)
    for wx, wz in ((0, 80), (120, 80)): go_to(e, wx, wz, maxf=300, tol=6)   # around the south end of the x~60 wall
    go_to(e, BX, SZ, maxf=300, tol=2)
    p = player(e)
    for i in range(3): e.step(0, *stick_world(e, world_yaw_to(p, BX, BZ), 30), 2)     # face the block
    for i in range(20): e.step(0, 0, 0, 2)
print('at', player(e), flush=True)
for a in (MALLOC, MALLOC_TAIL, FREE, REALLOC): e.bp_add(a)
def stats():
    h = Heap.from_emu(e)
    used = sum(ln + 0x10 for a, nxt, ln, al, mid in h.walk() if al)
    free_ = sum(ln for a, nxt, ln, al, mid in h.walk() if not al)
    big = max((ln for a, nxt, ln, al, mid in h.walk() if not al), default=0)
    return {'used': used, 'free': free_, 'nodes': len(h.n), 'largest_free': big,
            'nalloc': sum(1 for a, nxt, ln, al, mid in h.walk() if al)}
rows = [dict(swing=0, **stats())]
live = {}                     # sim-free tracking: block addr -> (size, caller name, swing)
e.dbg_log(1)
sim = Heap.from_emu(e)
from heapsim import apply_event
for s in range(1, N + 1):
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(28): e.step(0, 0, 0, 2)
    for ev in e.dbg_events():
        if ev['a0'] != HEAD_GENERAL: continue
        r = apply_event(sim, ev)
        if ev['pc'] in (MALLOC, MALLOC_TAIL) and r: live[r] = (ev['a1'], name(ev['caller']), s)
        if ev['pc'] == FREE: live.pop(ev['a1'], None)
    rows.append(dict(swing=s, **stats()))
    print(rows[-1], flush=True)
leaks = {}
for a, (sz, who, s) in live.items():
    k = (who, sz); leaks.setdefault(k, []).append((hex(a), s))
print('still allocated (made during the swings):')
for (who, sz), v in sorted(leaks.items(), key=lambda kv: -len(kv[1])):
    print('  %3d x size %5d from %-40s swings %s' % (len(v), sz, who, sorted(set(x[1] for x in v))[:12]))
json.dump({'rows': rows, 'live': {hex(a): v for a, v in live.items()}}, open(out, 'w'))
