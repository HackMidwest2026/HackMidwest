// Cloud Nine puffs -> gRandSeed search on a real capture (masks from cloud9_prep.py).
// Puff k: RandInt(40), RandInt(30) (dx = v-20, dy = v-15), one puff per frame. Between puff k and k+1 the seed
// advances 1 (per-frame step) + the aura's draws that frame (20-frame pattern 21010201310011101010, phase searched)
// + up to MAXEX extra single draws in total (lightning bolt, status-bar coin).
// A puff passes if its core is pure white in the capture at ages 1..6 (it is drawn in front; white backgrounds pass).
// build: gcc -O3 -march=native -fopenmp cloud9_search.c -o cloud9_search ; run: ./cloud9_search masks.bin [MAXEX AGES THR TOL NEED]
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#define X0 560
#define Y0 360
#define W 440
#define H 320
#define NM 21
#define NP 10
static int I[NM][H + 1][W + 1];
static const char *PAT = "21010201310011101010";
static const double SC[7] = {0, 0.30, 0.80, 1.20, 1.12, 1.04, 1.00};
static int MAXEX = 2;
// birth dots measured directly on the capture (new white dot at age 1; capture px -> units via the projection)
static const int NS = 3; static const double SDX[3] = {-14.6, -2.8, 9.7}, SDY[3] = {-14.4, 7.5, -13.8};
static double TOL = 1.6;
static int AGES = 4; static double THR = 0.5; static int NEED = 3;   // lenient: occlusion by sprites (emulator: 96% of true puffs pass 3 of ages 1-4)
static inline uint32_t adv(uint32_t s) { return s * 0x5D588B65u + 1; }
static inline uint32_t draw(uint32_t *s, uint32_t mx) {
    uint32_t d = 0xFFFFFFFFu / (mx + 1); if (!d) d = 1;
    for (;;) { *s = adv(*s); uint32_t v = *s / d; if (v <= mx) return v; }
}
static inline double frac(int m, int cx, int cy, int h) {
    int x0 = cx - h - X0, x1 = cx + h + 1 - X0, y0 = cy - h - Y0, y1 = cy + h + 1 - Y0;
    if (x0 < 0) x0 = 0; if (y0 < 0) y0 = 0; if (x1 > W) x1 = W; if (y1 > H) y1 = H;
    if (x1 <= x0 || y1 <= y0) return 1.0;    // off the region: no information
    int n = I[m][y1][x1] - I[m][y0][x1] - I[m][y1][x0] + I[m][y0][x0];
    return (double)n / ((x1 - x0) * (y1 - y0));
}
static int pass[NP][41][31];
static void tables(void) {
    for (int k = 0; k < NP; k++) for (int a = 0; a <= 40; a++) for (int b = 0; b <= 30; b++) {
        int ok = 1; double dx = a - 20, dy = b - 15;
        if (k < NS) { pass[k][a][b] = fabs(dx - SDX[k]) <= TOL && fabs(dy - SDY[k]) <= TOL; continue; }
        int good = 0, tried = 0;
        for (int age = 1; age <= AGES; age++) {
            int m = k + age; if (m >= NM) break;
            int cx = (int)lround(773.8 + 4.313 * dx), cy = (int)lround(503.5 - 4.18 * (dy + 0.6 * (age - 1)));
            int h = age == 1 ? 2 : (int)lround(0.4 * 24.7 * SC[age]);
            tried++; good += frac(m, cx, cy, h) >= THR;
        }
        ok = good >= NEED;
        pass[k][a][b] = ok;
    }
    for (int k = 0; k < NP; k++) { int n = 0; for (int a = 0; a <= 40; a++) for (int b = 0; b <= 30; b++) n += pass[k][a][b];
        fprintf(stderr, "puff %d: %d/1271 cells pass (%.2f bits)\n", k, n, log2(1271.0 / (n ? n : 1))); }
}
static long nsol = 0;
static void dfs(int k, uint32_t s, int ph, int ex, int *va, int *vb, int *ee, uint32_t s0) {
    if (k == NP) {
        #pragma omp critical
        { nsol++; if (nsol <= 2000) { printf("%08x ph=%d", s0, ph); for (int i = 0; i < NP; i++) printf(" %d,%d%s", va[i] - 20, vb[i] - 15, i && ee[i] ? "+" : ""); printf("\n"); } }
        return;
    }
    int n = 1 + (PAT[(ph + k - 1) % 20] - '0');
    for (int e = 0; e <= (ex < MAXEX ? 1 : 0); e++) {
        uint32_t t = s; for (int i = 0; i < n + e; i++) t = adv(t);
        int a = draw(&t, 40), b = draw(&t, 30);
        if (!pass[k][a][b]) continue;
        va[k] = a; vb[k] = b; ee[k] = e;
        dfs(k + 1, t, ph, ex + e, va, vb, ee, s0);
    }
}
int main(int argc, char **argv) {
    if (argc > 2) MAXEX = atoi(argv[2]);
    if (argc > 3) AGES = atoi(argv[3]);
    if (argc > 4) THR = atof(argv[4]);
    if (argc > 5) TOL = atof(argv[5]);
    if (argc > 6) NEED = atoi(argv[6]);
    FILE *f = fopen(argv[1], "rb"); static unsigned char m[NM][H][W];
    if (fread(m, 1, sizeof m, f) != sizeof m) { fprintf(stderr, "short masks\n"); return 1; } fclose(f);
    for (int i = 0; i < NM; i++) for (int y = 0; y < H; y++) for (int x = 0; x < W; x++)
        I[i][y + 1][x + 1] = I[i][y][x + 1] + I[i][y + 1][x] - I[i][y][x] + m[i][y][x];
    tables();
    long first = 0;
    #pragma omp parallel for schedule(dynamic, 1 << 16) reduction(+:first)
    for (int64_t s0 = 0; s0 < (1LL << 32); s0++) {
        uint32_t s = (uint32_t)s0; int a = draw(&s, 40), b = draw(&s, 30);
        if (!pass[0][a][b]) continue;
        first++;
        int va[NP], vb[NP], ee[NP]; va[0] = a; vb[0] = b; ee[0] = 0;
        for (int ph = 0; ph < 20; ph++) dfs(1, s, ph, 0, va, vb, ee, (uint32_t)s0);
    }
    fprintf(stderr, "puff-0 survivors %ld, full solutions %ld\n", first, nsol);
    return 0;
}
