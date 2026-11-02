"""After a reset on a real console: take a seed the page locked (and roughly how many game frames after the reset it was
locked), walk the LCG backwards, and report every step count n where seed_n - 1 looks like a boot osGetCount value
(in [LO, HI], default 0x01000000-0x03000000; the emulator gives 0x01A845xx-0x01A878xx). One clean hit tells you this
console's boot Count, so a few resets measure its spread. usage: python3 unwind.py SEEDhex MAX_STEPS [LOhex HIhex]"""
import sys
M = 0xFFFFFFFF; A = 0x5D588B65; AI = pow(A, -1, 1 << 32)
s = int(sys.argv[1], 16); N = int(sys.argv[2])
LO = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x01000000
HI = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x03000000
hits = []
for n in range(N + 1):
    if LO <= ((s - 1) & M) <= HI: hits.append((n, (s - 1) & M))
    s = ((s - 1) * AI) & M
# chance hits: (HI-LO)/2^32 per step
print('expected chance hits ~%.2f' % ((HI - LO) / 2**32 * (N + 1)))
for n, c in hits: print('n=%d steps back: boot osGetCount = 0x%08x' % (n, c))
