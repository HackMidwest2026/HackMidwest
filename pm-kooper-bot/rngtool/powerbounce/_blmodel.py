"""(run from bot1/) (run from bot1/) Blooper Power Bounce RNG model (from states/blooper_pb.st, emulator-measured): per frame 1 step; coin
rand_int(100) first at frame 23 then +24 (+48 after a shine, value >= 70?), Power Bounce roll k at D+76+26k (before the coin
on that frame), 6 star draws (rand_int(359)) at D+51+26k for hit k+1. Prints the rolls for SEED, D."""
import sys
from rngsim import *
TH = []; c = 200
for i in range(40): c = c * 90 // 100; TH.append(c)
def model(seed, D, verbose=False):
    s = seed; nc = 23; k = 0; rolls = []; hit = 0
    for f in range(D + 76 + 26 * 40):
        if f == D + 51 + 26 * hit and hit == k:           # stars for hit k+1 (the hit after roll k-1)
            for i in range(6): s, _ = rand_int(s, 359)
            hit += 1
        if f == D + 76 + 26 * k:
            s, v = rand_int(s, 100); rolls.append((f, v))
            if v > TH[k]: return rolls, k
            k += 1
        if f == nc:
            s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        s = adv(s)
    return rolls, k
if __name__ == '__main__':
    r, k = model(int(sys.argv[1], 16), int(sys.argv[2])); print(r, 'passes', k)
