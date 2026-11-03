/* Native check of the Charge search (same kernel.c as the page's WebAssembly, single thread):
 *   cc -O3 -march=native -DNATIVE -o harness harness.c -lm
 *   harness MAPS.bin [K=16384] [TRUESEED|0] [M2=300]
 * MAPS.bin = int32 N, ND, then float32 S[N][360][ND+1], C[...] (tools/jsmaps.js or readouts/charge_prep.py). Prints the
 * stage times, the true seed's rank among the stage-2 candidates and the two best seeds with their first-coin frame q. */
#include "../kernel.c"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static uint32_t back1(uint32_t s, int n) { for (int i = 0; i < n; i++) s = (s - 1u) * 0x6A76AE6Du; return s; }
static uint32_t fwd(uint32_t s, int n) { for (int i = 0; i < n; i++) s = adv(s); return s; }
typedef struct { float sc; uint32_t s; int q; } Rr;
static int cmp(const void *a, const void *b) { float x = ((Rr *)a)->sc, y = ((Rr *)b)->sc; return x < y ? 1 : x > y ? -1 : 0; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(int argc, char **argv) {
  FILE *f = fopen(argv[1], "rb"); int hdr[2]; if (!f || fread(hdr, 4, 2, f) != 2) return 1; size_t sz = (size_t)hdr[0] * 360 * (hdr[1] + 1);
  N = hdr[0]; ND = hdr[1]; if (fread(S, 4, sz, f) != sz || fread(C, 4, sz, f) != sz) return 1; fclose(f);
  int Kk = argc > 2 ? atoi(argv[2]) : 16384; uint32_t truth = argc > 3 ? strtoul(argv[3], 0, 16) : 0; int M2 = argc > 4 ? atoi(argv[4]) : 300;
  double t0 = now(); prepare(N, ND); setK(Kk); double t1 = now(); long nb[2] = {0, 0};
  for (int e = 0; e < 2; e++) { int ord[361]; for (int b = 0; b < 361; b++) ord[b] = b;
    for (int i = 0; i < 361; i++) for (int j = i + 1; j < 361; j++) if (UB[e][ord[j]] > UB[e][ord[i]]) { int t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
    for (int i = 0; i < 361; i++) { int b = ord[i]; if (UB[e][b] <= thr(e)) break; nb[e]++; stage1(e, b, (uint32_t)b * D360, D360, -1e30f); } }
  double t2 = now();
  int m = 0; Rr *J = malloc(sizeof(Rr) * 3 * KMAX);
  for (int i = 0; i < HN[0]; i++) { uint32_t s0 = back1(HD[0][i], 1); float b0 = s1score(1, fwd(s0, 25)), b1 = s1score(1, fwd(s0, 26)); J[m++] = (Rr){HS[0][i] + (b0 > b1 ? b0 : b1), s0, 0}; }
  for (int i = 0; i < HN[1]; i++) for (int c = 0; c < 2; c++) { uint32_t s0 = back1(HD[1][i], 25 + c); J[m++] = (Rr){HS[1][i] + s1score(0, adv(s0)), s0, 0}; }
  qsort(J, m, sizeof(Rr), cmp); int u = 0;
  for (int i = 0; i < m && u < M2; i++) { int d = 0; for (int k = 0; k < u; k++) if (J[k].s == J[i].s) { d = 1; break; } if (!d) J[u++] = J[i]; }
  int rt = -1; for (int i = 0; i < u; i++) if (J[i].s == truth) rt = i;
  for (int i = 0; i < u; i++) { float *q = qscores(J[i].s), b = -1e30f; int bq = 0; for (int k = 0; k < 48; k++) if (q[k] > b) { b = q[k]; bq = k; } J[i].sc = b; J[i].q = bq; }
  double t3 = now(); qsort(J, u, sizeof(Rr), cmp);
  printf("prep %.2fs stage1 %.2fs (bases %ld+%ld) stage2 %.2fs | joint rank %d | ", t1 - t0, t2 - t1, nb[0], nb[1], t3 - t2, rt);
  for (int i = 0; i < 2; i++) printf("%08x q%d %.0f%s ", J[i].s, J[i].q, J[i].sc, J[i].s == truth ? "*" : "");
  printf("ratio %.2f\n", J[0].sc / J[1].sc);
  return 0;
}
