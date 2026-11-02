/* Q4: how fast can the seed be found from Spiny Surge rest points, with early rejection?

   Each throw draws rand_int(140) (rest x - 10), rand_int(80) (rest y - 10), rand_int(360), rand_int(10) in a row.
   Between two throws the seed steps once per game frame (rand_int(1)) and once more if the status-bar coin drew in
   that gap (unknown phase: both branches are tried; the coin draws at most once per 24 frames).
   Search: the first throw's x draw is v = s' / d140 with s' the advanced seed, so the seeds with x in an interval are
   one contiguous range of s' -> enumerate only that range (x tolerance / 141 of 2^32), test y on the next draw, then
   follow the later throws (both coin branches), rejecting as soon as an observed throw misses.
   Self-test with a random true seed and simulated observations: x +-XT, y +-YT around the truth (the clip fit gave
   ~0.7 / 0.2 units 1 sd for an isolated spiny, so XT=2, YT=1 is ~3 sd), only every OBS-th throw observed.
   build: gcc -O2 -o surge_search surge_search.c   run: ./surge_search [SEED] [NTHROWS] [GAP] [XT] [YT] [OBS] [FIRSTONLY_X] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define MUL 0x5D588B65u
static inline uint32_t adv(uint32_t s) { return s * MUL + 1u; }
static inline uint32_t rnd(uint32_t *s, uint32_t mx) {          /* rand_int(mx) for mx >= 2, != 100 */
    uint32_t d = 0xFFFFFFFFu / (mx + 1), v;
    do { *s = adv(*s); v = *s / d; } while (v > mx);
    return v;
}
static inline uint32_t rnd1(uint32_t *s) { uint32_t d = 0xFFFFFFFFu / 1001, v; do { *s = adv(*s); v = *s / d; } while (v > 1000); return v >= 501; }

#define MAXT 40
static int NT, GAP, XT, YT, OBS;
static int ox[MAXT], oy[MAXT], seen[MAXT];
static long long nodes;
static uint32_t INV;                                  /* MUL^-1 mod 2^32: seed before = (s' - 1) * INV */

/* s: seed just after throw k's 4 draws; t: frames. Returns number of full matches found (prints them) */
static int follow(uint32_t s, int k, uint32_t start, int coins_since) {
    if (k == NT - 1) { printf("  match: seed before throw 1 = %08x\n", start); return 1; }
    int found = 0;
    for (int coin = 0; coin <= 1; coin++) {
        if (coin && coins_since < 24) continue;     /* coin draws are >= 24 frames apart */
        uint32_t t = s;
        for (int f = 0; f < GAP; f++) rnd1(&t);     /* the frame steps of the gap */
        if (coin) rnd(&t, 1009);                    /* the coin (rand_int(100) uses internal(1009)) */
        uint32_t u = t;
        int x = rnd(&u, 140), y = rnd(&u, 80);
        nodes++;
        if (seen[k + 1] && (abs(x - ox[k + 1]) > XT || abs(y - oy[k + 1]) > YT)) continue;
        rnd(&u, 360); rnd(&u, 10);
        found += follow(u, k + 1, start, coin ? GAP : coins_since + GAP);
    }
    return found;
}

int main(int argc, char **argv) {
    uint32_t truth = argc > 1 ? strtoul(argv[1], 0, 16) : 0x2468ace1u;
    NT = argc > 2 ? atoi(argv[2]) : 20; GAP = argc > 3 ? atoi(argv[3]) : 2;
    XT = argc > 4 ? atoi(argv[4]) : 2; YT = argc > 5 ? atoi(argv[5]) : 1; OBS = argc > 6 ? atoi(argv[6]) : 1;
    int coinphase = (truth >> 7) % 24;              /* frames until the true coin draw (one draw in the window) */
    /* simulate the truth */
    uint32_t s = truth; int fr = 0;
    srand(truth);
    for (int k = 0; k < NT; k++) {
        if (k) { for (int f = 0; f < GAP; f++) { rnd1(&s); fr++; if (fr == coinphase) rnd(&s, 1009); } }
        uint32_t u = s; int x = rnd(&u, 140), y = rnd(&u, 80); rnd(&u, 360); rnd(&u, 10); s = u;
        ox[k] = x + (rand() % (2 * XT + 1)) - XT; oy[k] = y + (rand() % (2 * YT + 1)) - YT;   /* observation error */
        seen[k] = (k % OBS) == 0;
    }
    printf("truth %08x, %d throws %d frames apart, coin draw after %d frames, obs x+-%d y+-%d, every %d-th throw\n",
           truth, NT, GAP, coinphase, XT, YT, OBS);
    INV = MUL; for (int i = 0; i < 5; i++) INV *= 2u - MUL * INV;
    clock_t c0 = clock();
    uint32_t d140 = 0xFFFFFFFFu / 141, d80 = 0xFFFFFFFFu / 81;
    long long cand = 0, pass_y = 0; int found = 0;
    for (int x = ox[0] - XT; x <= ox[0] + XT; x++) {
        if (x < 0 || x > 140) continue;
        uint64_t lo = (uint64_t)x * d140, hi = (uint64_t)(x + 1) * d140;     /* s' (advanced seed) range for this x */
        for (uint64_t sp = lo; sp < hi; sp++) {
            uint32_t a = (uint32_t)sp, b = adv(a);
            cand++;
            int y = b / d80;                                                   /* y draw (rejection: y = 81 never passes) */
            if (y < oy[0] - YT || y > oy[0] + YT) continue;
            pass_y++;
            uint32_t u = b; rnd(&u, 360); rnd(&u, 10);
            found += follow(u, 0, (a - 1u) * INV, 24);       /* coin history unknown: allowed in the first gap */
        }
    }
    double secs = (double)(clock() - c0) / CLOCKS_PER_SEC;
    printf("enumerated %lld advanced seeds (x window), %lld passed y, %lld tree nodes, %d full matches, %.2f s\n",
           cand, pass_y, nodes, found, secs);
    return 0;
}
