/* FB2 Power Bounce: what a menu lock can reach. Model = fb2model.py (emulator-matched): per frame lightning draws
 * (rand_int(359); two periodic sources, period 130 at {78,83,113,118} and period 220 at {18,78,88,178}, unknown phases
 * p1, p2 in a real run), then roll k (rand_int(100) at d+71+27(k-1)) or the hit's stars (at d+45+27(k-1)), then the
 * coin (rand_int(100), next draw at frame c0, +24 / +48 after >= 70), then the per-frame step. Frame 0 = the lock moment
 * (seed known), d = frames until the target-screen A.
 * usage: fb2dist NSEEDS DMAX [dmg0] [rngseed] [check SEED d p1 p2 c0]   -> histogram of the best bounce count over d in [0, W]
 * for W = 30, 60, 90, 150, 300 (exact frame), and the best "3-frame safe" count (min over d-1, d, d+1). */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define MUL 0x5D588B65u
static inline uint32_t adv(uint32_t s) { return s * MUL + 1; }
static inline uint32_t ri(uint32_t *s, uint32_t mx) {          /* rand_int; 100 -> internal(1009)/10 */
  uint32_t m = mx == 100 ? 1009 : mx, dv = 0xFFFFFFFFu / (m + 1), v;
  do { *s = adv(*s); v = *s / dv; } while (v > m);
  return mx == 100 ? v / 10 : v;
}
static int TH[32];
static const int A1[] = {78, 83, 113, 118}, A2[] = {18, 78, 88, 178};
static int light(int f, int p1, int p2) {
  int n = 0, a = (f + p1) % 130, b = (f + p2) % 220;
  for (int i = 0; i < 4; i++) n += (a == A1[i]) + (b == A2[i]);
  return n;
}
static int nstars(int dmg) { return dmg >= 9 ? 11 : dmg >= 5 ? 10 : dmg >= 3 ? 8 : 6; }
static int DMG0 = 13;
/* bounces for confirm frame d; lightning phases p1 p2; coin next draw c0 */
static int bounces(uint32_t s, int d, int p1, int p2, int c0, int verbose) {
  int nc = c0, k = 0, hit = 0;
  for (int f = 0; f < d + 71 + 27 * 30; f++) {
    for (int i = light(f, p1, p2); i > 0; i--) ri(&s, 359);
    if (f == d + 71 + 27 * k && k == hit - 1) {
      int v = ri(&s, 100); if (verbose) printf("%d=%d ", f, v);
      if (v > TH[k]) return k + 2;
      k++;
    }
    if (f == d + 45 + 27 * hit) { int dm = DMG0 - hit; if (dm < 1) dm = 1; for (int i = nstars(dm); i > 0; i--) ri(&s, 359); hit++; }
    if (f == nc) { int v = ri(&s, 100); nc += v >= 70 ? 48 : 24; }
    s = adv(s);
  }
  return k + 2;
}
int main(int argc, char **argv) {
  int c = 200; for (int i = 0; i < 32; i++) { c = c * 60 / 100; TH[i] = c; }
  if (argc > 3 && !strcmp(argv[3], "check")) {      /* fb2dist 0 0 check SEED d p1 p2 c0 */
    uint32_t S = strtoul(argv[4], 0, 16); int b = bounces(S, atoi(argv[5]), atoi(argv[6]), atoi(argv[7]), atoi(argv[8]), 1);
    printf("bounces %d\n", b); return 0;
  }
  int N = atoi(argv[1]), DMAX = atoi(argv[2]); if (argc > 3) DMG0 = atoi(argv[3]); srand(argc > 4 ? atoi(argv[4]) : 1);
  static const int W[] = {30, 60, 90, 150, 300}; long hist[5][32] = {{0}}, hsafe[5][32] = {{0}}; long dist1[32] = {0};
  double pk[5][12] = {{0}};   /* P(>= K bounces) when the press lands on the planned frame 50%, one early 25%, one late 25% */
  int *b = malloc(sizeof(int) * (DMAX + 2));
  for (int n = 0; n < N; n++) {
    uint32_t S = ((uint32_t)rand() << 16) ^ (uint32_t)rand(); int p1 = rand() % 130, p2 = rand() % 220, c0 = rand() % 24;
    for (int d = 0; d <= DMAX; d++) { b[d] = bounces(S, d, p1, p2, c0, 0); }
    dist1[b[0]]++;
    for (int w = 0; w < 5; w++) {
      int best = 0, bs = 0;
      for (int d = 0; d <= W[w] && d <= DMAX; d++) {
        if (b[d] > best) best = b[d];
        if (d >= 1 && d + 1 <= DMAX) { int m = b[d]; if (b[d-1] < m) m = b[d-1]; if (b[d+1] < m) m = b[d+1]; if (m > bs) bs = m; }
      }
      hist[w][best]++; hsafe[w][bs]++;
      for (int K = 5; K < 12; K++) { double bp = 0; for (int d = 1; d <= W[w] && d + 1 <= DMAX; d++) {
        double p = 0.5 * (b[d] >= K) + 0.25 * (b[d-1] >= K) + 0.25 * (b[d+1] >= K); if (p > bp) bp = p; } pk[w][K] += bp; }
    }
  }
  printf("one fixed frame: "); for (int k = 0; k < 32; k++) if (dist1[k]) printf("%d:%.4f ", k, (double)dist1[k] / N); printf("\n");
  for (int w = 0; w < 5; w++) {
    printf("window %3d frames: best exact  ", W[w]); for (int k = 0; k < 32; k++) if (hist[w][k]) printf("%d:%.4f ", k, (double)hist[w][k] / N);
    printf("\n                  best 3-safe ");    for (int k = 0; k < 32; k++) if (hsafe[w][k]) printf("%d:%.4f ", k, (double)hsafe[w][k] / N);
    printf("\n                  P(>=K) with a +-1 frame press (50/25/25): "); for (int K = 5; K < 12; K++) printf("%d:%.3f ", K, pk[w][K] / N); printf("\n");
  }
  return 0;
}
