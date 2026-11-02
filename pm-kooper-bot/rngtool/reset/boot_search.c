/* Boot-prior seed search for one HUD coin stream (status-bar coin in a room with no other RNG user).
   The seed at boot is 1 + C (C = osGetCount at main.c's seed line). Some n0 steps later the first observed coin draw
   happens; from then on every draw is rand_int(100) (shine if >= 70) followed by the frame step, and the next draw
   comes 24 game frames later (48 after a shine). So the seed before draw j is LCG^(n0 + sum of 25/49)(1 + C).
   This tries every C in [LO, HI] and n0 in [NLO, NHI] against a draw pattern ('S' shine, '.' plain spin) and prints
   every (C, n0) that fits, plus the expected number of chance fits (candidates x P(pattern)).
   Aliases: if the LCG path from 1 + C passes through another 1 + C' (C' in the window) within the n0 range, then
   (C', n0 - k) gives the same seed at the first draw and fits too, however long the pattern. Expected aliases
   ~ (HI - LO) x (NHI - NLO) / 2^32 per boot; only a narrower n0 or Count window removes them. Fits with the same
   seed at the first draw are one seed with several (C, n0) readings.
   usage: boot_search LOhex HIhex NLO NHI PATTERN
          boot_search test Chex N0 LEN [LOhex HIhex NLO NHI]   (makes a pattern from a known boot, then searches it)
   build: gcc -O2 -fopenmp -o boot_search boot_search.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#define MUL 0x5D588B65u
static inline uint32_t adv(uint32_t s) { return s * MUL + 1; }
static inline uint32_t internal(uint32_t *s, uint32_t mx) {          /* rngsim.internal */
    uint32_t d = 0xFFFFFFFFu / (mx + 1); if (!d) d = 1;
    for (;;) { *s = adv(*s); uint32_t v = *s / d; if (v <= mx) return v; }
}
static inline int coin(uint32_t *s) { return internal(s, 1009) / 10 >= 70; }   /* rand_int(100) */
static inline void frame_step(uint32_t *s) { internal(s, 1000); }             /* rand_int(1), once per game frame */
/* run the pattern from seed s (just before the first draw); return number of draws matched */
static int run(uint32_t s, const char *pat, int len) {
    for (int j = 0; j < len; j++) {
        int sh = coin(&s);
        if (sh != (pat[j] == 'S')) return j;
        int fr = sh ? 48 : 24;
        for (int k = 0; k < fr; k++) frame_step(&s);
    }
    return len;
}
static void make(uint32_t s, char *pat, int len) {
    for (int j = 0; j < len; j++) {
        int sh = coin(&s); pat[j] = sh ? 'S' : '.';
        for (int k = 0; k < (sh ? 48 : 24); k++) frame_step(&s);
    }
    pat[len] = 0;
}
/* affine power of the LCG: LCG^n(s) = a*s + b */
static void lcgpow(uint64_t n, uint32_t *a, uint32_t *b) {
    uint32_t ra = 1, rb = 0, pa = MUL, pb = 1;
    while (n) { if (n & 1) { rb = pa * rb + pb; ra = pa * ra; } pb = pa * pb + pb; pa = pa * pa; n >>= 1; }
    *a = ra; *b = rb;
}
static void search(uint32_t lo, uint32_t hi, int nlo, int nhi, const char *pat) {
    int len = strlen(pat), ns = 0;
    for (int j = 0; j < len; j++) ns += pat[j] == 'S';
    double bits = -(ns * log2(0.3) + (len - ns) * log2(0.7));
    double cand = ((double)hi - lo + 1) * (nhi - nlo + 1);
    printf("pattern %s (%d draws, %d shines, %.1f bits)\n", pat, len, ns, bits);
    printf("candidates C %08x-%08x x n0 %d-%d = 2^%.1f; expected chance fits %.3g; expected aliases of the true seed %.3g\n",
           lo, hi, nlo, nhi, log2(cand), cand * pow(2, -bits), ((double)hi - lo + 1) * (nhi - nlo) / 4294967296.0);
    uint32_t a, b; lcgpow(nlo, &a, &b);
    long hits = 0;
    #pragma omp parallel for schedule(dynamic, 65536) reduction(+:hits)
    for (int64_t c = lo; c <= (int64_t)hi; c++) {
        uint32_t s = a * (uint32_t)(c + 1) + b;
        for (int n = nlo; n <= nhi; n++, s = adv(s)) {
            if (run(s, pat, len) == len) {
                #pragma omp critical
                printf("FIT C=%08x n0=%d seed at first draw %08x\n", (uint32_t)c, n, s);
                hits++;
            }
        }
    }
    printf("fits: %ld\n", hits);
}
int main(int argc, char **argv) {
    if (argc > 1 && !strcmp(argv[1], "test")) {
        uint32_t C = strtoul(argv[2], 0, 16); int n0 = atoi(argv[3]), len = atoi(argv[4]);
        uint32_t a, b; lcgpow(n0, &a, &b); char pat[4096]; make(a * (C + 1) + b, pat, len);
        uint32_t lo = argc > 5 ? strtoul(argv[5], 0, 16) : 0x01000000, hi = argc > 6 ? strtoul(argv[6], 0, 16) : 0x02FFFFFF;
        int nlo = argc > 7 ? atoi(argv[7]) : n0 - 8, nhi = argc > 8 ? atoi(argv[8]) : n0 + 8;
        printf("truth C=%08x n0=%d\n", C, n0); search(lo, hi, nlo, nhi, pat); return 0;
    }
    if (argc < 6) { fprintf(stderr, "usage: see header\n"); return 1; }
    search(strtoul(argv[1], 0, 16), strtoul(argv[2], 0, 16), atoi(argv[3]), atoi(argv[4]), argv[5]);
    return 0;
}
