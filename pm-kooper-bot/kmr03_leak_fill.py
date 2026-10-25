"""Keep hitting the kmr_03 Hammer2 block with the basic hammer until something gives: logs general-heap used/free/
largest free block per hit, game mode, and whether the game still runs (a hang shows as no new frames / no polls).
Saves a state every 10 hits. usage: kmr03_leak_fill.py STATE MAXHITS OUTDIR   (env GAP: idle steps between hits)"""
import json, os, sys
from emu import *
from pm import *
from heapsim import Heap

st, MAXH, od = sys.argv[1], int(sys.argv[2]), sys.argv[3]
GAP = int(os.environ.get('GAP', '28'))
os.makedirs(od, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lf%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
rows = []
def heapinfo():
    h = Heap.from_emu(e)
    used = sum(ln + 0x10 for a, nxt, ln, al, mid in h.walk() if al)
    fr = [ln for a, nxt, ln, al, mid in h.walk() if not al]
    return used, sum(fr), max(fr, default=0), len(h.n)
for k in range(1, MAXH + 1):
    polls0 = e.polls
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(GAP): e.step(0, 0, 0, 2)
    used, free_, big, nodes = heapinfo()
    r = {'hit': k, 'used': used, 'free': free_, 'largest_free': big, 'nodes': nodes, 'mode': e.s16(GAME_MODE),
         'polls': e.polls - polls0, 'x': round(player(e)['x'], 1)}
    rows.append(r)
    if k % 10 == 0 or big < 0x4000: print(r, flush=True)
    if k % 10 == 0: e.save(os.path.join(od, 'hit%03d.st' % k)); e.step(0, 0, 0, 1)
    if r['polls'] == 0:
        print('game stopped polling input after hit', k, flush=True); break
json.dump(rows, open(os.path.join(od, 'rows.json'), 'w'))
