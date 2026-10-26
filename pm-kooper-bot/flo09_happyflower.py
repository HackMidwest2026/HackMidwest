"""Happy Flower dupe in flo_09: hammer the trees in the order 2, 3, 1 (tree 2 x=0, tree 3 x=200, tree 1 x=-200)
ROUNDS times without picking up the flower, counting live Happy Flower item entities after each round.
Inputs only after the (warped) start state. usage: flo09_happyflower.py STATE ROUNDS OUT.jsonl"""
import json, os, sys
from emu import *
from pm import *
from nav import go_to
st, ROUNDS, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hf%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
TREES = {1: -200, 2: 0, 3: 200}
Z = 60                         # walk along the front of the trees, clear of the trunks
fo = open(out, 'a')
def items():
    out = []
    for i in range(256):
        p = e.u32(0x8015AD20 + 4 * i)
        if 0x80000000 < p < 0x80800000 and e.u32(p) & 1:
            out.append((e.s16(p + 0x18), round(e.f32(p + 8)), round(e.f32(p + 0xC)), round(e.f32(p + 0x10))))
    return out
def hit(t):
    sd = 1 if t == 1 else -1       # side Mario stands on; tree 1 from the right so he never walks over the flowers at x=-250
    sx = TREES[t] + 60 * sd
    go_to(e, player(e)['x'], Z, maxf=100, tol=3)
    go_to(e, sx, Z, maxf=300, tol=3)
    go_to(e, sx, 10, maxf=100, tol=3)
    for i in range(10): e.step(0, -60 * sd, 0, 2)   # walk into the trunk so Mario faces it
    for i in range(3): e.step(0, 0, 0, 2)
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(25): e.step(0, 0, 0, 2)
    go_to(e, sx, Z, maxf=100, tol=3)
    if os.environ.get('V'): print('  hit', t, round(player(e)['x']), round(player(e)['z']), e.s16(GAME_MODE), flush=True)
for r in range(1, ROUNDS + 1):
    polls0 = e.polls
    for t in (2, 3, 1): hit(t)
    for i in range(20): e.step(0, 0, 0, 2)
    it = items()
    rec = {'round': r, 'mode': e.s16(GAME_MODE), 'n_items': len(it), 'items': it[-3:], 'polls': e.polls - polls0, 'pos': [round(v) for v in (player(e)['x'], player(e)['z'])]}
    print(rec, flush=True); fo.write(json.dumps(rec) + '\n'); fo.flush()
    if rec['polls'] == 0: print('stopped polling', flush=True); e.save('states/flo09_hf_dead.st'); break
    if r % 5 == 0: e.save('states/flo09_hf_r%03d.st' % r); e.step(0, 0, 0, 1)
