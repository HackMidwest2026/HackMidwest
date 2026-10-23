"""Random search over pre-hit action sequences (inputs only after the labeled teleport) for the omo_11 Super Block
heap state. Records the popup block address and the leftover userIndex[0] / enabled[0].
usage: omo11_heap_search.py SEED N OUT.jsonl"""
import json, random, sys
import omo11_superblock_probe as P
seed, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
R = random.Random(seed); fo = open(out, 'a')
ACTS = ['wait:%d', 'walk:%d:%d', 'jump', 'spin', 'hammer', 'pause', 'cright', 'cleft', 'cup']
for k in range(n):
    seq = []
    for j in range(R.randint(1, 6)):
        a = R.choice(ACTS)
        if a == 'wait:%d': a = a % R.choice([1, 2, 3, 5, 8, 13, 20, 40])
        elif a == 'walk:%d:%d': a = a % (R.choice([0, 90, 180, 270]), R.choice([2, 5, 10, 20]))
        seq.append(a)
    pre = ';'.join(seq)
    P.setup(); P.pre(pre); p, f = P.hit()
    r = {'pre': pre, 'ok': bool(p)}
    if p: r.update(P.dump(p))
    fo.write(json.dumps(r) + '\n'); fo.flush()
