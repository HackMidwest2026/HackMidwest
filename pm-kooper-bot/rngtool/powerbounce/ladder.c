/* High Power Bounce Manipulator: how long after a lock until a confirm frame gives >= K bounces (Blooper, FB2).
 * Models: blmodel.py (Blooper, 150/150 emulator matches) and fb2model.py (FB2, 113/113). Per random locked state (seed,
 * coin phase, FB2 lightning phases), scans confirm frames d = LEAD .. LEAD+H and records, for each K, the first d with
 * bounces >= K, plus whether d-1 / d+1 also reach K (a press one frame off). Also counts frames with >= K (per-frame p).
 * usage: ladder BOSS(bl|fb) DM(0/1) NSEEDS H LEAD THREADS SEED0      (frames are game frames, 30 per second) */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#define MUL 0x5D588B65u
#define KM 40
static int BOSS, DM, NS, H, LEAD, T; static uint32_t SEED0;
static int TH[KM];
static uint32_t PA[2048], PC[2048];
static inline uint32_t adv(uint32_t s) { return s * MUL + 1; }
static inline uint32_t jump(uint32_t s, int n) { while (n >= 2048) { s = PA[2047] * s + PC[2047]; n -= 2047; } return PA[n] * s + PC[n]; }
static inline uint32_t ri(uint32_t *s, uint32_t mx) {          /* rand_int(mx) for 100 or 359 */
  uint32_t m = mx == 100 ? 1009 : mx, dv = 0xFFFFFFFFu / (m + 1), v;
  do { *s = adv(*s); v = *s / dv; } while (v > m);
  return mx == 100 ? v / 10 : v;
}
static const int A130[4] = {78, 83, 113, 118}, A220[4] = {18, 78, 88, 178};
static inline int light(long f, int p130, int p220) {
  if (BOSS == 0) return 0;
  int a = (f + p130) % 130, b = (f + p220) % 220, n = 0;
  for (int i = 0; i < 4; i++) n += (A130[i] == a) + (A220[i] == b);
  return n;
}
static inline int nstars(int dmg) { return dmg >= 9 ? 11 : dmg >= 5 ? 10 : dmg >= 3 ? 8 : 6; }
/* bounces for confirm frame d, starting from the base state at frame d: seed s (start of frame d), next coin nc */
static int bounces(uint32_t s, long d, long nc, int p130, int p220) {
  int R = BOSS ? 71 : 76, S = BOSS ? 45 : 51, P = BOSS ? 27 : 26;
  int k = 0, hit = 0; long f = d;
  for (;;) {
    long fs = d + S + (long)P * hit, fr = d + R + (long)P * k;
    long ev = (hit == k) ? fs : fr;                 /* next bounce event */
    /* advance frame by frame only over frames with lightning or coin; otherwise jump */
    while (f < ev) {
      long nxt = ev; if (nc < nxt) nxt = nc;
      if (BOSS) { long g = f; while (g < nxt && !light(g, p130, p220)) g++; nxt = g; }
      s = jump(s, (int)(nxt - f)); f = nxt;
      if (f >= ev) break;
      for (int i = light(f, p130, p220); i > 0; i--) ri(&s, 359);
      if (f == nc) nc += ri(&s, 100) >= 70 ? 48 : 24;
      s = adv(s); f++;
    }
    for (int i = light(f, p130, p220); i > 0; i--) ri(&s, 359);
    if (hit == k) {
      int dmg = BOSS ? (13 - hit < 1 ? 1 : 13 - hit) : 1;
      for (int i = nstars(dmg); i > 0; i--) ri(&s, 359);
      hit++;
    } else {
      if ((int)ri(&s, 100) > TH[k]) return k + 2;
      k++; if (k >= KM - 1) return k + 2;
    }
    if (f == nc) nc += ri(&s, 100) >= 70 ? 48 : 24;
    s = adv(s); f++;
  }
}
static long long FIRST[100000][KM + 3]; static signed char NB[100000][KM + 3];
static long long CNT[KM + 3]; static long long TOT; static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static int next_i = 0;
static void *work(void *a) {
  long N = LEAD + H + 2; uint32_t *bs = malloc(N * 4); long *bn = malloc(N * sizeof(long)); signed char *b = malloc(N);
  long long cnt[KM + 3];
  for (;;) {
    pthread_mutex_lock(&mu); int i = next_i++; pthread_mutex_unlock(&mu);
    if (i >= NS) break;
    uint32_t r = SEED0 ^ (uint32_t)(i * 0x9E3779B9u); for (int j = 0; j < 7; j++) r = adv(r) ^ (r >> 13);
    uint32_t s = r; int p130 = (r >> 3) % 130, p220 = (r >> 11) % 220; long nc = (r >> 20) % 24;
    if (BOSS) p130 = (p130 / 5) * 5 + (p220 % 5) - ((p130 / 5) * 5 + (p220 % 5) >= 130 ? 5 : 0); /* mod-5 assumption */
    for (long f = 0; f < N; f++) {                   /* base sequence (no bounce) */
      bs[f] = s; bn[f] = nc;
      for (int j = light(f, p130, p220); j > 0; j--) ri(&s, 359);
      if (f == nc) nc += ri(&s, 100) >= 70 ? 48 : 24;
      s = adv(s);
    }
    memset(cnt, 0, sizeof cnt);
    for (long d = LEAD - 1; d < N; d++) b[d] = bounces(bs[d], d, bn[d], p130, p220);
    for (int K = 0; K <= KM + 2; K++) { FIRST[i][K] = -1; NB[i][K] = 0; }
    for (long d = LEAD; d < N - 1; d++) {
      int v = b[d]; if (v > KM + 2) v = KM + 2;
      for (int K = 2; K <= v; K++) {
        cnt[K]++;
        if (FIRST[i][K] < 0) { FIRST[i][K] = d - LEAD; NB[i][K] = (b[d - 1] >= K) + 2 * (b[d + 1] >= K); }
      }
    }
    pthread_mutex_lock(&mu); for (int K = 0; K <= KM + 2; K++) CNT[K] += cnt[K]; TOT += N - 1 - LEAD; pthread_mutex_unlock(&mu);
  }
  return 0;
}
static int cmpll(const void *a, const void *b) { long long x = *(long long *)a, y = *(long long *)b; return x < y ? -1 : x > y; }
int main(int argc, char **argv) {
  if (!strcmp(argv[1], "chk")) {   /* stdin: boss(b/f) dm seedhex d p130 p220 coinNext -> bounces (model cross-check) */
    PA[0] = 1; PC[0] = 0; for (int i = 1; i < 2048; i++) { PA[i] = PA[i - 1] * MUL; PC[i] = PC[i - 1] * MUL + 1; }
    char bb[4]; uint32_t sd; long d, nc; int p130, p220, dm;
    while (scanf("%3s %d %x %ld %d %d %ld", bb, &dm, &sd, &d, &p130, &p220, &nc) == 7) {
      BOSS = bb[0] == 'f'; int c = 200, val = (BOSS ? 60 : 90) + (dm ? 7 : 0); for (int i = 0; i < KM; i++) { c = c * val / 100; TH[i] = c; }
      uint32_t s = sd; for (long f = 0; f < d; f++) { for (int j = light(f, p130, p220); j > 0; j--) ri(&s, 359); if (f == nc) nc += ri(&s, 100) >= 70 ? 48 : 24; s = adv(s); }
      printf("%d\n", bounces(s, d, nc, p130, p220));
    }
    return 0;
  }
  BOSS = argv[1][0] == 'f'; DM = atoi(argv[2]); NS = atoi(argv[3]); H = atoi(argv[4]); LEAD = atoi(argv[5]); T = atoi(argv[6]);
  SEED0 = strtoul(argv[7], 0, 16);
  PA[0] = 1; PC[0] = 0; for (int i = 1; i < 2048; i++) { PA[i] = PA[i - 1] * MUL; PC[i] = PC[i - 1] * MUL + 1; }
  int c = 200, val = (BOSS ? 60 : 90) + (DM ? 7 : 0); for (int i = 0; i < KM; i++) { c = c * val / 100; TH[i] = c; }
  pthread_t th[16]; for (int t = 0; t < T; t++) pthread_create(&th[t], 0, work, 0); for (int t = 0; t < T; t++) pthread_join(th[t], 0);
  printf("# boss %s dm %d seeds %d horizon %d frames (%.1f min) lead %d; frames scanned %lld\n", BOSS ? "fb2" : "blooper", DM, NS, H, H / 1800.0, LEAD, TOT);
  printf("# K  p_frame      found  med_s     p90_s    (geom med_s  p90_s)   P(>=K) press 50/25/25\n");
  static long long w[100000];
  for (int K = 3; K <= KM + 2; K++) {
    if (!CNT[K]) break;
    int n = 0; double rob = 0;
    for (int i = 0; i < NS; i++) if (FIRST[i][K] >= 0) { w[n++] = FIRST[i][K]; rob += 0.5 + 0.25 * (NB[i][K] & 1) + 0.25 * ((NB[i][K] >> 1) & 1); }
    qsort(w, n, sizeof w[0], cmpll);
    double p = (double)CNT[K] / TOT;
    char med[32] = "-", p90[32] = "-";
    if (n > NS / 2) sprintf(med, "%.1f", w[NS / 2] / 30.0);
    if (n > NS * 9 / 10) sprintf(p90, "%.1f", w[NS * 9 / 10] / 30.0);
    printf("%3d  %.3e  %5d  %8s  %8s   (%9.1f %9.1f)   %.3f\n", K, p, n, med, p90, 0.6931 / p / 30, 2.3026 / p / 30, n ? rob / n : 0);
  }
  return 0;
}
