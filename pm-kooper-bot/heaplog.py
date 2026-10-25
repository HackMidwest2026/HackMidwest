"""Capture an exact general-heap event log while replaying inputs, and validate heapsim against the live heap.
Runs the debugger-enabled core (M64P_DBG=1 is set here). Breakpoints on _heap_malloc / _heap_malloc_tail /
_heap_free / _heap_realloc log every call (args + the general_heap_* wrapper's caller); after every step the live
heap is compared with the simulated one.
usage: heaplog.py STATE INPUTS.json K0 K1 OUT.json    (INPUTS.json: steplog db, key __last__, steps K0..K1)"""
import json, os, sys
os.environ['M64P_DBG'] = '1'
from emu import *
from heapsim import Heap, apply_event, MALLOC, MALLOC_TAIL, FREE, REALLOC, HEAD_GENERAL

st, inp, k0, k1, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
steps = json.load(open(inp))['__last__'][k0:k1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hl%d' % os.getpid())
e.load(st)
for a in (MALLOC, MALLOC_TAIL, FREE, REALLOC): e.bp_add(a)
sim = Heap.from_emu(e)
start_nodes = {hex(k): v for k, v in sim.n.items()}
e.dbg_log(1)
log, bad = [], 0
for i, (b, x, y, n) in enumerate(steps):
    e.step(b, x, y, n)
    evs = e.dbg_events()
    for ev in evs:
        ev['step'] = i
        r = apply_event(sim, ev)
        if r is not None: ev['sim_ret'] = r
        log.append(ev)
    live = Heap.from_emu(e)
    d = sim.diff(live)
    if d:
        bad += 1
        if bad <= 3: print('MISMATCH after step', i, d[:6], flush=True)
        sim = live                                   # resync and continue
print('steps', len(steps), 'events', len(log), 'general-heap events', sum(1 for v in log if v['a0'] == HEAD_GENERAL),
      'steps with mismatch', bad, flush=True)
json.dump({'state': st, 'k0': k0, 'k1': k1, 'start_nodes': start_nodes, 'events': log}, open(out, 'w'))
