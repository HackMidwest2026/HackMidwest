/* Native check of the Charge search with Final Bowser's star aura as nuisance (FB2 T1-T4; kernel.c fb1score):
 *   cc -O3 -march=native -DNATIVE -o harness_fb1 harness_fb1.c -lm
 *   harness_fb1 MAPS.bin [TRUE_S0|0] [K=16384] [M2=300]
 * Stage 1 on effect A (its creation draws are contiguous: no nuisance), the joint stage with B's base draw 24..24+A_VMAX
 * steps after A's, then the relaxed path score (fb1score) of the best M2. Prints the true seed's joint rank, the best
 * candidates, the ratio and the best path (the extra draws k_n per frame). */
#include "../kernel.c"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
static uint32_t back1(uint32_t s, int n) { for (int i = 0; i < n; i++) s = (s - 1u) * 0x6A76AE6Du; return s; }
static uint32_t fwd(uint32_t s, int n) { for (int i = 0; i < n; i++) s = adv(s); return s; }
typedef struct { float sc; uint32_t a; int v; } Rr;
static int cmp(const void *x, const void *y) { float a = ((Rr *)x)->sc, b = ((Rr *)y)->sc; return a < b ? 1 : a > b ? -1 : 0; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static Rr J[KMAX * (A_VMAX + 2) + 8];
int main(int argc, char **argv) {
  FILE *f = fopen(argv[1], "rb"); int hdr[2]; if (!f || fread(hdr, 4, 2, f) != 2) return 1; size_t sz = (size_t)hdr[0] * 360 * (hdr[1] + 1);
  N = hdr[0]; ND = hdr[1]; if (fread(S, 4, sz, f) != sz || fread(C, 4, sz, f) != sz) return 1; fclose(f);
  uint32_t truth = argc > 2 ? strtoul(argv[2], 0, 16) : 0; int Kk = argc > 3 ? atoi(argv[3]) : 16384, M2 = argc > 4 ? atoi(argv[4]) : 300;
  double t0 = now(); prepare(N, ND); setK(Kk); long nb = 0;
  for (int e = 0; e < 2; e++) { int ord[361]; for (int b = 0; b < 361; b++) ord[b] = b;
    for (int i = 0; i < 361; i++) for (int j = i + 1; j < 361; j++) if (UB[e][ord[j]] > UB[e][ord[i]]) { int t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
    for (int i = 0; i < 361; i++) { int b = ord[i]; if (UB[e][b] <= thr(e)) break; nb++; stage1g(e, b, (uint32_t)b * D360, D360, -1e30f); } }
  double t1 = now(); int m = 0;
  for (int i = 0; i < HN[0]; i++) { uint32_t a = HD[0][i]; float bb = -1e30f; int bv = 0; for (int v = 0; v <= A_VMAX; v++) { float x = s1score(1, fwd(a, 24 + v)); if (x > bb) { bb = x; bv = v; } } J[m++] = (Rr){HS[0][i] + bb, a, bv}; }
  for (int i = 0; i < HN[1]; i++) for (int v = 0; v <= A_VMAX; v++) { uint32_t a = back1(HD[1][i], 24 + v); J[m++] = (Rr){HS[1][i] + s1score(0, a), a, v}; }
  qsort(J, m, sizeof(Rr), cmp); { int u2 = 0; for (int i = 0; i < m && u2 < 4 * M2; i++) { int d = 0; for (int k = 0; k < u2; k++) if (J[k].a == J[i].a) { d = 1; break; } if (!d) J[u2++] = J[i]; } m = u2; }
  uint32_t ta = truth ? fwd(truth, 1) : 0; int rt = -1, rt1 = -1;   /* truth = s0 before frame 0's bolts: try 0..2 bolts */
  for (int i = 0; i < m; i++) for (int k = 0; k < 3; k++) if (truth && J[i].a == fwd(truth, k + 1)) { rt = i; ta = J[i].a; }
  for (int i = 0; i < HN[0]; i++) for (int k = 0; k < 3; k++) if (truth && HD[0][i] == fwd(truth, k + 1)) rt1 = i;
  for (int i = 0; i < HN[1]; i++) for (int k = 0; k < 40; k++) if (truth && HD[1][i] == fwd(truth, k + 1)) rt1 = 100000 + i;
  double t2 = now(); int u = m < M2 ? m : M2;
  for (int i = 0; i < u; i++) J[i].sc = fb1score(J[i].a), J[i].v = ABV;
  double t3 = now(); qsort(J, u, sizeof(Rr), cmp);
  printf("prep+stage1 %.2fs (bases %ld) joint %.2fs stage2 %.2fs (%d) | true in stage-1 heap %s, joint rank %d\n", t1 - t0, nb, t2 - t1, t3 - t2, u, rt1 >= 0 ? "yes" : "no", rt);
  for (int i = 0; i < 5; i++) printf("  a %08x v %d score %.0f%s\n", J[i].a, J[i].v, J[i].sc, J[i].a == ta && truth ? " *" : "");
  printf("ratio %.2f\n", J[0].sc / J[1].sc);
  { /* structured fit of the best: every lightning pattern x q x second coin */
    static const int P130[4] = {78, 83, 113, 118}, P220[4] = {18, 78, 88, 178}; int np = 0;
    for (int p2 = 0; p2 < 220; p2++) for (int p1 = p2 % 5; p1 < 130; p1 += 5) {
      uint8_t row[NMAX]; for (int n = 0; n < N; n++) { int c = 0; for (int i = 0; i < 4; i++) { c += (n + 13 + p1) % 130 == P130[i]; c += (n + 13 + p2) % 220 == P220[i]; } row[n] = (uint8_t)c; }
      int dup = 0; for (int k = 0; k < np && !dup; k++) if (!memcmp(PAT[k], row, N)) dup = 1;
      if (!dup && np < NPATMAX) memcpy(PAT[np++], row, N); }
    setPatterns(np); int *P = fb1path(J[0].a); int v = P[0]; double t4 = now(); float b = fb1struct(J[0].a, v); double t5 = now();
    int nk = 0, nk1 = 0; for (int i = 0; i < np * 96; i++) { if (SC3[i] >= b * 0.998f) nk++; if (SC3[i] >= b * 0.99f) nk1++; }
    printf("struct: v %d best %.1f (relaxed %.1f) %.2fs, within 0.2%%: %d, 1%%: %d\n", v, b, J[0].sc, t5 - t4, nk, nk1);
    int shown = 0; for (int i = 0; i < np * 96 && shown < 6; i++) if (SC3[i] >= b * 0.998f) { int p = i / 96, q = (i % 96) / 2, br = i % 2; float x = fb1aura(p, q, br);
      printf("  p %d q %d br %d %.1f aura(rays j)", p, q, br, x); for (int j = 0; j < 20; j++) printf("%d", XA[j]); printf(" bolts"); for (int n = 0; n < N; n++) if (PAT[p][n]) printf(" %d", n); printf("\n"); shown++; } }
  if (truth) { printf("true A initial %.0f (heap thr %.0f, UB of its base %.0f), true B initial %.0f (v=%d)\n", s1score(0, ta), thr(0), UB[0][ta / D360], s1score(1, fwd(ta, 24 + 1)), 1);
    float bx = -1e30f; int bv = 0; for (int v = 0; v <= A_VMAX; v++) { float x = s1score(1, fwd(ta, 24 + v)); if (x > bx) { bx = x; bv = v; } } printf("  best B over v: %.0f at v %d\n", bx, bv); }
  if (truth) { float x = fb1score(ta); int *P = fb1path(ta); printf("true: score %.0f v %d path", x, P[0]); for (int n = 3; n < N; n++) printf(" %d", P[n]); printf("\n"); }
  return 0;
}
