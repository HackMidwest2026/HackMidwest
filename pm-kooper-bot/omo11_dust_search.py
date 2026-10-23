"""Random search over dust-making action sequences before the omo_11 Super Block hit (inputs only after the labeled
teleport onto the platform). Mario returns to the hit spot before jumping. Records block address and leftover fields.
usage: omo11_dust_search.py SEED N OUT.jsonl"""
import json, random, sys
import omo11_superblock_probe as P
seed, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
R = random.Random(seed); fo = open(out, 'a')
def act():
    c = R.random()
    if c < 0.25: return 'hammerq:%d' % R.choice([5, 10, 15, 20, 30, 45])
    if c < 0.45: return 'jumpq:%d' % R.choice([1, 2, 4, 8])
    if c < 0.60: return 'spinjump:%d' % R.choice([2, 5, 8, 12])
    if c < 0.75: return 'run:%d:%d' % (R.choice([0, 90, 180, 270]), R.choice([3, 6, 10]))
    if c < 0.85: return 'spin'
    return 'wait:%d' % R.choice([1, 2, 3, 5, 8, 13, 21, 34, 55])
for k in range(n):
    pre = ';'.join(act() for j in range(R.randint(2, 10)))
    P.setup(); P.pre(pre); p, f = P.hit()
    r = {'pre': pre, 'ok': bool(p)}
    if p: r.update(P.dump(p))
    fo.write(json.dumps(r) + '\n'); fo.flush()
