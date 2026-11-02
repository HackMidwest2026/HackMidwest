"""Blooper Power Bounce RNG model, emulator-verified (states/blooper_pb.st = the target screen; frame 0 = any frame whose
start seed is `seed`; d = frame of the target-screen A). 150 of 150 random (seed, d in 0-127) pairs match the emulator's
roll values exactly (_blorder.py), plus the verified 29 (1c08132d, d 2).
Per frame, draws happen in this order (measured: same-frame orders seen RCS and TCS):
  1. the hit's firework stars rand_int(359) x n at d+51+26(k-1) for hit k (n by that hit's damage, like FB2: damage = dmg0 - (k-1), at least 1; the
     verified state does 1 per hit -> 6 stars), or
     roll k rand_int(100) at d+76+26(k-1) (continue if value <= chance_k);
  2. the status-bar coin rand_int(100) (every 24 frames, 48 after a value >= 70);
  3. the per-frame step.
The menu and the target screen draw nothing else (2000 idle frames each: only the coin and the step).
chance_k: c = 200; c = c * value // 100 per roll; value = 90 (Blooper), +7 with Dodge Master (power_bounce.c).
Action command: from bounce 7 on, A must land 1 or 2 frames before the HP drop (d+51+26(k-1)); 3 early fails.
usage: blmodel.py SEED D [dodgemaster 0/1] [coinNext]"""
import sys
M = 0xFFFFFFFF
def adv(s): return (s * 0x5D588B65 + 1) & M
def internal(s, mx):
    d = M // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)
def chances(value, n=40):
    out = []; c = 200
    for i in range(n): c = c * value // 100; out.append(c)
    return out
def nstars(dmg): return 11 if dmg >= 9 else 10 if dmg >= 5 else 8 if dmg >= 3 else 6
def model(seed, d, dm=False, coin0=23, dmg0=1, kmax=40):
    """returns (rolls [(frame, value)], bounces = rolls passed + 2)."""
    TH = chances(90 + (7 if dm else 0), kmax)
    s = seed; nc = coin0; k = 0; hit = 0; rolls = []
    for f in range(d + 76 + 26 * kmax):
        if f == d + 51 + 26 * hit and hit == k:
            for i in range(nstars(max(1, dmg0 - hit))): s, _ = rand_int(s, 359)
            hit += 1
        if f == d + 76 + 26 * k:
            s, v = rand_int(s, 100); rolls.append((f, v))
            if v > TH[k]: return rolls, k + 2
            k += 1
        if f == nc:
            s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        s = adv(s)
    return rolls, k + 2
if __name__ == '__main__':
    a = sys.argv
    r, b = model(int(a[1], 16), int(a[2]), len(a) > 3 and a[3] == '1', int(a[4]) if len(a) > 4 else 23)
    print(' '.join('%d=%d' % x for x in r), 'bounces', b)
