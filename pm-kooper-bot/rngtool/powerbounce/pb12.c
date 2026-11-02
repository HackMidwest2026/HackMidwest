/* Final Bowser phase 2 Power Bounce: search all 2^32 seeds (written at frame 0 of states/fb2_t7like_pb.st) x confirm
 * delays d for long bounce chains. Schedule (emulator-measured): lightning draws on fixed frames (before the coin),
 * coin first at frame 3 then +24/+48, per bounce k: firework stars at d+45+27(k-1) (count by damage 13,12,...: 11 for
 * 9+, 10 for 5-8, 8 for 3-4, 6 for 1-2), roll k at d+71+27(k-1) vs 120,72,43,25,15,9,5,3,1,0,0,0 (bounces = 2 + passes).
 * Fixed: on a frame with lightning the lightning draws come before the roll (the old code put the roll first, which made
 * delay 2 / seed 29531ef7 predict 12 where the emulator gives 7). */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#define MUL 0x5D588B65u
#define NMAX 4096
static uint32_t PA[NMAX], PC[NMAX];
static const int LIGHT[] = {23,28,88,118,123,148,153,158,208,218,248,253,283,288,308,368,378,383,413,418,428,438,508,513,528,543,548,588,638,643,648,658,673,678};
static const int TH[] = {120,72,43,25,15,9,5,3,1,0,0,0,0};
#define NR 12
#define KMIN 10
static int DMAX, DLO;
static int Fs[256][800], PRE[256][800];          // steps before frame f's draws (no coins); draws before the coin on frame f
static int ROLLF[256][NR], ROLLOFF[256][NR];
static inline uint32_t jump(uint32_t s, int n) { return PA[n] * s + PC[n]; }
static const uint32_t D1010 = 0xFFFFFFFFu / 1010;
static const uint32_t SHINE = 700u * (0xFFFFFFFFu / 1010);
typedef struct { uint32_t lo, hi; int t; } job;
static long long hist[256][16]; static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static void *work(void *a) {
  job *J = a; static __thread long long h[256][16]; memset(h, 0, sizeof h);
  for (uint64_t x = J->lo; x < J->hi; x++) {
    uint32_t S = (uint32_t)x;
    for (int d = DLO; d <= DMAX; d++) {
      int coins = 0, nc = 3, k;
      for (k = 0; k < NR; k++) {
        int r = ROLLF[d][k];
        while (nc <= r) {                         // coin draws on frames before the roll frame (on the roll frame: after it)
          if (nc == r) break;
          uint32_t t = jump(S, Fs[d][nc] + PRE[d][nc] + coins) * MUL + 1;
          coins++; nc += (t >= SHINE) ? 48 : 24;
        }
        uint32_t t = jump(S, Fs[d][r] + ROLLOFF[d][k] + coins) * MUL + 1;
        int roll = (int)(t / D1010) / 10;
        if (roll > TH[k]) break;
      }
      h[d][k]++;
      if (k >= KMIN) printf("HIT seed %08x delay %d passes %d (bounces %d)\n", S, d, k, k + 2), fflush(stdout);
    }
  }
  pthread_mutex_lock(&mu); for (int d = 0; d < 256; d++) for (int k = 0; k < 16; k++) hist[d][k] += h[d][k]; pthread_mutex_unlock(&mu);
  return 0;
}
int main(int argc, char **argv) {
  DLO = atoi(argv[1]); DMAX = atoi(argv[2]); uint64_t lo = strtoull(argv[3], 0, 16), hi = strtoull(argv[4], 0, 16); int T = 2;
  PA[0] = 1; PC[0] = 0; for (int i = 1; i < NMAX; i++) { PA[i] = PA[i-1] * MUL; PC[i] = PC[i-1] * MUL + 1; }
  for (int d = DLO; d <= DMAX; d++) {
    int cnt[800] = {0}, roll[800]; for (int f = 0; f < 800; f++) roll[f] = -1;
    for (int i = 0; i < (int)(sizeof LIGHT / sizeof *LIGHT); i++) cnt[LIGHT[i]]++;
    for (int k = 1; k <= 13; k++) { int dmg = 13 - (k - 1); if (dmg < 1) dmg = 1; int n = dmg >= 9 ? 11 : dmg >= 5 ? 10 : dmg >= 3 ? 8 : 6; cnt[d + 45 + 27 * (k - 1)] += n; }
    int lc[800] = {0}; for (int i = 0; i < (int)(sizeof LIGHT / sizeof *LIGHT); i++) lc[LIGHT[i]]++;
    for (int k = 0; k < NR; k++) { int f = d + 71 + 27 * k; ROLLF[d][k] = f; ROLLOFF[d][k] = lc[f]; roll[f] = k; }   // lightning first, then the roll (fb2model.py)
    int acc = 0; for (int f = 0; f < 800; f++) { Fs[d][f] = acc; PRE[d][f] = cnt[f] + (roll[f] >= 0); acc += cnt[f] + (roll[f] >= 0) + 1; }
  }
  pthread_t th[8]; job J[8]; uint64_t step = (hi - lo) / T;
  for (int t = 0; t < T; t++) { J[t].lo = lo + t * step; J[t].hi = t == T - 1 ? hi : lo + (t + 1) * step; J[t].t = t; pthread_create(&th[t], 0, work, &J[t]); }
  for (int t = 0; t < T; t++) pthread_join(th[t], 0);
  for (int k = 0; k <= NR; k++) { long long s = 0; for (int d = DLO; d <= DMAX; d++) s += hist[d][k]; printf("passes %2d (bounces %2d): %lld\n", k, k + 2, s); }
  return 0;
}
