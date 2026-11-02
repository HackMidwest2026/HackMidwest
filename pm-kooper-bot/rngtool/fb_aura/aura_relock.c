/* Seed search from real-footage aura stars when the frame bookkeeping is unknown (star phases, which star restarts
 * when, coin and bolts not tracked). Each observation j is one star restart: an approximate restart frame f_j and draw
 * angle A_j. Its draw is rand_int(359) at some LCG position k_j relative to the anchor's draw; k_j is about
 * RATE * (f_j - f_anchor) (1 step per frame + about 0.9 draws per frame), so the search allows k in
 * [round(RATE*df) - W, round(RATE*df) + W]. A candidate is every state whose draw is within +-delta of the anchor
 * angle (enumerated from the angle interval); it scores one point per observation that some k in its window matches
 * within +-delta. With M observations a random state scores about M * (2W+1)(2 delta+1)/360; the true one about M
 * (less detector errors). Prints the best candidates with their scores and the k found per observation.
 * usage: aura_relock DELTA W RATE MAXMISS [MINCHAIN] < obs.txt   (obs.txt: N, then N lines "frame angle"; line 1 = anchor)
 * build: gcc -O2 -fopenmp -o aura_relock aura_relock.c */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#define D359 (0xFFFFFFFFu / 360u)
#define MUL 0x5D588B65u
static uint32_t IMUL;
int N, delta, W, maxmiss, minscore; double rate;
double fr[256]; int an[256], lo[256], hi[256];
static int near(int a, int b) { int d = abs(a - b) % 360; if (d > 180) d = 360 - d; return d <= delta; }
typedef struct { uint32_t s; int score; } Hit;
int main(int argc, char **argv) {
    delta = atoi(argv[1]); W = atoi(argv[2]); rate = atof(argv[3]); maxmiss = atoi(argv[4]); minscore = argc > 5 ? atoi(argv[5]) : 0;
    IMUL = 1; for (int i = 0; i < 31; i++) IMUL *= IMUL * MUL;   /* MUL^(2^31 - 1) = MUL^-1 mod 2^32 */
    if (scanf("%d", &N) != 1) return 1;
    for (int j = 0; j < N; j++) if (scanf("%lf %d", &fr[j], &an[j]) != 2) return 1;
    static int ord[256];
    for (int j = 0; j < N; j++) ord[j] = j;
    for (int i = 0; i < N; i++) for (int j = i + 1; j < N; j++) if (fr[ord[j]] < fr[ord[i]]) { int t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
    int kmin = 0, kmax = 0;
    for (int j = 1; j < N; j++) {
        double df = fabs(fr[j] - fr[0]); int w = W + (int)(df / 8);
        int e = (int)lround(rate * (fr[j] - fr[0])); lo[j] = e - w; hi[j] = e + w;
        if (lo[j] < kmin) kmin = lo[j]; if (hi[j] > kmax) kmax = hi[j];
    }
    long total = 0; int nh = 0; static Hit hits[100000];
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:total)
    for (int da = -delta; da <= delta; da++) {
        int a1 = ((an[0] + da) % 360 + 360) % 360;
        uint32_t base = (uint32_t)a1 * D359;
        int span = kmax - kmin + 1;
        int *dv = malloc(sizeof(int) * span);
        for (uint32_t x = 0; x < D359; x++) {
            uint32_t s0 = base + x;
            /* draws at k = kmin..kmax: state after k steps from s0 (k < 0: inverse steps) */
            uint32_t s = s0;
            for (int k = 0; k > kmin; k--) s = (s - 1u) * IMUL;
            for (int k = kmin; k <= kmax; k++) { dv[k - kmin] = (int)(s / D359); s = s * MUL + 1u; }
            total++;
            int miss = 0, score = 0;
            int nk[256], ks[256][4]; nk[0] = 1;
            for (int j = 1; j < N && miss <= maxmiss; j++) {
                nk[j] = 0;
                for (int k = lo[j]; k <= hi[j]; k++) if (k != 0 && dv[k - kmin] <= 359 && near(dv[k - kmin], an[j]) && nk[j] < 4) ks[j][nk[j]++] = k;
                if (!nk[j]) miss++;
            }
            if (miss <= maxmiss) {
                /* longest chain over the observations in frame order (ord[]), anchor = k 0: k strictly increasing
                   and |dk - rate * df| <= 3 + df / 8 between chained neighbours */
                int bestc[256][4]; score = 0;
                for (int pj = 0; pj < N; pj++) {
                    int j = ord[pj], nkj = j == 0 ? 1 : nk[j];
                    for (int a = 0; a < nkj; a++) {
                        int kj = j == 0 ? 0 : ks[j][a], bb = 1;
                        for (int pi = 0; pi < pj; pi++) {
                            int i = ord[pi], nki = i == 0 ? 1 : nk[i];
                            for (int c = 0; c < nki; c++) {
                                int ki = i == 0 ? 0 : ks[i][c]; double df = fr[j] - fr[i];
                                if (kj > ki && fabs((kj - ki) - rate * df) <= 4 + df / 8 && bestc[i][c] + 1 > bb) bb = bestc[i][c] + 1;
                            }
                        }
                        bestc[j][a] = bb; if (bb > score) score = bb;
                    }
                }
                if (score >= minscore)
                #pragma omp critical
                { if (nh < 100000) { hits[nh].s = s0; hits[nh].score = score; nh++; } }
            }
        }
        free(dv);
    }
    /* sort by score */
    for (int i = 0; i < nh; i++) for (int j = i + 1; j < nh; j++) if (hits[j].score > hits[i].score) { Hit t = hits[i]; hits[i] = hits[j]; hits[j] = t; }
    printf("anchor states tried %ld; candidates with <= %d misses of %d: %d\n", total, maxmiss, N - 1, nh);
    for (int i = 0; i < nh && i < 8; i++) {
        printf("  state after anchor draw %08x  chain %d/%d  k:", hits[i].s, hits[i].score, N);
        uint32_t s0 = hits[i].s;
        for (int j = 1; j < N; j++) {
            int found = -9999;
            for (int k = lo[j]; k <= hi[j] && found == -9999; k++) {
                if (k == 0) continue;
                uint32_t s = s0;
                if (k > 0) for (int q = 0; q < k; q++) s = s * MUL + 1u; else for (int q = 0; q > k; q--) s = (s - 1u) * IMUL;
                int v = (int)(s / D359);
                if (v <= 359 && near(v, an[j])) found = k;
            }
            if (found == -9999) printf(" -"); else printf(" %d", found);
        }
        printf("\n");
    }
    return 0;
}
