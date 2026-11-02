/* Seed lock from Final Bowser's phase-2 aura angles (energy_in_out type 4: 16 stars, each restart = rand_int(359)).
 * Input (stdin, from aura_lockdemo.py): N delta p220 / 16 part counters at frame 0 / N lines "k a1 .. ak" (observed
 * restart angles of frame f in part order, each within +-delta of the true draw).
 * Known to the search: the part counters (one 20-frame cycle of viewing fixes them: each star's restart frame), the
 * sky-bolt phase p220 (the visible bolts). Unknown: the seed, the low-bolt phase (130 values) and the coin's next draw
 * frame (48 values). Anchor = first frame with >= 3 restarts: every seed whose consecutive draws fall in the observed
 * +-delta windows is enumerated directly from the angle interval (no 2^32 loop), then simulated forward per hypothesis.
 * Prints the survivors after each further frame and the seed before the anchor's first aura draw for the survivors. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#define D359 (0xFFFFFFFFu / 360u)
static inline uint32_t adv(uint32_t s) { return s * 0x5D588B65u + 1u; }
static inline uint32_t rint_(uint32_t *s, uint32_t mx) {
    uint32_t d = 0xFFFFFFFFu / (mx + 1u), v;
    if (!d) d = 1;
    for (;;) { *s = adv(*s); v = *s / d; if (v <= mx) return v; }
}
static inline uint32_t rint100(uint32_t *s) { return rint_(s, 1009) / 10; }
int N, delta, p220, t0[16], nobs[4000], obs[4000][16];
static int near(int a, int b) { int d = abs(a - b); if (d > 180) d = 360 - d; return d <= delta; }
static int sky(int f) { int m = ((f - p220) % 220 + 220) % 220; return m == 0 || m == 60 || m == 70 || m == 160; }
static int low(int f, int p) { int m = ((f - p) % 130 + 130) % 130; return m == 0 || m == 5 || m == 35 || m == 40; }
int main(void) {
    if (scanf("%d %d %d", &N, &delta, &p220) != 3) return 1;
    for (int i = 0; i < 16; i++) scanf("%d", &t0[i]);
    for (int f = 0; f < N; f++) { scanf("%d", &nobs[f]); for (int j = 0; j < nobs[f]; j++) scanf("%d", &obs[f][j]); }
    /* part counters at each frame start */
    static int tf[4000][16];
    for (int i = 0; i < 16; i++) { int t = t0[i]; for (int f = 0; f < N; f++) { tf[f][i] = t; t = (t + 1 >= 20) ? 0 : t + 1; } }
    int A = -1;
    for (int f = 0; f < N; f++) if (nobs[f] >= 3) { A = f; break; }
    if (A < 0) return 1;
    int maxf = A + 40 < N ? A + 40 : N;
    static long surv[64], sseed[64];
    long ncand = 0, nfinal = 0, nseeds = 0; uint32_t last = 0; int lastp = -1, lastc = -1;
    for (int da = -delta; da <= delta; da++) {
        int a1 = ((obs[A][0] + da) % 360 + 360) % 360;
        uint64_t lo = (uint64_t)a1 * D359, hi = lo + D359;               /* states after the first draw */
        for (uint64_t x = lo; x < hi; x++) {
            uint32_t s = (uint32_t)x, s2 = s;
            int ok = 1;
            for (int j = 1; j < nobs[A] && ok; j++) { uint32_t v = rint_(&s2, 359); ok = near(v, obs[A][j]); }
            if (!ok) continue;
            ncand++;
            int alive = 0, best = A;
            uint32_t sA = adv(s2);                                        /* after the anchor frame's step */
            for (int p = 0; p < 130; p++) for (int c = A + 1; c <= A + 48; c++) {
                uint32_t q = sA; int nc = c, f;
                for (f = A + 1; f < maxf; f++) {
                    if (sky(f)) rint_(&q, 359);
                    if (low(f, p)) rint_(&q, 359);
                    if (f == nc) nc += rint100(&q) >= 70 ? 48 : 24;
                    int j = 0, bad = 0;
                    for (int i = 0; i < 16; i++) if (tf[f][i] + 1 >= 20) {
                        uint32_t v = rint_(&q, 359);
                        if (j >= nobs[f] || !near(v, obs[f][j])) { bad = 1; break; }
                        j++;
                    }
                    if (bad || j != nobs[f]) break;
                    q = adv(q);
                    surv[f - A] += 1;
                }
                if (f > best) best = f;
                if (f == maxf) { nfinal++; alive = 1; last = s; lastp = p; lastc = c; }
            }
            nseeds += alive;
            for (int k = 1; k < maxf - A; k++) if (best > A + k) sseed[k]++;
        }
    }
    printf("anchor frame %d (%d draws), seeds matching the anchor frame: %ld (x 6240 phase hypotheses)\n", A, nobs[A], ncand);
    for (int k = 1; k < maxf - A; k++) printf("after +%d frames: %ld seeds, %ld (seed, low phase, coin) survivors\n", k, sseed[k], surv[k]);
    printf("distinct seeds surviving: %ld; (seed, phase, coin) survivors %ld; one: state after anchor draw 1 = %08x, low phase %d, coin next %d\n", nseeds, nfinal, last, lastp, lastc);
    return 0;
}
