"""Final Bowser phase 2 Power Bounce RNG model, emulator-measured from states/fb2_t7like_pb.st (frame 0 = target screen,
A confirms at frame D, A one frame before each landing at D+44+27k).
Per frame, draws happen in this order (measured, _fborder.py): lightning effect (rand_int(359), fixed frames LIGHT),
then the Power Bounce roll (rand_int(100), frame D+71+27(k-1) for roll k) or the hit's firework stars
(rand_int(359) x n at D+45+27(k-1), n = 11 for damage >= 9, 10 for 5-8, 8 for 3-4, 6 for 1-2), then the status-bar coin
(rand_int(100), first at frame 3 then +24, +48 after a value >= 70), then the 1 per-frame step.
The old pb12.c put the roll before the lightning on a shared frame; that is the delay-2 mismatch (frame 208).
usage: fb2model.py SEED D [first-damage]  -> roll list and bounce count."""
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
LIGHT = [23,28,88,118,123,148,153,158,208,218,248,253,283,288,308,368,378,383,413,418,428,438,508,513,528,543,548,588,638,643,648,658,673,678]
TH = []; c = 200
for i in range(30): c = c * 60 // 100; TH.append(c)          # 120, 72, 43, 25, 15, 9, 5, 3, 1, 0, ...
def nstars(dmg): return 11 if dmg >= 9 else 10 if dmg >= 5 else 8 if dmg >= 3 else 6
def model(seed, d, dmg0=13, coin0=3, light=LIGHT, kmax=30):
    """returns (rolls [(frame, value)], bounces). coin0: frame of the first coin draw; light: lightning frames."""
    s = seed; nc = coin0; k = 0; hit = 0; rolls = []; L = set(light); lc = {f: light.count(f) for f in L}
    end = d + 71 + 27 * kmax
    for f in range(end):
        for i in range(lc.get(f, 0)): s, _ = rand_int(s, 359)
        if f == d + 71 + 27 * k and k == hit - 1:            # roll k+1, after hit k+1
            s, v = rand_int(s, 100); rolls.append((f, v))
            if v > TH[k]: return rolls, k + 2
            k += 1
        if f == d + 45 + 27 * hit:                           # hit (hit+1): stars
            for i in range(nstars(max(1, dmg0 - hit))): s, _ = rand_int(s, 359)
            hit += 1
        if f == nc:
            s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        s = adv(s)
    return rolls, k + 2
if __name__ == '__main__':
    r, b = model(int(sys.argv[1], 16), int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 13)
    print(' '.join('%d=%d' % x for x in r), 'bounces', b)
