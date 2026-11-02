// Brute-force gRandSeed from Charge rays (two energy_in_out type-6 effects, created on frames 0 and SPAWN_B).
// Model = charge_model.py (verified on emulator logs). Observation = ridge prefix sums from charge_obs.build_maps.
// Stage 1: all 2^32 seeds at the start of frame 0, scored on effect A's initial rays only (21 draws, no nuisance);
//          keep the top K1 (branch and bound against the running K1-th best).
// Stage 2: survivors x first-coin frame q in [0,48) (then 24/48 rule from the rolls): full simulation, all rays of
//          both effects, frames 0..N-1. Prints the top results.
// build: gcc -O3 -march=native -fopenmp -o charge_search charge_search.c -lm
// usage: charge_search MAPS.bin [K1=200000] [SPAWN_B=3] [EXTRA=0] [SEED]  (EXTRA: rand_int(1) steps per frame beyond the 1;
//        SEED: only print that seed's score for each first-coin frame q)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <omp.h>

static int N, ND;
static float *S, *C;     // [N][360][ND+1]
static int SPAWN_B = 3;
static int EXTRA = 0;
static int USE_B = 0;   // env STAGE1B=1: stage 1 also scores effect B's initial rays
#define IDX(n, t, d) (((size_t)(n) * 360 + (t)) * (ND + 1) + (d))

static inline uint32_t adv(uint32_t s) { return s * 0x5D588B65u + 1u; }
static inline uint32_t rint_c(uint32_t *s, uint32_t mx) {   // rand_int for mx >= 2, mx != 100
    uint32_t d = 0xFFFFFFFFu / (mx + 1), v;
    do { *s = adv(*s); v = *s / d; } while (v > mx);
    return v;
}
#define RI(s, MX) ({ uint32_t _v; do { *(s) = adv(*(s)); _v = *(s) / (0xFFFFFFFFu / ((MX) + 1)); } while (_v > (MX)); _v; })
static inline uint32_t r360(uint32_t *s) { return RI(s, 360); }
static inline uint32_t r359(uint32_t *s) { return RI(s, 359); }
static inline uint32_t r10(uint32_t *s) { return RI(s, 10); }
static inline uint32_t r100(uint32_t *s) { uint32_t v = RI(s, 1009); return v / 10; }
static inline uint32_t r1(uint32_t *s) { uint32_t v = RI(s, 1000); return v >= 501; }

static int ALPHA_P[11];
static float seg(int n, int th, float D0, float D1) {
    int b0 = (int)floorf(D0 / 4.0f), b1 = (int)ceilf(D1 / 4.0f);
    if (b0 < 0) b0 = 0; if (b1 > ND) b1 = ND; if (b1 <= b0) return 0;
    float c = C[IDX(n, th, b1)] - C[IDX(n, th, b0)];
    if (c < 3) return 0;
    float m = (S[IDX(n, th, b1)] - S[IDX(n, th, b0)]) / c;
    if (m > 80) m = 80; if (m < -80) m = -80;
    return m;
}
static int alpha0_at(int n) {   // part-0 alpha after the (n+1)-th update
    int t = n + 1, life = 45 - t, a = 0;
    if (life < 16) a = life * 16;
    if (t < 16) a = t * 16 + 15;
    return a;
}
static const float SCALE_I[3] = {1.0f, 0.7f, 0.4f};   // index i % 3 (float math as the game: 1.0 - (i%3)*0.3)
static float *T1, *T1B;   // [3][360][11][11]: effect A / B initial rays
#define TI(k, th, v, sp) ((((size_t)(k) * 360 + (th)) * 11 + (v)) * 11 + (sp))

typedef struct { float sc; uint32_t seed; } Item;
static void heap_push(Item *h, int *n, int K, Item it) {
    if (*n < K) { int i = (*n)++; h[i] = it; while (i > 0) { int p = (i - 1) / 2; if (h[p].sc <= h[i].sc) break; Item t = h[p]; h[p] = h[i]; h[i] = t; i = p; } return; }
    if (it.sc <= h[0].sc) return;
    h[0] = it; int i = 0;
    for (;;) { int l = 2 * i + 1, r = l + 1, m = i; if (l < *n && h[l].sc < h[m].sc) m = l; if (r < *n && h[r].sc < h[m].sc) m = r; if (m == i) break; Item t = h[m]; h[m] = h[i]; h[i] = t; i = m; }
}

// ---- full simulation (stage 2) ----
typedef struct { int speed, u14, th; float posx, scale; int alpha; } Part;
typedef struct { Part p[10]; int life, t, alpha0, alive; float scale0; } Eff;
static void eff_init(Eff *e, uint32_t *s, float scale0) {
    int base = r360(s);
    e->scale0 = scale0; e->life = 45; e->t = 0; e->alpha0 = 0; e->alive = 1;
    for (int i = 1; i <= 10; i++) {
        int sp = r10(s), ph = r10(s);
        Part *p = &e->p[i - 1];
        p->speed = -(sp + 4); p->u14 = -ph; p->posx = (float)((10 + ph) * (sp + 4));
        p->th = (i - 1) * 36 + base; p->scale = (float)(1.0 - (i % 3) * 0.3); p->alpha = 0;
    }
}
static void eff_update(Eff *e, uint32_t *s) {
    e->life--; e->t++;
    if (e->life < 0) { e->alive = 0; return; }
    if (e->life < 16) e->alpha0 = e->life * 16;
    if (e->t < 16) e->alpha0 = e->t * 16 + 15;
    for (int i = 0; i < 10; i++) {
        Part *p = &e->p[i];
        p->u14++;
        if (p->u14 >= 10) { p->u14 = 0; p->posx = (float)(-10 * p->speed); p->th = r359(s); }
        p->posx += p->speed;
        p->alpha = (p->u14 < 0 || p->u14 > 10) ? 0 : ALPHA_P[p->u14];
    }
}
static float eff_score(Eff *e, int n) {
    float sc = 0;
    if (!e->alive || n >= N) return 0;
    for (int i = 0; i < 10; i++) {
        Part *p = &e->p[i];
        if (p->alpha <= 0) continue;
        float a = e->alpha0 * p->alpha / 65025.0f;
        float D0 = e->scale0 * (p->posx + 20), D1 = e->scale0 * (p->posx + 20 + 128 * p->scale);
        sc += a * seg(n, ((p->th % 360) + 360) % 360, D0, D1);
    }
    return sc;
}
static float full_score(uint32_t seed, int q, uint32_t *endseed) {
    uint32_t s = seed; Eff A, B; A.alive = B.alive = 0; int coin_next = q; float sc = 0;
    int last = N > 50 ? N : 50;
    for (int n = 0; n < last; n++) {
        if (n == 0) eff_init(&A, &s, 1.2f);
        if (n == SPAWN_B) eff_init(&B, &s, 0.8f);
        if (n == coin_next) { int v = r100(&s); coin_next = n + (v >= 70 ? 48 : 24); }
        if (A.alive) eff_update(&A, &s);
        if (n >= SPAWN_B && B.alive) eff_update(&B, &s);
        r1(&s); for (int k = 0; k < EXTRA; k++) r1(&s);
        sc += eff_score(&A, n) + (n >= SPAWN_B ? eff_score(&B, n) : 0);
    }
    if (endseed) *endseed = s;
    return sc;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s MAPS.bin [K1] [SPAWN_B] [EXTRA]\n", argv[0]); return 1; }
    int K1 = argc > 2 ? atoi(argv[2]) : 200000;
    if (argc > 3) SPAWN_B = atoi(argv[3]);
    if (argc > 4) EXTRA = atoi(argv[4]);
    USE_B = getenv("STAGE1B") && atoi(getenv("STAGE1B"));
    FILE *f = fopen(argv[1], "rb"); int hdr[2];
    if (!f || fread(hdr, 4, 2, f) != 2) { perror("maps"); return 1; }
    N = hdr[0]; ND = hdr[1];
    size_t sz = (size_t)N * 360 * (ND + 1);
    S = malloc(sz * 4); C = malloc(sz * 4);
    if (fread(S, 4, sz, f) != sz || fread(C, 4, sz, f) != sz) { fprintf(stderr, "short read\n"); return 1; }
    fclose(f);
    for (int u = 0; u <= 10; u++) ALPHA_P[u] = (int)(sinf(u * 18.0f * (float)M_PI / 180.0f) * 255.0f);
    // stage-1 tables: effect A part with scale index k, angle th, phase v, speed sp: rays before the first respawn
    T1 = calloc((size_t)3 * 360 * 11 * 11, sizeof(float)); T1B = calloc((size_t)3 * 360 * 11 * 11, sizeof(float));
    for (int k = 0; k < 3; k++) for (int th = 0; th < 360; th++) for (int v = 0; v <= 10; v++) for (int sp = 0; sp <= 10; sp++) {
        float sc = 0; int spd = sp + 4;
        for (int n = v; n <= v + 8 && n < N; n++) {
            int u = n - v + 1; float posx = (float)((9 + v - n) * spd);
            float a = alpha0_at(n) * ALPHA_P[u] / 65025.0f;
            sc += a * seg(n, th, 1.2f * (posx + 20), 1.2f * (posx + 20 + 128 * SCALE_I[k]));
        }
        T1[TI(k, th, v, sp)] = sc;
        float sb = 0;   // effect B (created on SPAWN_B, scale0 0.8)
        for (int n = v; n <= v + 8 && SPAWN_B + n < N; n++) {
            int u = n - v + 1; float posx = (float)((9 + v - n) * spd);
            float a = alpha0_at(n) * ALPHA_P[u] / 65025.0f;
            sb += a * seg(SPAWN_B + n, th, 0.8f * (posx + 20), 0.8f * (posx + 20 + 128 * SCALE_I[k]));
        }
        T1B[TI(k, th, v, sp)] = sb;
    }
    float MX[3][360], MXB = 0;
    float MXBk[3][360];
    for (int k = 0; k < 3; k++) for (int th = 0; th < 360; th++) { float m = -1e9; for (int j = 0; j < 121; j++) if (T1B[TI(k, th, 0, 0) + j] > m) m = T1B[TI(k, th, 0, 0) + j]; MXBk[k][th] = m; }
    for (int k = 0; k < 3; k++) { float m = -1e9; for (int th = 0; th < 360; th++) if (MXBk[k][th] > m) m = MXBk[k][th]; MXB += 3.4f * m; }   // bound on B's 10 parts (4/3/3 per scale index, generous)
    if (!USE_B) MXB = 0;
    for (int k = 0; k < 3; k++) for (int th = 0; th < 360; th++) { float m = -1e9; for (int v = 0; v <= 10; v++) for (int sp = 0; sp <= 10; sp++) if (T1[TI(k, th, v, sp)] > m) m = T1[TI(k, th, v, sp)]; MX[k][th] = m; }
    if (argc > 5) {   // evaluate one seed: score for every first-coin frame q
        uint32_t sd = (uint32_t)strtoul(argv[5], NULL, 16);
        for (int q = 0; q < 48; q++) printf("q %2d score %.1f\n", q, full_score(sd, q, NULL));
        return 0;
    }
    int nt = omp_get_max_threads();
    Item **heaps = malloc(nt * sizeof(Item *)); int *hn = calloc(nt, sizeof(int));
    for (int t = 0; t < nt; t++) heaps[t] = malloc((size_t)K1 * sizeof(Item));
    #pragma omp parallel
    {
        int tid = omp_get_thread_num(); Item *h = heaps[tid]; int *n = &hn[tid];
        #pragma omp for schedule(dynamic, 1)
        for (int64_t blk = 0; blk < 4096; blk++) {
            for (uint64_t lo = 0; lo < (1u << 20); lo++) {
                uint32_t seed = (uint32_t)((blk << 20) | lo), s = seed;
                int base = r360(&s);
                float thr = (*n < K1) ? -1e30f : h[0].sc;
                float rem = 0;
                int th[10];
                for (int i = 1; i <= 10; i++) { th[i - 1] = ((i - 1) * 36 + base) % 360; rem += MX[i % 3][th[i - 1]]; }
                if (rem + MXB <= thr) continue;
                float sc = 0; int ok = 1;
                for (int i = 1; i <= 10; i++) {
                    int sp = r10(&s), ph = r10(&s);
                    rem -= MX[i % 3][th[i - 1]];
                    sc += T1[TI(i % 3, th[i - 1], ph, sp)];
                    if (sc + rem + MXB <= thr) { ok = 0; break; }
                }
                if (ok && USE_B) {   // effect B: 3 frame steps (+1 if the coin fell in frames 0..2), then its 21 draws
                    float bb = -1e30f;
                    for (int var = 0; var < 2; var++) {
                        uint32_t t = s; for (int k = 0; k < 3 + var; k++) t = adv(t);
                        int bs = r360(&t); float sb = 0;
                        for (int i = 1; i <= 10; i++) { int sp = r10(&t), ph = r10(&t); sb += T1B[TI(i % 3, ((i - 1) * 36 + bs) % 360, ph, sp)]; }
                        if (sb > bb) bb = sb;
                    }
                    sc += bb;
                }
                if (ok) heap_push(h, n, K1, (Item){sc, seed});
            }
        }
    }
    // merge
    Item *all = malloc((size_t)nt * K1 * sizeof(Item)); int na = 0;
    for (int t = 0; t < nt; t++) { memcpy(all + na, heaps[t], hn[t] * sizeof(Item)); na += hn[t]; }
    int cmp(const void *a, const void *b) { float x = ((Item *)a)->sc, y = ((Item *)b)->sc; return x < y ? 1 : x > y ? -1 : 0; }
    qsort(all, na, sizeof(Item), cmp);
    if (na > K1) na = K1;
    fprintf(stderr, "stage 1: kept %d, score range %.1f .. %.1f\n", na, all[0].sc, all[na - 1].sc);
    // stage 2
    typedef struct { float sc; uint32_t seed; int q; float s1; int rank1; } Res;
    Res *res = malloc((size_t)na * sizeof(Res));
    #pragma omp parallel for schedule(dynamic, 256)
    for (int i = 0; i < na; i++) {
        float best = -1e30f; int bq = 0;
        for (int q = 0; q < 48; q++) { float sc = full_score(all[i].seed, q, NULL); if (sc > best) { best = sc; bq = q; } }
        res[i] = (Res){best, all[i].seed, bq, all[i].sc, i};
    }
    int cmpr(const void *a, const void *b) { float x = ((Res *)a)->sc, y = ((Res *)b)->sc; return x < y ? 1 : x > y ? -1 : 0; }
    qsort(res, na, sizeof(Res), cmpr);
    double m = 0, m2 = 0; for (int i = 0; i < na; i++) { m += res[i].sc; m2 += res[i].sc * res[i].sc; }
    m /= na; double sd = sqrt(m2 / na - m * m);
    printf("stage2 mean %.1f sd %.1f over %d survivors\n", m, sd, na);
    for (int i = 0; i < 15 && i < na; i++) {
        uint32_t es; full_score(res[i].seed, res[i].q, &es);
        printf("%2d seed %08x q %2d score %.1f (z %.1f) stage1 %.1f rank1 %d seed_after_%d %08x\n", i, res[i].seed, res[i].q, res[i].sc, (res[i].sc - m) / sd, res[i].s1, res[i].rank1, N > 50 ? N : 50, es);
    }
    return 0;
}
