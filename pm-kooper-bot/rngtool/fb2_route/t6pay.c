/* Joint payoff of the T6 -> T7 levers after a T6 Charge-ray lock (port of t6model.py; same draws and order).
   Per trial: random gRandSeed at frame 61 after the T6 Charge confirm, random lightning phases (p130, p220), random coin
   phase; flags slam_ok / claw_ok. Levers: K = frame of the A that dismisses the "+3" popup (window [KLO, KLO+KW) within
   77..136), and d = the Power Bounce target-screen A, window [menu+45, menu+45+DW) where menu = the T7 menu frame (it
   depends on Bowser's attack). The page knows the K that actually happened (input display) before planning d.
   Press error per lever: 50% on the frame, 25% one early, 25% one late (or exact with EXACT=1).
   Prints P(Close Call), P(Close Call and >= N bounces) for N = 6, 7, 8, blind and planned, and the mean added frames.
   build: gcc -O2 -o t6pay t6pay.c ; run: ./t6pay TRIALS KLO KW DW SLAM_OK CLAW_OK [EXACT] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef uint32_t u32;
static inline u32 adv(u32 s) { return s * 0x5D588B65u + 1; }
static inline u32 internal(u32 *s, u32 mx) { u32 d = 0xFFFFFFFFu / (mx + 1); if (!d) d = 1; for (;;) { *s = adv(*s); u32 v = *s / d; if (v <= mx) return v; } }
static inline int ri(u32 *s, int mx) { if (mx == 100) return internal(s, 1009) / 10; return internal(s, mx); }
static const int P130[4] = {78, 83, 113, 118}, P220[4] = {18, 78, 88, 178};
static int TH[30];
static int DELTA_CLAW = 62, DELTA_FIRE = 55, DELTA_SLAM = 52, MENU_CLAW = 83, MENU_FIRE = 134, MENU_SLAM = 101;
static int nst(int d) { return d >= 9 ? 11 : d >= 5 ? 10 : d >= 3 ? 8 : 6; }
static int nbolts(int f, int p130, int p220) { int n = 0, a = (f + p130) % 130, b = (f + p220) % 220;
  for (int i = 0; i < 4; i++) { n += a == P130[i]; n += b == P220[i]; } return n; }
typedef struct { u32 s; int nc; } St;
/* advance whole frames f0..f1-1 with only bolts, coin, step */
static void idle(St *t, int f0, int f1, int p130, int p220) {
  for (int f = f0; f < f1; f++) { for (int i = nbolts(f, p130, p220); i; i--) ri(&t->s, 359);
    if (f == t->nc) { int v = ri(&t->s, 100); t->nc += v >= 70 ? 48 : 24; } t->s = adv(t->s); }
}
/* from frame f0 state, K: returns lucky (and fills attack menu frame, state at start of frame T+1) */
static int ai(St *t, int f0, int K, int p130, int p220, int slam_ok, int claw_ok, int *menu, int *Tout) {
  int E = K + 40; idle(t, f0, E, p130, p220);
  int f = E; for (int i = nbolts(f, p130, p220); i; i--) ri(&t->s, 359);
  ri(&t->s, 100); int v80 = ri(&t->s, 80), atk;
  if (v80 < 20 && slam_ok) atk = 0; else { int v60 = ri(&t->s, 60); atk = (v60 < 20 && claw_ok) ? 1 : 2; }
  if (f == t->nc) { int v = ri(&t->s, 100); t->nc += v >= 70 ? 48 : 24; } t->s = adv(t->s);
  int T = E + (atk == 0 ? DELTA_SLAM : atk == 1 ? DELTA_CLAW : DELTA_FIRE);
  idle(t, E + 1, T, p130, p220);
  for (int i = nbolts(T, p130, p220); i; i--) ri(&t->s, 359);
  int cc = ri(&t->s, 100);
  if (T == t->nc) { int v = ri(&t->s, 100); t->nc += v >= 70 ? 48 : 24; } t->s = adv(t->s);
  *menu = T + (atk == 0 ? MENU_SLAM : atk == 1 ? MENU_CLAW : MENU_FIRE); *Tout = T;
  return cc < 30;
}
/* bounces for the confirm on frame d, from state at start of frame f0 (<= d) */
static int pb(St t0, int f0, int d, int p130, int p220, int dmg0) {
  St t = t0; idle(&t, f0, d, p130, p220);
  int k = 0, hit = 0;
  for (int f = d; f < d + 71 + 27 * 20; f++) {
    for (int i = nbolts(f, p130, p220); i; i--) ri(&t.s, 359);
    if (f == d + 71 + 27 * k && k == hit - 1) { int v = ri(&t.s, 100); if (v > TH[k]) return k + 2; k++; }
    if (f == d + 45 + 27 * hit) { int dm = dmg0 - hit; if (dm < 1) dm = 1; for (int i = nst(dm); i; i--) ri(&t.s, 359); hit++; }
    if (f == t.nc) { int v = ri(&t.s, 100); t.nc += v >= 70 ? 48 : 24; }
    t.s = adv(t.s);
  }
  return k + 2;
}
static u32 rng = 12345; static u32 xr(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
int main(int argc, char **argv) {
  int N = atoi(argv[1]), KLO = atoi(argv[2]), KW = atoi(argv[3]), DW = atoi(argv[4]), slam_ok = atoi(argv[5]), claw_ok = atoi(argv[6]);
  int exact = argc > 7 ? atoi(argv[7]) : 0; int dmg0 = 15;
  int c = 200; for (int i = 0; i < 30; i++) { c = c * 60 / 100; TH[i] = c; }
  double w[3] = {0.25, 0.5, 0.25}; if (exact) { w[0] = 0; w[1] = 1; w[2] = 0; }
  double sumL = 0, sumB[3] = {0}, sumJ[3] = {0}, sumWait[3] = {0}, nWait[3] = {0}, blindL = 0, blindB[3] = {0}, sumPlanL = 0;
  int NN[3] = {6, 7, 8};
  for (int tr = 0; tr < N; tr++) {
    u32 s = xr(); int p130 = xr() % 130, p220 = xr() % 220; int nc = 61 + (xr() % 100 < 70 ? xr() % 24 : xr() % 48);
    St t61 = {s, nc};
    /* blind: no press (K = 137), d = earliest */
    { St t = t61; int menu, T; int L = ai(&t, 61, 137, p130, p220, slam_ok, claw_ok, &menu, &T); blindL += L;
      if (L) { int b = pb(t, T + 1, menu + 45, p130, p220, dmg0); for (int j = 0; j < 3; j++) blindB[j] += b >= NN[j]; } }
    /* planned: for each K' in [KLO-1, KLO+KW]: lucky, and best d per target N */
    int nk = KW + 2; double best[3] = {0}; int bestK[3] = {0}; double bestL = 0; double waitK[3] = {0};
    static int luck[200], mn[200]; static double bestd[200][3]; static int bestdw[200][3];
    for (int i = 0; i < nk; i++) {
      int K = KLO - 1 + i; St t = t61; int menu, T; luck[i] = ai(&t, 61, K, p130, p220, slam_ok, claw_ok, &menu, &T); mn[i] = menu;
      for (int j = 0; j < 3; j++) { bestd[i][j] = 0; bestdw[i][j] = 0; }
      if (!luck[i]) continue;
      int D0 = menu + 45; static int bb[200];
      for (int q = 0; q < DW + 2; q++) bb[q] = pb(t, T + 1, D0 - 1 + q, p130, p220, dmg0);
      for (int j = 0; j < 3; j++) for (int q = 1; q <= DW; q++) {
        double p = w[0] * (bb[q - 1] >= NN[j]) + w[1] * (bb[q] >= NN[j]) + w[2] * (bb[q + 1] >= NN[j]);
        if (p > bestd[i][j] + 1e-9) { bestd[i][j] = p; bestdw[i][j] = q - 1; } }
    }
    for (int i = 1; i <= KW; i++) {
      double L = w[0] * luck[i - 1] + w[1] * luck[i] + w[2] * luck[i + 1]; if (L > bestL) bestL = L;
      for (int j = 0; j < 3; j++) { double v = w[0] * bestd[i - 1][j] + w[1] * bestd[i][j] + w[2] * bestd[i + 1][j];
        if (v > best[j] + 1e-9) { best[j] = v; bestK[j] = i - 1; waitK[j] = (KLO + i - 1 - 77) + bestdw[i][j]; } }
    }
    sumPlanL += bestL; for (int j = 0; j < 3; j++) { sumJ[j] += best[j]; if (best[j] > 0) { sumWait[j] += waitK[j]; nWait[j]++; } }
  }
  printf("trials %d K window [%d,%d) d window %d slam_ok %d claw_ok %d press %s\n", N, KLO, KLO + KW, DW, slam_ok, claw_ok, exact ? "exact" : "50/25/25");
  printf("blind (no popup press, earliest d): P(CC) %.3f  P(CC & >=6) %.4f  >=7 %.4f  >=8 %.5f\n", blindL / N, blindB[0] / N, blindB[1] / N, blindB[2] / N);
  printf("planned: P(CC) %.3f  P(CC & >=6) %.3f  >=7 %.3f  >=8 %.4f\n", sumPlanL / N, sumJ[0] / N, sumJ[1] / N, sumJ[2] / N);
  printf("mean added frames vs the fastest play (popup A on 77, earliest target A), when a plan exists, >=6/7/8: %.1f %.1f %.1f (no press at all costs 60)\n",
         sumWait[0] / (nWait[0] + 1e-9), sumWait[1] / (nWait[1] + 1e-9), sumWait[2] / (nWait[2] + 1e-9));
  return 0;
}
