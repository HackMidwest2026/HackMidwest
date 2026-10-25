"""Step through an input list from a state and log every heap change in an address window: allocations and frees
with block address, size and malloc id, plus Mario's action. usage: omo11_heaptrace.py STATE INPUTS.json START LO HI"""
import json, os, sys
from emu import *
from pm import *
from omo11_heapwalk import walk
st, inp, k0, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4], 16), int(sys.argv[5], 16)
steps = json.load(open(inp))['__last__'][k0:]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ht%d' % os.getpid()); e.load(st)
def snap():
    return {bk: (ln, al, mid) for n, bk, ln, al, mid in walk(e) if lo <= bk < hi}
prev = snap()
for i, (b, x, y, n) in enumerate(steps):
    e.step(b, x, y, n)
    cur = snap()
    ch = []
    for bk in sorted(set(prev) | set(cur)):
        a, c = prev.get(bk), cur.get(bk)
        if a != c:
            if c and c[1] and (not a or not a[1] or a[2] != c[2]):
                ch.append('ALLOC %08x len %4x id %d [%d %d %d]' % (bk, c[0], c[2], e.u32(bk), e.u32(bk + 4), e.u32(bk + 8)))
            elif a and a[1] and (not c or not c[1]):
                ch.append('free  %08x len %4x id %d' % (bk, a[0], a[2]))
    if ch:
        p = player(e); print('step %4d btn %02x act %2d x %.0f:' % (i, b, p['action'], p['x']), '; '.join(ch), flush=True)
    p = e.u32(0x8010D85C)
    if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4: print('MENU at %08x' % p); break
    prev = cur
