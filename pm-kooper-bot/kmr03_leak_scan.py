"""Find what grows when the basic hammer hits the unbreakable Hammer2 block in kmr_03: swing N times from a state
next to the block, snapshot all 8 MB of RDRAM after every swing (same phase), and report words that change
monotonically with the hit count (counters, list lengths, advancing pointers), grouped into regions.
Also tracks the general / collision heaps.  usage: kmr03_leak_scan.py STATE N OUT.json"""
import json, os, sys
from emu import *
from pm import *
from heapsim import Heap

st, N, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ls%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
for i in range(20): e.step(0, 0, 0, 2)
def snap():
    return bytes(memoryview(e.ram).cast('B'))       # host-endian words; compare as u32 arrays
import array
def words(b):
    a = array.array('I'); a.frombytes(b); return a
def heap_used(head):
    h = Heap.from_emu(e, head)
    return sum(ln + 0x10 for a, nxt, ln, al, mid in h.walk() if al), len(h.n)
snaps, heaps = [], []
for s in range(N + 1):
    if s:
        for i in range(2): e.step(B, 0, 0, 2)
        for i in range(30): e.step(0, 0, 0, 2)
    snaps.append(words(snap()))
    heaps.append({'general': heap_used(0x802FB800), 'collision': heap_used(0x80268000)})
    print(s, heaps[-1], player(e)['x'], flush=True)
# words strictly monotonic over the swings (ignore the first two)
mono = []
first = snaps[2]
n = len(first)
diffs = [i for i in range(n) if snaps[-1][i] != first[i]]
for i in diffs:
    seq = [snaps[k][i] for k in range(2, N + 1)]
    inc = all(b > a for a, b in zip(seq, seq[1:])); dec = all(b < a for a, b in zip(seq, seq[1:]))
    if inc or dec:
        steps = [b - a for a, b in zip(seq, seq[1:])]
        mono.append({'addr': hex(0x80000000 + 4 * i), 'first': hex(seq[0]), 'last': hex(seq[-1]),
                     'step': steps[0] if len(set(steps)) == 1 else 'varies'})
print('words changed', len(diffs), 'monotonic', len(mono))
for m in mono[:80]: print(m)
json.dump({'heaps': heaps, 'monotonic': mono}, open(out, 'w'))
