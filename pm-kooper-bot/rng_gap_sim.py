"""Seed known before the battle; the menu disappears for an unknown number of seed steps n (0..NMAX); then the coin is
watched again in the battle menu. How many menu spins until only one n fits?"""
import numpy as np
M = np.uint64(0xFFFFFFFF); MUL = np.uint64(0x5D588B65); SH = np.uint64(700 * 4252443)
def adv(x): return (x * MUL + np.uint64(1)) & M
def stepn(x, n):
    for _ in range(n): x = adv(x)
    return x
rng = np.random.default_rng(7); NMAX = 20000; res = []
for trial in range(200):
    s0 = int(rng.integers(0, 2**32)); n_true = int(rng.integers(0, NMAX))
    # candidate seeds at the first menu draw for every n
    xs = np.empty(NMAX + 1, dtype=np.uint64); x = np.uint64(s0)
    for n in range(NMAX + 1): xs[n] = x; x = adv(x)
    true = xs[n_true]; alive = np.ones(NMAX + 1, bool); cur = xs.copy(); t = np.uint64(true); k = 0
    while alive.sum() > 1 and k < 60:
        cur = adv(cur); t = adv(t); obs = t >= SH
        alive &= ((cur >= SH) == obs)
        cur = np.where(cur >= SH, stepn(cur, 48), stepn(cur, 24)); t = stepn(t, 48 if obs else 24); k += 1
    res.append(k)
res = np.array(res)
print('menu spins needed to pin down a gap of up to %d steps: median %d, 90%% %d, max %d' % (NMAX, np.median(res), np.percentile(res, 90), res.max()))
