/* Blooper Power Bounce (value 90): search all 2^32 seeds (written at frame 0 of states/blooper_pb.st) x confirm delays
 * d for long chains. Schedule (emulator-measured): 1 step per frame; coin rand_int(100) first at frame 23, then +24/+48
 * (shine); 6 star draws at d+51+26k (hit k+1); roll k at d+76+26k vs 180,162,145,... (x90/100 each); bounces = 2 + passes.
 * usage: blsearch DLO DHI LOHEX HIHEX KMIN THREADS */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#define MUL 0x5D588B65u
#define NMAX 8192
#define NF 1100
#define NR 34
static uint32_t PA[NMAX], PC[NMAX];
static int TH[NR], DLO, DMAX, KMIN;
static int Fs[8][NF], PRE[8][NF], ROLLF[8][NR];
static inline uint32_t jump(uint32_t s, int n) { return PA[n] * s + PC[n]; }
static const uint32_t D1010 = 0xFFFFFFFFu / 1010;
static const uint32_t SHINE = 700u * (0xFFFFFFFFu / 1010);
typedef struct { uint64_t lo, hi; } job;
static long long hist[8][NR + 1]; static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static void *work(void *a) {
  job *J = a; long long h[8][NR + 1]; memset(h, 0, sizeof h);
  for (uint64_t x = J->lo; x < J->hi; x++) {
    uint32_t S = (uint32_t)x;
    for (int d = DLO; d <= DMAX; d++) {
      int coins = 0, nc = 23, k;
      for (k = 0; k < NR; k++) {
        int r = ROLLF[d - DLO][k];
        while (nc < r) { uint32_t t = jump(S, Fs[d - DLO][nc] + PRE[d - DLO][nc] + coins) * MUL + 1; coins++; nc += (t >= SHINE) ? 48 : 24; }
        uint32_t t = jump(S, Fs[d - DLO][r] + coins) * MUL + 1;
        if ((int)(t / D1010) / 10 > TH[k]) break;
      }
      h[d - DLO][k]++;
      if (k >= KMIN) printf("HIT seed %08x delay %d passes %d (bounces %d)\n", S, d, k, k + 2), fflush(stdout);
    }
  }
  pthread_mutex_lock(&mu); for (int d = 0; d < 8; d++) for (int k = 0; k <= NR; k++) hist[d][k] += h[d][k]; pthread_mutex_unlock(&mu);
  return 0;
}
int main(int argc, char **argv) {
  DLO = atoi(argv[1]); DMAX = atoi(argv[2]); uint64_t lo = strtoull(argv[3], 0, 16), hi = strtoull(argv[4], 0, 16);
  KMIN = atoi(argv[5]); int T = atoi(argv[6]);
  PA[0] = 1; PC[0] = 0; for (int i = 1; i < NMAX; i++) { PA[i] = PA[i-1] * MUL; PC[i] = PC[i-1] * MUL + 1; }
  int c = 200; for (int i = 0; i < NR; i++) { c = c * 90 / 100; TH[i] = c; }
  for (int d = DLO; d <= DMAX; d++) {
    int cnt[NF] = {0}, roll[NF]; for (int f = 0; f < NF; f++) roll[f] = 0;
    for (int k = 0; k <= NR; k++) if (d + 51 + 26 * k < NF) cnt[d + 51 + 26 * k] += 6;
    for (int k = 0; k < NR; k++) { ROLLF[d - DLO][k] = d + 76 + 26 * k; roll[d + 76 + 26 * k] = 1; }
    int acc = 0; for (int f = 0; f < NF; f++) { Fs[d - DLO][f] = acc; PRE[d - DLO][f] = cnt[f] + roll[f]; acc += cnt[f] + roll[f] + 1; }
  }
  // Fs/PRE/ROLLF are indexed by d - DLO
  pthread_t th[8]; job J[8]; uint64_t step = (hi - lo) / T;
  for (int t = 0; t < T; t++) { J[t].lo = lo + t * step; J[t].hi = t == T - 1 ? hi : lo + (t + 1) * step; pthread_create(&th[t], 0, work, &J[t]); }
  for (int t = 0; t < T; t++) pthread_join(th[t], 0);
  for (int k = 0; k <= NR; k++) { long long s = 0; for (int d = 0; d <= DMAX - DLO; d++) s += hist[d][k]; if (s) printf("passes %2d (bounces %2d): %lld\n", k, k + 2, s); }
  return 0;
}
