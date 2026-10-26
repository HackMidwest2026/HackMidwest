"""tik_23: hammer the Super Hammer block with the basic hammer MAXH times (inputs only after states/tik23_westzone.st).
Every 10 hits: invisible wall o102 (collider 9) flags, the block entity still present, general-heap used/largest
free, and a walk test from a saved copy: walk west along z = 8 (the 5-unit strip north of the block) and see whether
Mario gets past x -280 into the tunnel. usage: tik23_hammer_many.py MAXH OUT.jsonl"""
import os, sys, json
from emu import *
from pm import *
from nav import go_to
from heapsim import Heap
from dump_collision_tik15 import GCOLL
MAXH, out = int(sys.argv[1]), sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hm%d' % os.getpid())
e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
go_to(e, -235, -20, maxf=200, tol=2)
for i in range(6): e.step(0, -60, 0, 2)       # face west, against the block
for i in range(10): e.step(0, 0, 0, 2)
fo = open(out, 'a')
def o102_flags():
    return hex(e.u32(e.u32(GCOLL + 4) + 9 * 0x1C))
def block_alive():
    p = e.u32(0x801563C0)
    return 0x80000000 < p < 0x80800000 and round(e.f32(p + 0x48)) == -280
def heap():
    h = Heap.from_emu(e)
    used = sum(ln + 0x10 for a, nxt, ln, al, mid in h.walk() if al)
    fr = [ln for a, nxt, ln, al, mid in h.walk() if not al]
    return used, max(fr, default=0)
def walk_test():
    tmp = '/dev/shm/pmbot/hm%d_tmp.st' % os.getpid()
    e.save(tmp); e.step(0, 0, 0, 1)
    go_to(e, -250, 8, maxf=120, tol=1.5)
    mn = 999
    for i in range(40):
        e.step(0, -80, 0, 2); mn = min(mn, player(e)['x'])
    area = where(e)
    e.load(tmp); e.step(0, 0, 0, 2)
    return round(mn, 1), area
print('start', o102_flags(), block_alive(), heap(), walk_test(), flush=True)
for k in range(1, MAXH + 1):
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(28): e.step(0, 0, 0, 2)
    if k % 10 == 0 or k <= 3:
        used, big = heap()
        r = {'hit': k, 'o102': o102_flags(), 'block': block_alive(), 'heap_used': used, 'largest_free': big,
             'pos': [round(player(e)['x'], 1), round(player(e)['z'], 1)], 'mode': e.s16(GAME_MODE)}
        if k % 20 == 0 or k <= 3: r['walk_min_x'], r['area'] = walk_test()
        fo.write(json.dumps(r) + '\n'); fo.flush(); print(r, flush=True)
