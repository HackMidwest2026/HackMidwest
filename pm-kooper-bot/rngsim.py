"""Paper Mario (JP) RNG: seed at 0x800743F0 (copy at gGameStatus+0x138 = 0x8007413C), advance = seed*0x5D588B65+1.
rand_int (0x800299BC): |max|; 0 -> 0; 1 -> (internal(1000) >= 501); 100 -> internal(1009)/10; else internal(max).
internal(max) (0x80029954): d = 0xFFFFFFFF // (max+1) (min 1); repeat advance, v = seed // d until v <= max."""
SEED, SEED2 = 0x800743F0, 0x8007413C
RAND_INT = 0x800299BC
M = 0xFFFFFFFF
def adv(s): return (s * 0x5D588B65 + 1) & M
def internal(s, mx):
    d = M // (mx + 1) or 1
    while True:
        s = adv(s); v = s // d
        if v <= mx: return s, v
def rand_int(s, mx):
    mx = abs(mx)
    if mx == 0: return s, 0
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)
