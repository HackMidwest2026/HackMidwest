"""Check charge_model.simulate against emulator logs from _cs_probe (per-frame seeds, rand_int callers, RAM parts).
usage: charge_verify.py LOG.json [LOG.json ...]"""
import sys, json
from charge_model import *
import charge_model
def check(fn, verbose=False):
    L = json.load(open(fn))
    c = next(f for f, fr in enumerate(L) if any(x[0] == '0xe00d6160' for x in fr['calls']))
    spawns = [f - c for f, fr in enumerate(L) if any(x[0] == '0xe00d6160' for x in fr['calls'])]
    coins = [f - c for f, fr in enumerate(L) if f >= c and any(x[0] == '0x80146d54' for x in fr['calls'])]
    N = min(len(L) - c, 50)
    sim = simulate(L[c]['s0'], N, spawns=spawns, coin_frames=coins, snapshot=True)
    bad = 0
    for k in range(N):
        fr = L[c + k]; sm = sim[k]
        got = [x[2] for x in fr['calls'] if x[0].startswith('0xe00d6838')]
        exp = [v for t, v in sm['draws'] if t == 'r']
        if fr['s1'] != sm['seed_end'] or got != exp: bad += 1; verbose and print('frame', k, 'seed/draw mismatch', got, exp)
        # parts vs RAM (in creation order = address order of creation)
        ram = [fr['fx'][a] for a in sorted(fr['fx'], key=lambda a: int(a, 16))] if fr['fx'] else []
        for e, sp in (sm['parts'] or {}).items():
            rp = ram[e]
            for i, (r, p) in enumerate(zip(rp[1:], sp)):
                th, u14, posx, alpha = p
                if (int(r[9]) != th or r[5] != u14 or abs(r[1] - posx) > 1e-3 or r[6] != alpha):
                    bad += 1; verbose and print('frame', k, 'eff', e, 'part', i, 'ram', r, 'sim', p)
    return c, spawns, coins, bad
if __name__ == '__main__':
    for fn in sys.argv[1:]:
        for cf in (True, False):
            charge_model.COIN_FIRST = cf
            c, sp, co, bad = check(fn)
            print(fn, 'c=%d spawns %s coins %s COIN_FIRST=%s mismatching frames/parts: %d' % (c, sp, co, cf, bad))
