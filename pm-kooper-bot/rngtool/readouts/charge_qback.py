"""Check the first-coin frame q of a Charge seed against the coin before the Charge (T1 menu), stepping the LCG
back: frames -13..-1 (Charge confirm to effect creation) and the menu only draw the per-frame rand_int(1) and the coin.
usage: charge_qback.py HUD.npz V0 SEEDHEX QLO-QHI [R]"""
import sys, numpy as np
from charge_model import rand_int
M = 0xFFFFFFFF; INV = pow(0x5D588B65, -1, 1 << 32)
def back(s, n):
    for _ in range(n): s = ((s - 1) * INV) & M
    return s
hud, V0, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3], 16); lo, hi = map(int, sys.argv[4].split('-'))
Rr = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0058
h = np.load(hud); g = lambda i: (i - V0) / Rr
present = h['gold'] > 0.3; flash = present & (h['white'] > 0.03)
idx = [i for i in range(len(present)) if g(i) < -8 and g(i) > -200]
pres = [i for i in idx if present[i]]; win = (g(min(pres)) + 1, g(max(pres)) - 1) if pres else None
fl = [g(i) for i in idx if flash[i] and not flash[i - 1]]
print('pre-Charge coin window (frames) %s, flash starts %s' % (win and (round(win[0], 1), round(win[1], 1)), [round(x, 1) for x in fl]))
for q in range(lo, hi + 1):
    # walk back coin by coin: previous coin at q - 24 (roll < 70) or q - 48 (roll >= 70)
    ok, chain, f = True, [], q
    while win and f - 24 > win[0] - 60:
        cands = []
        for gap in (24, 48):
            f1 = f - gap
            if f1 > -1: continue
            # draws after the coin at f1 up to frame 0: r1 on frames f1..-1, and the coins between f1 and 0 (all in chain)
            n = (-f1) + 1 + sum(1 for x, _ in chain)
            s = back(seed, n); _, v = rand_int(s, 100)
            if (v >= 70) == (gap == 48): cands.append((f1, v))
        if not cands: ok = False; chain.append(('impossible', None)); break
        if len(cands) > 1: chain.append(('?', None)); break
        f1, v = cands[0]; chain.append((f1, v)); f = f1
    # observed flashes in the window must match the chain's shines (flash = draw +6/+7)
    bad = 0
    for f1, v in chain:
        if f1 in ('?', 'impossible'): continue
        m = f1 + 6.5
        if win and win[0] <= m - 1.5 and m + 1.5 <= win[1]:
            seen = any(abs(m - (x + 0.5)) <= 1.5 for x in fl)
            if seen != (v >= 70): bad += 1
    for x in fl:
        if not any(f1 not in ('?', 'impossible') and v >= 70 and abs(f1 + 6.5 - (x + 0.5)) <= 1.5 for f1, v in chain): bad += 1
    print('q %2d  %s  coins before the Charge (frame, roll): %s  mismatches %d' % (q, 'ok' if ok and not bad else 'REJECTED', chain, bad))
