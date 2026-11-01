"""Does one observation of the RNG (coin glint = rand_int(100) >= 70; or any top-bits reading) shift the odds of
Bowser's attack choice n seed steps later? Exact LCG model, 2^20 random seeds per test."""
import numpy as np
M = np.uint64(0xFFFFFFFF); A = 0x5D588B65
def adv(x): return (x * np.uint64(A) + np.uint64(1)) & M
def draw(x, mx):          # internal(mx) without the (vanishingly rare) rejection redraw
    x = adv(x); return x, x // np.uint64(0xFFFFFFFF // (mx + 1))
rng = np.random.default_rng(1)
x0 = rng.integers(0, 2**32, size=1 << 20, dtype=np.uint64)
x, v = draw(x0, 1009); glint = (v // 10) >= 70
quad = (x >> np.uint64(30)).astype(int)        # e.g. a lightning angle read to the nearest quadrant (top 2 bits)
def move(y):
    y, r80 = draw(y, 80); y, r60 = draw(y, 60)
    return np.where(r80 < 20, 0, np.where(r60 < 20, 1, 2))   # 0 BodySlam, 1 Claw, 2 Fire
base = None; worst = (0, None); worstq = (0, None)
y = x.copy()
for n in range(1, 2001):
    y = adv(y)
    m = move(y)
    if base is None: base = [np.mean(m == k) for k in range(3)]
    for k in range(3):
        d = abs(np.mean(m[glint] == k) - np.mean(m == k))
        if d > worst[0]: worst = (d, (n, k))
        for q in range(4):
            dq = abs(np.mean(m[quad == q] == k) - np.mean(m == k))
            if dq > worstq[0]: worstq = (dq, (n, k, q))
print('baseline P(BodySlam, Claw, Fire) = %.3f %.3f %.3f' % tuple(base))
print('largest shift after a coin glint, over n = 1..2000 steps: %.4f at %s' % worst)
print('largest shift from a top-2-bit reading (e.g. quadrant), n = 1..2000: %.4f at %s' % worstq)
print('noise level for this sample size ~ %.4f' % (3 * np.sqrt(0.25 / glint.sum())))
