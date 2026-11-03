/* Native check of the Charge search with the Final Bowser lightning as nuisance (kernel.c, single thread):
 *   cc -O3 -march=native -DNATIVE -o harness_fb2 harness_fb2.c -lm
 *   harness_fb2 MAPS.bin [TRUE_S0|0] [K=16384] [ONLY_A=0]
 * Lightning patterns from every phase pair (p130, p220) with p130 = p220 mod 5 (fb_aura README: both loops start
 * together, all waits are multiples of 5), deduplicated; bolt frames: (f + p130) % 130 in {78, 83, 113, 118},
 * (f + p220) % 220 in {18, 78, 88, 178}, f = rays frame + 13 (frames after the Charge confirm, fb2_route/t6model.py).
 * Prints the stage times, the true seed's joint rank and the best candidates (seed before frame 0's bolts, pattern
 * index, q, score). With TRUE_S0 = a Hallway seed and no bolts, also checks fb2full's no-bolt score against full(). */
#include "../kernel.c"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static uint32_t back1(uint32_t s, int n) { for (int i = 0; i < n; i++) s = (s - 1u) * 0x6A76AE6Du; return s; }
static uint32_t fwd(uint32_t s, int n) { for (int i = 0; i < n; i++) s = adv(s); return s; }
typedef struct { float sc; uint32_t a; int p, q; } Rr;
static int cmp(const void *x, const void *y) { float a = ((Rr *)x)->sc, b = ((Rr *)y)->sc; return a < b ? 1 : a > b ? -1 : 0; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static const int P130[4] = {78, 83, 113, 118}, P220[4] = {18, 78, 88, 178};
static int nb(int f, int p1, int p2) { int n = 0; for (int i = 0; i < 4; i++) { n += (f + p1) % 130 == P130[i]; n += (f + p2) % 220 == P220[i]; } return n; }
static Rr J[5 * KMAX + 8];
int main(int argc, char **argv) {
  FILE *f = fopen(argv[1], "rb"); int hdr[2]; if (!f || fread(hdr, 4, 2, f) != 2) return 1; size_t sz = (size_t)hdr[0] * 360 * (hdr[1] + 1);
  N = hdr[0]; ND = hdr[1]; if (fread(S, 4, sz, f) != sz || fread(C, 4, sz, f) != sz) return 1; fclose(f);
  uint32_t truth = argc > 2 ? strtoul(argv[2], 0, 16) : 0; int Kk = argc > 3 ? atoi(argv[3]) : 16384, onlyA = argc > 4 ? atoi(argv[4]) : 0;
  /* patterns */
  int np = 0;
  for (int p2 = 0; p2 < 220; p2++) for (int p1 = p2 % 5; p1 < 130; p1 += 5) {
    uint8_t row[NMAX]; for (int n = 0; n < N; n++) row[n] = (uint8_t)nb(n + 13, p1, p2);
    int dup = 0; for (int k = 0; k < np && !dup; k++) if (!memcmp(PAT[k], row, N)) dup = 1;
    if (!dup && np < NPATMAX) memcpy(PAT[np++], row, N); }
  setPatterns(np);
  double t0 = now(); prepare(N, ND); setK(Kk); long nbs[2] = {0, 0};
  for (int e = 0; e < (onlyA ? 1 : 2); e++) { int ord[361]; for (int b = 0; b < 361; b++) ord[b] = b;
    for (int i = 0; i < 361; i++) for (int j = i + 1; j < 361; j++) if (UB[e][ord[j]] > UB[e][ord[i]]) { int t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
    for (int i = 0; i < 361; i++) { int b = ord[i]; if (UB[e][b] <= thr(e)) break; nbs[e]++; stage1g(e, b, (uint32_t)b * D360, D360, -1e30f); } }
  double t1 = now(); int m = 0;
  for (int i = 0; i < HN[0]; i++) { uint32_t a = HD[0][i]; float bb = -1e30f; for (int v = 0; v < 4; v++) { float x = s1score(1, fwd(a, 24 + v)); if (x > bb) bb = x; } J[m++] = (Rr){HS[0][i] + bb, a, 0, 0}; }
  for (int i = 0; i < HN[1]; i++) for (int v = 0; v < 4; v++) { uint32_t a = back1(HD[1][i], 24 + v); J[m++] = (Rr){HS[1][i] + s1score(0, a), a, 0, 0}; }
  qsort(J, m, sizeof(Rr), cmp); int u = 0;
  for (int i = 0; i < m && u < 300; i++) { int d = 0; for (int k = 0; k < u; k++) if (J[k].a == J[i].a) { d = 1; break; } if (!d) J[u++] = J[i]; }
  int rt = -1;
  /* the true a: s0 -> after frame 0's bolts (any phase: try 0..2) and the base draw */
  uint32_t ta[3]; for (int k = 0; k < 3; k++) ta[k] = fwd(truth, k + 1);
  for (int i = 0; i < u; i++) for (int k = 0; k < 3; k++) if (J[i].a == ta[k]) rt = i;
  double t2 = now();
  float best = -1e30f; long nfull = 0;
  for (int i = 0; i < u; i++) { float r = fb2cand(J[i].a, best / 1.8f); if (r > -1e29f) nfull++; J[i].sc = r; J[i].p = BPQ[0]; J[i].q = BPQ[1]; if (r > best) best = r; }
  double t3 = now(); qsort(J, u, sizeof(Rr), cmp);
  printf("patterns %d | prep+stage1 %.2fs (bases %ld+%ld) joint %.2fs stage2 %.2fs (%ld scored in full) | true joint rank %d\n", np, t1 - t0, nbs[0], nbs[1], t2 - t1, t3 - t2, nfull, rt);
  for (int i = 0; i < 3; i++) { int star = 0; for (int k = 0; k < 3; k++) if (J[i].a == ta[k]) star = 1;
    printf("  a %08x pattern %d q %d score %.0f%s  bolts on", J[i].a, J[i].p, J[i].q, J[i].sc, star ? " *" : ""); for (int n = 0; n < N; n++) if (PAT[J[i].p][n]) printf(" %d", n); printf("\n"); }
  printf("ratio %.2f\n", J[0].sc / J[1].sc);
  if (truth) { /* no-bolt check against full() */
    int pe = -1; for (int k = 0; k < np; k++) { int z = 1; for (int n = 0; n < N; n++) if (PAT[k][n]) z = 0; if (z) pe = k; }
    fb2full(fwd(truth, 1), 0, 0); float md = 0; for (int q = 0; q < 48; q++) { float d = SC2[pe * 48 + q] - full(truth, q, N, 0); if (d < 0) d = -d; if (d > md) md = d; }
    printf("no-bolt pattern vs full(): max |diff| over q = %.3f (score q0 %.1f)\n", md, full(truth, 0, N, 0)); }
  return 0;
}
