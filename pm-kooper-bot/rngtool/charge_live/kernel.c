/* Charge rays -> gRandSeed: the search kernel, compiled to WebAssembly for the page's workers (build.sh) and natively
 * for tests (cc -DNATIVE). Model = readouts/charge_model.py (two energy_in_out(6) effects, frames 0 and 3; verified on
 * emulator logs). Observation = ridge prefix sums S/C [N][360][ND+1] built by the page (charge_live.js, maps()).
 *
 * Stage 1, per effect E (A: scale 1.2 created on frame 0 from s0; B: scale 0.8 created on frame 3, its first draw is
 * the 25th (26th if the coin fell in frames 0-2) LCG step after s0): the effect's initial rays depend only on the
 * state s1 after its rand_int(360) base-angle draw, and s1 lies in the base's interval [b*D360, (b+1)*D360). Each base
 * has an upper bound UB(b) = sum over its 10 parts of the best ray score at that part's angle; bases are searched in
 * decreasing UB with branch and bound against the running K-th best (parts in decreasing bound order, each part's two
 * draws by jump constants). A base whose UB is at or below the K-th best cannot hold a top-K seed, so the top K of all
 * 2^32 is exact. The caller (JS) hands out (effect, base, part of the interval) tasks and stops at that bound.
 * Stage 2: candidates ranked by the joint A+B initial-ray score, then the full simulation of both effects over all 48
 * frames for every first-coin frame q (0..47, then the 24/48 rule). */
#include <stdint.h>
#ifdef NATIVE
#include <math.h>
#define FLOOR floorf
#define CEIL ceilf
#else
#define FLOOR __builtin_floorf
#define CEIL __builtin_ceilf
#define EXPORT(n) __attribute__((export_name(n)))
#endif
#ifndef EXPORT
#define EXPORT(n)
#endif
#define NMAX 52
#define NDMAX 96
#define KMAX 65536
static int N = 48, ND = 96;
static float S[NMAX * 360 * (NDMAX + 1)], C[NMAX * 360 * (NDMAX + 1)];
static float T[2][3 * 360 * 121], MX[2][3][360], UB[2][361];
#define IDX(n, t, d) (((n) * 360 + (t)) * (ND + 1) + (d))
static const int ALPHA_P[11] = {0, 78, 149, 206, 242, 255, 242, 206, 149, 78, 0};
static const float SCALE_I[3] = {1.0f, 0.7f, 0.4f};
#define MUL 0x5D588B65u
#define D10 390451572u
#define D360 11897416u
static inline uint32_t adv(uint32_t s) { return s * MUL + 1u; }
#define RI(s, MX_) ({ uint32_t _v; do { *(s) = adv(*(s)); _v = *(s) / (0xFFFFFFFFu / ((MX_) + 1)); } while (_v > (MX_)); _v; })
static inline uint32_t r360(uint32_t *s) { return RI(s, 360); }
static inline uint32_t r359(uint32_t *s) { return RI(s, 359); }
static inline uint32_t r10(uint32_t *s) { return RI(s, 10); }
static inline uint32_t r100(uint32_t *s) { uint32_t v = RI(s, 1009); return v / 10; }
static inline uint32_t r1(uint32_t *s) { uint32_t v = RI(s, 1000); return v >= 501; }

EXPORT("ptrS") float *ptrS(void) { return S; }
EXPORT("ptrC") float *ptrC(void) { return C; }
static float seg(int n, int th, float D0, float D1) {
    int b0 = (int)FLOOR(D0 / 4.0f), b1 = (int)CEIL(D1 / 4.0f);
    if (b0 < 0) b0 = 0; if (b1 > ND) b1 = ND; if (b1 <= b0) return 0;
    float c = C[IDX(n, th, b1)] - C[IDX(n, th, b0)];
    if (c < 3) return 0;
    float m = (S[IDX(n, th, b1)] - S[IDX(n, th, b0)]) / c;
    if (m > 80) m = 80; if (m < -80) m = -80;
    return m;
}
static int alpha0_at(int n) { int t = n + 1, life = 45 - t, a = 0; if (life < 16) a = life * 16; if (t < 16) a = t * 16 + 15; return a; }
static uint32_t JA[24], JC[24];
/* after S and C are filled: stage-1 tables T[e][k][th][v][sp] (rays of a part with scale index k, angle th, start
 * phase v, speed sp, before its first respawn), bounds MX and UB */
EXPORT("prepare") void prepare(int n, int nd) {
    N = n; ND = nd;
    uint32_t a = 1, c = 0; for (int k = 0; k < 24; k++) { JA[k] = a; JC[k] = c; a = a * MUL; c = c * MUL + 1u; }
    for (int e = 0; e < 2; e++) {
        float sc0 = e ? 0.8f : 1.2f; int off = e ? 3 : 0;
        for (int k = 0; k < 3; k++) for (int th = 0; th < 360; th++) {
            float m = -1e30f;
            for (int v = 0; v <= 10; v++) for (int sp = 0; sp <= 10; sp++) {
                float sc = 0; int spd = sp + 4;
                for (int f = v; f <= v + 8 && off + f < N; f++) { int u = f - v + 1; float posx = (float)((9 + v - f) * spd);
                    float al = alpha0_at(f) * ALPHA_P[u] / 65025.0f; sc += al * seg(off + f, th, sc0 * (posx + 20), sc0 * (posx + 20 + 128 * SCALE_I[k])); }
                T[e][(k * 360 + th) * 121 + v * 11 + sp] = sc; if (sc > m) m = sc;
            }
            MX[e][k][th] = m;
        }
        for (int b = 0; b < 361; b++) { float u = 0; for (int i = 1; i <= 10; i++) u += MX[e][i % 3][((i - 1) * 36 + b) % 360]; UB[e][b] = u; }
    }
}
EXPORT("ub") float ub(int e, int b) { return UB[e][b]; }

/* ---- stage 1: per-effect top-K min-heap ---- */
static float HS[2][KMAX]; static uint32_t HD[2][KMAX]; static int HN[2], K = 2048;
EXPORT("setK") void setK(int k) { K = k > KMAX ? KMAX : k; HN[0] = HN[1] = 0; }
static void push(int e, float sc, uint32_t sd) {
    float *h = HS[e]; uint32_t *d = HD[e]; int n = HN[e];
    if (n < K) { int i = n; HN[e] = n + 1; h[i] = sc; d[i] = sd;
        while (i > 0) { int p = (i - 1) >> 1; if (h[p] <= h[i]) break; float t = h[p]; h[p] = h[i]; h[i] = t; uint32_t u = d[p]; d[p] = d[i]; d[i] = u; i = p; } return; }
    if (sc <= h[0]) return;
    h[0] = sc; d[0] = sd; int i = 0;
    for (;;) { int l = 2 * i + 1, r = l + 1, m = i; if (l < n && h[l] < h[m]) m = l; if (r < n && h[r] < h[m]) m = r; if (m == i) break;
        float t = h[m]; h[m] = h[i]; h[i] = t; uint32_t u = d[m]; d[m] = d[i]; d[i] = u; i = m; }
}
EXPORT("thr") float thr(int e) { return HN[e] < K ? -1e30f : HS[e][0]; }
EXPORT("heapN") int heapN(int e) { return HN[e]; }
EXPORT("heapS") float *heapS(int e) { return HS[e]; }
EXPORT("heapD") uint32_t *heapD(int e) { return HD[e]; }
/* seeds s1 in [lo, lo + cnt) of base b (s1 = state right after effect e's base-angle draw) */
EXPORT("stage1") void stage1(int e, int b, uint32_t lo, uint32_t cnt, float ext) {
    int pi[10]; float pm[10], cum[11]; const float *tp[10]; uint32_t pa[10], pc[10], qa[10], qc[10];
    for (int i = 0; i < 10; i++) { pi[i] = i + 1; pm[i] = MX[e][(i + 1) % 3][(i * 36 + b) % 360]; }
    for (int x = 0; x < 10; x++) for (int y = x + 1; y < 10; y++) if (pm[y] > pm[x]) { float t = pm[x]; pm[x] = pm[y]; pm[y] = t; int u = pi[x]; pi[x] = pi[y]; pi[y] = u; }
    cum[10] = 0; for (int x = 9; x >= 0; x--) cum[x] = cum[x + 1] + pm[x];
    for (int x = 0; x < 10; x++) { int i = pi[x]; tp[x] = T[e] + ((i % 3) * 360 + ((i - 1) * 36 + b) % 360) * 121;
        pa[x] = JA[2 * i - 1]; pc[x] = JC[2 * i - 1]; qa[x] = JA[2 * i]; qc[x] = JC[2 * i]; }
    float t = thr(e); if (ext > t) t = ext;
    for (uint32_t k = 0; k < cnt; k++) {
        uint32_t s = lo + k; float sc = 0; int x = 0;
        for (; x < 10; x++) { uint32_t u = pa[x] * s + pc[x], w = qa[x] * s + qc[x]; sc += tp[x][(w / D10) * 11 + u / D10]; if (sc + cum[x + 1] <= t) break; }
        if (x == 10) { push(e, sc, s); t = thr(e); if (ext > t) t = ext; }
    }
}
/* exact initial-ray score of effect e from s1 */
EXPORT("s1score") float s1score(int e, uint32_t s1) {
    int b = s1 / D360; float sc = 0; uint32_t s = s1;
    for (int i = 1; i <= 10; i++) { int sp = r10(&s), ph = r10(&s); sc += T[e][((i % 3) * 360 + ((i - 1) * 36 + b) % 360) * 121 + ph * 11 + sp]; }
    return sc;
}
/* ---- stage 2: the full simulation ---- */
typedef struct { int speed, u14, th; float posx, scale; int alpha; } Part;
typedef struct { Part p[10]; int life, t, alpha0, alive; float scale0; } Eff;
static void eff_init(Eff *e, uint32_t *s, float scale0) {
    int base = r360(s);
    e->scale0 = scale0; e->life = 45; e->t = 0; e->alpha0 = 0; e->alive = 1;
    for (int i = 1; i <= 10; i++) { int sp = r10(s), ph = r10(s); Part *p = &e->p[i - 1];
        p->speed = -(sp + 4); p->u14 = -ph; p->posx = (float)((10 + ph) * (sp + 4)); p->th = (i - 1) * 36 + base; p->scale = (float)(1.0 - (i % 3) * 0.3); p->alpha = 0; }
}
static void eff_update(Eff *e, uint32_t *s) {
    e->life--; e->t++;
    if (e->life < 0) { e->alive = 0; return; }
    if (e->life < 16) e->alpha0 = e->life * 16;
    if (e->t < 16) e->alpha0 = e->t * 16 + 15;
    for (int i = 0; i < 10; i++) { Part *p = &e->p[i]; p->u14++;
        if (p->u14 >= 10) { p->u14 = 0; p->posx = (float)(-10 * p->speed); p->th = r359(s); }
        p->posx += p->speed; p->alpha = (p->u14 < 0 || p->u14 > 10) ? 0 : ALPHA_P[p->u14]; }
}
static float eff_score(Eff *e, int n) {
    float sc = 0; if (!e->alive || n >= N) return 0;
    for (int i = 0; i < 10; i++) { Part *p = &e->p[i]; if (p->alpha <= 0) continue;
        float a = e->alpha0 * p->alpha / 65025.0f;
        sc += a * seg(n, ((p->th % 360) + 360) % 360, e->scale0 * (p->posx + 20), e->scale0 * (p->posx + 20 + 128 * p->scale)); }
    return sc;
}
static int ORDER = 0, SPAWNB = 3, EXTRA = 0;   /* model variants for tests only (the verified model is 0, 3, 0) */
/* score of seed s0 (gRandSeed before frame 0's draws) with the first coin draw on frame q; extra = rand_int(1) steps
 * per frame beyond the one; returns the score, *end = the seed after frame `upto` - 1 */
EXPORT("full") float full(uint32_t seed, int q, int upto, uint32_t *end) {
    uint32_t s = seed; Eff A, B; A.alive = B.alive = 0; int coin_next = q; float sc = 0;
    for (int n = 0; n < upto; n++) {
        if (n == 0) eff_init(&A, &s, 1.2f);
        if (n == SPAWNB) eff_init(&B, &s, 0.8f);
        if (n == coin_next) { int v = r100(&s); coin_next = n + (v >= 70 ? 48 : 24); }
        if (ORDER && n >= SPAWNB && B.alive) eff_update(&B, &s);
        if (A.alive) eff_update(&A, &s);
        if (!ORDER && n >= SPAWNB && B.alive) eff_update(&B, &s);
        r1(&s); for (int k = 0; k < EXTRA; k++) r1(&s);
        sc += eff_score(&A, n) + (n >= SPAWNB ? eff_score(&B, n) : 0);
    }
    if (end) *end = s;
    return sc;
}
EXPORT("setVariant") void setVariant(int order, int spawnb, int extra) { ORDER = order; SPAWNB = spawnb; EXTRA = extra; }
static float QS[48];
EXPORT("qscores") float *qscores(uint32_t seed) { for (int q = 0; q < 48; q++) QS[q] = full(seed, q, N, 0); return QS; }
