"""Frame-by-frame watch: logs any frame where some free general-heap hole of at least 0x330 bytes has
u32(hole+0x108)==3 (what the APG menu would read as partner id if it were allocated there), with +0x18C. Actions are random
short sequences (jump/hammer/spin/spinjump/walk). usage: omo11_apg_watch.py SEED N OUT.jsonl"""
import json, os, random, sys
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
from omo11_heapwalk import walk
from emu import A, B, Z
e = P.e
BASES = [0x80318be0, 0x80319fa0, 0x80318d60, 0x8031a080, 0x80318e40, 0x80318fa0, 0x80318db0, 0x80319050,
         0x80318df0, 0x8031a1e0, 0x8031a110, 0x80318f70, 0x80318f10, 0x8031a150, 0x80318eb0]
seed, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
R = random.Random(seed); fo = open(out, 'a')
def frames():
    k = R.random()
    if k < 0.2: return [(A, 0, 0)] * R.choice([1, 3, 6]) + [(0, 0, 0)] * 25
    if k < 0.4: return [(B, 0, 0)] * 2 + [(0, 0, 0)] * R.choice([10, 20, 30])
    if k < 0.55: return [(Z, 0, 0)] * 2 + [(0, 0, 0)] * R.choice([5, 15, 30])
    if k < 0.7: return [(Z, 0, 0)] + [(0, 0, 0)] * R.choice([2, 5]) + [(A, 0, 0)] * 4 + [(0, 0, 0)] * 25
    if k < 0.9:
        sx = R.choice([-60, 60]); return [(0, sx, 0)] * R.choice([2, 4, 8]) + [(0, -sx, 0)] * R.choice([2, 4, 8])
    return [(0, 0, 0)] * R.choice([3, 10, 30])
for k in range(n):
    P.setup(); seq = []
    for j in range(R.randint(2, 8)): seq += frames()
    for f, (b, x, y) in enumerate(seq):
        e.step(b, x, y, 2)
        for nn, bk, ln, al, mid in walk(e):
            if al or ln < 0x330: continue
            if e.u32(bk + 0x108) == 3:
                fo.write(json.dumps({'run': k, 'seed': seed, 'f': f, 'hole': hex(bk), 'len': hex(ln),
                                     'en': e.u32(bk + 0x18C), 'y': P.player(e)['y']}) + '\n'); fo.flush()
