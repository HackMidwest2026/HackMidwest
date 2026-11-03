/* Frame-exact seed search for Final Bowser's phase-2 aura with unread restarts allowed (README section 8).
 * Model per game frame f (aura_model.py, verified 2000/2000 frames in the emulator):
 *   sky bolt rand_int(359) if (f - P220) mod 220 in {0, 60, 70, 160}; low bolt rand_int(359) if (f - P130) mod 130 in
 *   {0, 5, 35, 40}; the coin rand_int(100) on its frame (next +24, +48 after a value >= 70); the aura: one
 *   rand_int(359) per part whose counter wraps (count n_f known from the part table); one LCG step.
 * Observations: per frame the n_f restarts, each with a read angle (or -1 = not read) and a tolerance. The parts that
 * restart on one frame draw in index order, which the footage does not give, so a frame's draws are matched to its
 * readings as a set (best assignment).
 * Stage 1: anchor = the first aura draw of frame FA (a frame with one restart, read). Every state x after that draw
 *   with draw in [a - d, a + d] is enumerated (no 2^32 loop). Each x is checked against the next K read restarts in
 *   frames FA+1.. at their nominal LCG offsets + e, e = extra (bolt / coin) draws so far, non-decreasing, each step
 *   0..2. x survives with >= MK matches.
 * Stage 2: per survivor, every hypothesis (P220 in [PLO, PHI], P130 0..129, first coin frame FA+1..FA+48) is
 *   simulated over the whole stretch from the anchor; score = matched reads; a hypothesis is dropped once its misses
 *   exceed M0 + 0.35 x reads so far. Prints the best hypotheses (score, misses, state, phases) and the score
 *   histogram of the best per survivor.
 * stdin: N FA PLO PHI K MK M0 / then N lines: n_f then n_f pairs "angle tol"
 * SLOPE / M0 on the command line override the drop rule (the null baseline is run with a slope near 1, so random
 * states are scored over the whole stretch instead of dropped).
 * usage: aura_lock2 [NTOP=10 [SLOPE=0.35 [M0]]] < obs.txt     build: gcc -O2 -fopenmp -o aura_lock2 aura_lock2.c */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define D359 (0xFFFFFFFFu / 360u)
#define D1009 (0xFFFFFFFFu / 1010u)
#define MUL 0x5D588B65u
#define MAXN 4096
static inline uint32_t adv(uint32_t s) { return s * MUL + 1u; }
static inline uint32_t r359(uint32_t *s) { uint32_t v; for (;;) { *s = adv(*s); v = *s / D359; if (v <= 359) return v; } }
static inline uint32_t r100(uint32_t *s) { uint32_t v; for (;;) { *s = adv(*s); v = *s / D1009; if (v <= 1009) return v / 10; } }
int N, FA, PLO, PHI, K, MK, M0;
int nf[MAXN], ang[MAXN][6], tol[MAXN][6];
static int near(int a, int b, int t) { int d = abs(a - b) % 360; if (d > 180) d = 360 - d; return d <= t; }
static int sky(int f, int p) { int m = ((f - p) % 220 + 220) % 220; return m == 0 || m == 60 || m == 70 || m == 160; }
static int low(int f, int p) { int m = ((f - p) % 130 + 130) % 130; return m == 0 || m == 5 || m == 35 || m == 40; }
/* best set-match count of draws v[0..n) to the frame's readings (best assignment, any n <= 6); also the number of reads */
static int bestassign(int f, const int *v, int j, int n, int used) {
    if (j == n) return 0;
    int best = 0;
    for (int o = 0; o < n; o++) if (!(used >> o & 1)) {
        int c = (ang[f][o] >= 0 && near(v[j], ang[f][o], tol[f][o])) + bestassign(f, v, j + 1, n, used | 1 << o);
        if (c > best) best = c;
    }
    return best;
}
static int setmatch(int f, const int *v, int *nread) {
    int n = nf[f], r = 0;
    for (int j = 0; j < n; j++) r += ang[f][j] >= 0;
    *nread = r;
    if (n == 1) return ang[f][0] >= 0 && near(v[0], ang[f][0], tol[f][0]);
    return bestassign(f, v, 0, n, 0);
}
typedef struct { int score, miss, p220, p130, coin; uint32_t x; } Res;
int main(int argc, char **argv) {
    int NTOP = argc > 1 ? atoi(argv[1]) : 10;
    double SLOPE = argc > 2 ? atof(argv[2]) : 0.35;
    if (scanf("%d %d %d %d %d %d %d", &N, &FA, &PLO, &PHI, &K, &MK, &M0) != 7) return 1;
    if (argc > 3) M0 = atoi(argv[3]);
    for (int f = 0; f < N; f++) { if (scanf("%d", &nf[f]) != 1 || nf[f] > 6) return 1; for (int j = 0; j < nf[f]; j++) scanf("%d %d", &ang[f][j], &tol[f][j]); }
    if (nf[FA] != 1 || ang[FA][0] < 0) { fprintf(stderr, "anchor frame must have one read restart\n"); return 1; }
    /* stage-1 reads: next K read restarts after FA: nominal offset (from x) of the draw */
    int s1f[64], s1a[64], s1t[64], s1d[64], ns1 = 0, off = 1;   /* off: offset of the next frame's first draw - 1 */
    for (int f = FA + 1; f < N && ns1 < K; f++) {
        for (int j = 0; j < nf[f]; j++) if (ang[f][j] >= 0 && nf[f] == 1 && ns1 < K) { s1f[ns1] = f; s1a[ns1] = ang[f][j]; s1t[ns1] = tol[f][j]; s1d[ns1] = off + 1 + j; ns1++; }
        off += nf[f] + 1;
    }
    int span = s1d[ns1 - 1] + 8;
    static uint32_t surv[2000000]; int nsurv = 0; long tried = 0;
    int a0 = ang[FA][0], t0 = tol[FA][0];
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:tried)
    for (int da = -t0; da <= t0; da++) {
        int a1 = ((a0 + da) % 360 + 360) % 360;
        uint32_t base = (uint32_t)a1 * D359;
        int *dv = malloc(sizeof(int) * (span + 1));
        for (uint32_t i = 0; i < D359; i++) {
            uint32_t x = base + i, s = x;
            tried++;
            for (int k = 1; k <= span; k++) { s = adv(s); dv[k] = (int)(s / D359); }
            int e = 0, sc = 0;
            for (int q = 0; q < ns1; q++) {
                for (int de = 0; de <= 2; de++) { int k = s1d[q] + e + de; if (k <= span && dv[k] <= 359 && near(dv[k], s1a[q], s1t[q])) { e += de; sc++; break; } }
                if (sc + (ns1 - q - 1) < MK) break;
            }
            if (sc >= MK) {
                #pragma omp critical
                { if (nsurv < 2000000) surv[nsurv++] = x; }
            }
        }
        free(dv);
    }
    printf("stage 1: anchor frame %d angle %d +-%d: %ld states, %d survive (>= %d of %d reads)\n", FA, a0, t0, tried, nsurv, MK, ns1);
    fflush(stdout);
    /* stage 2 */
    int nreads = 0; for (int f = FA + 1; f < N; f++) for (int j = 0; j < nf[f]; j++) nreads += ang[f][j] >= 0;
    Res *best = calloc(nsurv, sizeof(Res));
    #pragma omp parallel for schedule(dynamic, 16)
    for (int i = 0; i < nsurv; i++) {
        Res b = {-1, 0, 0, 0, 0, surv[i]};
        for (int p2 = PLO; p2 <= PHI; p2++) for (int p1 = 0; p1 < 130; p1++) for (int c = FA + 1; c <= FA + 48; c++) {
            uint32_t s = adv(surv[i]); int nc = c, sc = 0, mi = 0, rd = 0, f;
            for (f = FA + 1; f < N; f++) {
                if (sky(f, p2)) r359(&s);
                if (low(f, p1)) r359(&s);
                if (f == nc) nc += r100(&s) >= 70 ? 48 : 24;
                int v[6], nr;
                for (int j = 0; j < nf[f]; j++) v[j] = (int)r359(&s);
                int mt = setmatch(f, v, &nr);
                sc += mt; mi += nr - mt; rd += nr;
                if (mi > M0 + SLOPE * rd) break;
                s = adv(s);
            }
            if (f == N && sc > b.score) { b.score = sc; b.miss = mi; b.p220 = p2; b.p130 = p1; b.coin = c; }
        }
        best[i] = b;
    }
    /* rank */
    int hist[MAXN] = {0}, nok = 0;
    for (int i = 0; i < nsurv; i++) if (best[i].score >= 0) { hist[best[i].score]++; nok++; }
    printf("stage 2: reads after the anchor %d; survivors with a complete hypothesis %d; best-score histogram (score:count):", nreads, nok);
    for (int sc = 0; sc <= nreads; sc++) if (hist[sc]) printf(" %d:%d", sc, hist[sc]);
    printf("\n");
    for (int t = 0; t < NTOP; t++) {
        int bi = -1;
        for (int i = 0; i < nsurv; i++) if (best[i].score >= 0 && (bi < 0 || best[i].score > best[bi].score)) bi = i;
        if (bi < 0) break;
        Res r = best[bi];
        printf("TOP score %d / %d reads (misses %d)  state after anchor draw %08x  sky %d  low %d  coin %d\n", r.score, nreads, r.miss, r.x, r.p220, r.p130, r.coin);
        best[bi].score = -1;
    }
    return 0;
}
