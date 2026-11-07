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
 * frames for every first-coin frame q (0..47, then the 24/48 rule).
 *
 * Nuisance draws (Final Bowser: the stage lightning, fb2_route/t6_raycheck.py): each bolt starting on a frame draws one
 * rand_int(359) before everything else on that frame. The page hands the possible bolt patterns over the 48 frames
 * (setPatterns: one count per frame, from the lightning loops' phases) and stage 2 scores every pattern x q (fb2full):
 * all draws are single LCG steps, so a pattern only shifts the stream, and the score is a sum over frames of
 * g[n][k] = the score of frame n's respawned rays when k extra draws (bolts + coins) came before them; with prefix
 * sums over n each (pattern, q) costs one lookup per insertion. Effect B's creation moves with the bolts on frames 1-3
 * and a coin on frames 0-2 (variant v = their count), so its parts and the respawn schedule are per variant. */
#include <stdint.h>
#ifdef NATIVE
#include <math.h>
#define FLOOR floorf
#define CEIL ceilf
#else
#define FLOOR __builtin_floorf
#define CEIL __builtin_ceilf
#define EXPORT(n) __attribute__((export_name(n)))
__attribute__((no_builtin("memset"))) void *memset(void *d, int c, unsigned long n) { unsigned char *p = d; while (n--) *p++ = (unsigned char)c; return d; }   /* no libc in the wasm build */
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
static uint32_t JA[64], JC[64];
/* after S and C are filled: stage-1 tables T[e][k][th][v][sp] (rays of a part with scale index k, angle th, start
 * phase v, speed sp, before its first respawn), bounds MX and UB */
EXPORT("prepare") void prepare(int n, int nd) {
    N = n; ND = nd;
    uint32_t a = 1, c = 0; for (int k = 0; k < 64; k++) { JA[k] = a; JC[k] = c; a = a * MUL; c = c * MUL + 1u; }
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
/* stage1 by strides (same result as stage1, faster): s = lo + r + g*t. For the part with the largest bound (x = 0), its
 * two draws u = pa*s + pc and w = qa*s + qc move by the constants du = pa*g, dw = qa*g (mod 2^32) per step of t; g is
 * chosen so that both are small, so along t the part's (speed, phase) cell stays the same for runs of ~40 seeds. Each
 * run is scored once for that part; a run whose part-0 score plus the other parts' bounds cannot beat the threshold is
 * skipped whole, the others are scored seed by seed for parts 1..9 as in stage1. */
static uint32_t GSTEP[11]; static int32_t GDU[11], GDW[11];
static void gpick(int i) {     /* g in [1, 2^18] minimising max(|JA[2i-1] g|, |JA[2i] g|) as signed 32-bit values */
    uint32_t a = JA[2 * i - 1], b = JA[2 * i], best = 0xFFFFFFFFu, bg = 1;
    for (uint32_t g = 1; g <= (1u << 18); g++) { int32_t x = (int32_t)(a * g), y = (int32_t)(b * g);
        uint32_t m = (uint32_t)(x < 0 ? -(int64_t)x : x), n = (uint32_t)(y < 0 ? -(int64_t)y : y); if (n > m) m = n;
        if (m < best) { best = m; bg = g; } }
    GSTEP[i] = bg; GDU[i] = (int32_t)(a * bg); GDW[i] = (int32_t)(b * bg);
}
/* steps t >= 1 until floor(v / D10) changes when v moves by d per step (64-bit, v in [0, 2^32), wrap at 2^32) */
static inline uint32_t cellrun(uint32_t v, int32_t d) {
    uint64_t c = v / D10, V = v;
    if (d > 0) { uint64_t B = (c + 1) * (uint64_t)D10; if (B > 4294967296ull) B = 4294967296ull; return (uint32_t)((B - V + (uint64_t)d - 1) / (uint64_t)d); }
    uint64_t B = c * (uint64_t)D10, ad = (uint64_t)(-(int64_t)d); return (uint32_t)((V - B) / ad + 1);
}
EXPORT("stage1g") void stage1g(int e, int b, uint32_t lo, uint32_t cnt, float ext) {
    int pi[10]; float pm[10], cum[11]; const float *tp[10]; uint32_t pa[10], pc[10], qa[10], qc[10];
    for (int i = 0; i < 10; i++) { pi[i] = i + 1; pm[i] = MX[e][(i + 1) % 3][(i * 36 + b) % 360]; }
    for (int x = 0; x < 10; x++) for (int y = x + 1; y < 10; y++) if (pm[y] > pm[x]) { float t = pm[x]; pm[x] = pm[y]; pm[y] = t; int u = pi[x]; pi[x] = pi[y]; pi[y] = u; }
    cum[10] = 0; for (int x = 9; x >= 0; x--) cum[x] = cum[x + 1] + pm[x];
    for (int x = 0; x < 10; x++) { int i = pi[x]; tp[x] = T[e] + ((i % 3) * 360 + ((i - 1) * 36 + b) % 360) * 121;
        pa[x] = JA[2 * i - 1]; pc[x] = JC[2 * i - 1]; qa[x] = JA[2 * i]; qc[x] = JC[2 * i]; }
    int i0 = pi[0]; if (!GSTEP[i0]) gpick(i0);
    uint32_t g = GSTEP[i0]; int32_t du = GDU[i0], dw = GDW[i0];
    float t = thr(e); if (ext > t) t = ext;
    for (uint32_t r = 0; r < g && r < cnt; r++) {
        uint32_t s = lo + r, n = (cnt - r + g - 1) / g, u = pa[0] * s + pc[0], w = qa[0] * s + qc[0];
        for (uint32_t k = 0; k < n;) {
            uint32_t m = cellrun(u, du), m2 = cellrun(w, dw); if (m2 < m) m = m2; if (m > n - k) m = n - k;
            float s0 = tp[0][(w / D10) * 11 + u / D10];
            if (s0 + cum[1] > t) {
                for (uint32_t j = 0; j < m; j++) {
                    uint32_t ss = s + g * j; float sc = s0; int x = 1;
                    for (; x < 10; x++) { uint32_t uu = pa[x] * ss + pc[x], ww = qa[x] * ss + qc[x]; sc += tp[x][(ww / D10) * 11 + uu / D10]; if (sc + cum[x + 1] <= t) break; }
                    if (x == 10) { push(e, sc, ss); t = thr(e); if (ext > t) t = ext; }
                }
            }
            k += m; s += g * m; u += (uint32_t)du * m; w += (uint32_t)dw * m;
        }
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

/* ---- stage 2 with nuisance bolts (Final Bowser) ---- */
#define NPATMAX 2048
#define KM 10
static uint8_t PAT[NPATMAX][NMAX]; static int NPAT = 0;
static float SC2[NPATMAX * 48];
EXPORT("patPtr") uint8_t *patPtr(void) { return &PAT[0][0]; }
EXPORT("setPatterns") void setPatterns(int n) { NPAT = n > NPATMAX ? NPATMAX : n; }
EXPORT("sc2Ptr") float *sc2Ptr(void) { return SC2; }
typedef struct { int e, n, spd; float scale, scale0; } Ev;
static float G2[4][KM + 1][NMAX + 1];   /* prefix sums over n of g_v[n][k] (frames 3..N-1) */
static float INIT2[4]; static int P0V[4][NMAX + 1]; static uint32_t Y0[4]; static int VOK[4];
static int alpha0h(int n) { int t = n + 1, life = 45 - t; if (t < 16) return t * 16 + 15; if (life < 16) return life * 16; return 255; }   /* held at 255 in between */
/* exact score of effect e's initial rays (as in full(); s1score's table drops the held master alpha on t = 16..19) */
static float initscore(int e, uint32_t s1) {
    int b = s1 / D360, off = e ? 3 : 0; float sc0 = e ? 0.8f : 1.2f, sc = 0; uint32_t s = s1;
    for (int i = 1; i <= 10; i++) { int sp = r10(&s), ph = r10(&s), th = ((i - 1) * 36 + b) % 360;
        for (int f = ph; f <= ph + 8 && off + f < N; f++) { int u = f - ph + 1; float posx = (float)((9 + ph - f) * (sp + 4));
            float al = alpha0h(f) * ALPHA_P[u] / 65025.0f; sc += al * seg(off + f, th, sc0 * (posx + 20), sc0 * (posx + 20 + 128 * SCALE_I[i % 3])); } }
    return sc;
}
static float evscore(const Ev *E, int th) {
    float sc = 0;
    for (int j = 1; j <= 9; j++) { int f = E->n + j; if (f >= N) break;
        if (E->e == 0 && f >= 45) break; if (E->e == 1 && f >= 48) break;
        float a0 = (float)alpha0h(E->e ? f - 3 : f), a = a0 * ALPHA_P[j] / 65025.0f; float posx = (float)((9 - j) * E->spd);
        sc += a * seg(f, th, E->scale0 * (posx + 20), E->scale0 * (posx + 20 + 128 * E->scale)); }
    return sc;
}
/* variant v: effect B created from fwd(a, 24 + v); builds the respawn events per frame, then g and its prefix sums */
static void fb2variant(uint32_t a, int v) {
    int sp[2][10], ph[2][10]; uint32_t s = a;
    for (int i = 0; i < 10; i++) { sp[0][i] = r10(&s); ph[0][i] = r10(&s); }
    uint32_t sb = JA[24 + v] * a + JC[24 + v]; s = sb; INIT2[v] = initscore(0, a) + initscore(1, sb);
    for (int i = 0; i < 10; i++) { sp[1][i] = r10(&s); ph[1][i] = r10(&s); }
    Y0[v] = s;                                    /* after B's creation */
    /* respawns per frame: A part i wraps on frames 9 + ph + 10 m (< 45), B part i on 12 + ph + 10 m (< 48); A first */
    static Ev ev[NMAX][24]; int ne[NMAX]; for (int n = 0; n < N; n++) ne[n] = 0;
    for (int e = 0; e < 2; e++) for (int i = 0; i < 10; i++) for (int n = (e ? 12 : 9) + ph[e][i]; n < (e ? 48 : 45) && n < N; n += 10)
        ev[n][ne[n]++] = (Ev){e, n, sp[e][i] + 4, (float)(1.0 - ((i + 1) % 3) * 0.3), e ? 0.8f : 1.2f};
    /* order inside a frame: A's parts then B's, each in index order (the loop above adds A first, parts in order) */
    int P = 0; for (int n = 3; n <= N; n++) { P0V[v][n] = P; if (n < N) P += ne[n] + 1; }
    static uint32_t Y[NMAX * 26 + KM + 8]; int ny = P + KM + 4; Y[0] = s; for (int i = 1; i < ny; i++) Y[i] = adv(Y[i - 1]);
    for (int k = 0; k <= KM; k++) { float acc = 0; G2[v][k][3] = 0;
        for (int n = 3; n < N; n++) { float g = 0; int base = P0V[v][n] + k;
            for (int j = 0; j < ne[n]; j++) { uint32_t y = Y[base + 1 + j]; uint32_t th = y / (0xFFFFFFFFu / 360); if (th > 359) th = 359; g += evscore(&ev[n][j], (int)th); }
            acc += g; G2[v][k][n + 1] = acc; } }
    VOK[v] = 1;
}
static inline uint32_t jump(uint32_t s, int n) { uint32_t a = 1, c = 0, m = MUL, d = 1u; /* s -> fwd(s, n) */
    while (n) { if (n & 1) { a = a * m; c = c * m + d; } d = d * (m + 1u); m = m * m; n >>= 1; } return a * s + c; }
static inline int r100v(uint32_t st) { uint32_t v = st / (0xFFFFFFFFu / 1010); if (v > 1009) v = 1009; return (int)(v / 10); }
/* every pattern x first-coin frame q for candidate a (state right after effect A's base-angle draw): scores into SC2
 * (pattern-major); returns the best, *bp / *bq its pattern and q */
static uint32_t VA = 0xFFFFFFFFu; static int VAOK = 0;
EXPORT("fb2full") float fb2full(uint32_t a, int *bp, int *bq) {
    if (!VAOK || VA != a) { VOK[0] = VOK[1] = VOK[2] = VOK[3] = 0; VA = a; VAOK = 1; } float best = -1e30f; int Bp = 0, Bq = 0;
    for (int p = 0; p < NPAT; p++) {
        const uint8_t *pt = PAT[p]; int b123 = pt[1] + pt[2] + pt[3];
        for (int q = 0; q < 48; q++) {
            int v = b123 + (q <= 2); if (v > 3) v = 3;
            if (!VOK[v]) fb2variant(a, v);
            int c1; if (q <= 2) { int nb = 0; for (int m = 1; m <= q; m++) nb += pt[m]; c1 = r100v(jump(a, 21 + q + nb)); }
            /* walk frames 3..N-1: k = bolts on frames 4..n + coins on frames 3..n */
            float sc = INIT2[v]; int k = 0, from = 3, c2 = -1; if (q <= 2) c2 = c1 < 70 ? q + 24 : -1;
            for (int n = 3; n < N; n++) {
                int add = (n >= 4 ? pt[n] : 0) + (n == q && q >= 3) + (n == c2);
                if (add) { sc += G2[v][k][n] - G2[v][k][from]; k += add; if (k > KM) k = KM; from = n;
                    if (n == q && q >= 3) { int cv = r100v(jump(Y0[v], P0V[v][n] + k)); c2 = cv < 70 ? q + 24 : -1; } }
            }
            sc += G2[v][k][N] - G2[v][k][from];
            SC2[p * 48 + q] = sc; if (sc > best) { best = sc; Bp = p; Bq = q; }
        }
    }
    if (bp) *bp = Bp; if (bq) *bq = Bq; return best;
}
static int BPQ[2];
EXPORT("fb2best") float fb2best(uint32_t a) { return fb2full(a, &BPQ[0], &BPQ[1]); }
EXPORT("fb2bp") int fb2bp(int i) { return BPQ[i]; }
/* the same, skipped when even the best k on every frame (any insertion pattern) cannot reach thr: returns -1e30 then */
EXPORT("fb2cand") float fb2cand(uint32_t a, float thr2) {
    float ub2 = -1e30f; VA = a; VAOK = 1;
    for (int v = 0; v < 4; v++) { fb2variant(a, v); float u = INIT2[v];
        for (int n = 3; n < N; n++) { float m = -1e30f; for (int k = 0; k <= KM; k++) { float g = G2[v][k][n + 1] - G2[v][k][n]; if (g > m) m = g; } u += m; }
        if (u > ub2) ub2 = u; }
    if (ub2 <= thr2) return -1e30f;
    float r = fb2full(a, &BPQ[0], &BPQ[1]); return r;
}
/* the exact simulation of one hypothesis (pattern p, first coin q) from candidate a, to the start of frame `upto`:
 * END[0] = gRandSeed then, END[1] = the next coin frame (same frame numbers), END[2] = the score (check vs SC2) */
static uint32_t END[3];
EXPORT("endPtr") uint32_t *endPtr(void) { return END; }
EXPORT("fb2end") void fb2end(uint32_t a, int p, int q, int upto) {
    uint32_t s = (a - 1u) * 0x6A76AE6Du; Eff A, B; A.alive = B.alive = 0; int coin_next = q; float sc = 0;
    for (int n = 0; n < upto; n++) {
        if (n > 0 && n < NMAX) for (int k = 0; k < PAT[p][n]; k++) r359(&s);      /* frame 0's bolts came before a */
        if (n == 0) eff_init(&A, &s, 1.2f);
        if (n == 3) eff_init(&B, &s, 0.8f);
        if (n == coin_next) { int v = r100(&s); coin_next = n + (v >= 70 ? 48 : 24); }
        if (A.alive) eff_update(&A, &s);
        if (n >= 3 && B.alive) eff_update(&B, &s);
        r1(&s);
        if (n < N) sc += eff_score(&A, n) + (n >= 3 ? eff_score(&B, n) : 0);
    }
    END[0] = s; END[1] = (uint32_t)coin_next; union { float f; uint32_t u; } c; c.f = sc; END[2] = c.u;
}
EXPORT("setN") void setN(int n) { N = n; VAOK = 0; }
EXPORT("fb2npat") int fb2npat(void) { return NPAT; }
/* the upper bound fb2cand tests (any insertion pattern, the best k on every frame), for ordering the candidates */
EXPORT("fb2ub") float fb2ub(uint32_t a) {
    float ub2 = -1e30f; VA = a; VAOK = 1;
    for (int v = 0; v < 4; v++) { fb2variant(a, v); float u = INIT2[v];
        for (int n = 3; n < N; n++) { float m = -1e30f; for (int k = 0; k <= KM; k++) { float g = G2[v][k][n + 1] - G2[v][k][n]; if (g > m) m = g; } u += m; }
        if (u > ub2) ub2 = u; }
    return ub2;
}

/* ---- stage 2 with Bowser's star aura (Final Bowser phase 2, T1-T4; fb2_route/t14model.py) ----
 * The aura is an energy_in_out(4) effect in an effect slot before the Charge rays: on every frame its 16 stars draw
 * c[f mod 20] rand_int(359) after the coin and before the rays' respawns (c: the fight's 20-frame pattern, 16 per
 * period, drawn when phase 2 began; unknown to the page until a lock). With the lightning and the coin these are all
 * single LCG steps before frame n's respawns, so the score is again a sum of g_v[n][k_n], k_n = the extra draws on
 * frames 3..n (aura and coin on 3..n, bolts on 4..n), and B's creation offset v = the extra draws on frames 0..2 (coin,
 * aura) and the bolts on 1..3. fb1score: the best monotone path k_3 <= k_4 <= ... with per-frame steps 0..A_DMAX,
 * over every v (a relaxed score: any aura pattern, bolt pattern and coin; the page fits the structure from the path,
 * fb14_live.js). fb1path: that path for the best v. */
#define A_VMAX 14
#define A_KM 60
#define A_DMAX 6
static float AG[A_VMAX + 1][A_KM + 1][NMAX];   /* g_v[n][k] (not prefix sums) */
static float AINIT[A_VMAX + 1]; static int AOK[A_VMAX + 1]; static uint32_t AVA = 0xFFFFFFFFu;
static void fb1variant(uint32_t a, int v) {
    int sp[2][10], ph[2][10]; uint32_t s = a;
    for (int i = 0; i < 10; i++) { sp[0][i] = r10(&s); ph[0][i] = r10(&s); }
    uint32_t sb = jump(a, 24 + v); s = sb; AINIT[v] = initscore(0, a) + initscore(1, sb);
    for (int i = 0; i < 10; i++) { sp[1][i] = r10(&s); ph[1][i] = r10(&s); }
    static Ev ev[NMAX][24]; int ne[NMAX]; for (int n = 0; n < N; n++) ne[n] = 0;
    for (int e = 0; e < 2; e++) for (int i = 0; i < 10; i++) for (int n = (e ? 12 : 9) + ph[e][i]; n < (e ? 48 : 45) && n < N; n += 10)
        ev[n][ne[n]++] = (Ev){e, n, sp[e][i] + 4, (float)(1.0 - ((i + 1) % 3) * 0.3), e ? 0.8f : 1.2f};
    int P0[NMAX + 1], P = 0; for (int n = 3; n <= N; n++) { P0[n] = P; if (n < N) P += ne[n] + 1; }
    static uint32_t Y[NMAX * 26 + A_KM + 8]; int ny = P + A_KM + 4; Y[0] = s; for (int i = 1; i < ny; i++) Y[i] = adv(Y[i - 1]);
    for (int k = 0; k <= A_KM; k++) for (int n = 0; n < N; n++) { float g = 0;
        if (n >= 3) { int base = P0[n] + k;
            for (int j = 0; j < ne[n]; j++) { uint32_t y = Y[base + 1 + j]; uint32_t th = y / (0xFFFFFFFFu / 360); if (th > 359) th = 359; g += evscore(&ev[n][j], (int)th); } }
        AG[v][k][n] = g; }
    AOK[v] = 1;
}
static float ADP[NMAX][A_KM + 1]; static int8_t AFROM[NMAX][A_KM + 1]; static int APATH[NMAX], ABV = 0;
static float fb1dp(int v, int keep) {
    for (int k = 0; k <= A_KM; k++) ADP[3][k] = k <= A_DMAX ? AG[v][k][3] : -1e30f;
    for (int n = 4; n < N; n++) for (int k = 0; k <= A_KM; k++) {
        float b = -1e30f; int bd = 0; for (int d = 0; d <= A_DMAX && d <= k; d++) { float x = ADP[n - 1][k - d]; if (x > b) { b = x; bd = d; } }
        ADP[n][k] = b + AG[v][k][n]; AFROM[n][k] = (int8_t)bd; }
    int bk = 0; for (int k = 1; k <= A_KM; k++) if (ADP[N - 1][k] > ADP[N - 1][bk]) bk = k;
    if (keep) { int k = bk; for (int n = N - 1; n >= 3; n--) { APATH[n] = k; if (n > 3) k -= AFROM[n][k]; } }
    return AINIT[v] + ADP[N - 1][bk];
}
EXPORT("fb1score") float fb1score(uint32_t a) {
    if (AVA != a) { for (int v = 0; v <= A_VMAX; v++) AOK[v] = 0; AVA = a; }
    float best = -1e30f; for (int v = 0; v <= A_VMAX; v++) { if (!AOK[v]) fb1variant(a, v); float x = fb1dp(v, 0); if (x > best) { best = x; ABV = v; } }
    return best;
}
/* the best path of the last fb1score: APATH[3..N-1] = k_n, ABV = v */
EXPORT("fb1path") int *fb1path(uint32_t a) { fb1score(a); fb1dp(ABV, 1); APATH[0] = ABV; return APATH; }
/* the score of one structured hypothesis: k_n for n = 3..N-1 given in KH[], v = KH[0] */
static int KH[NMAX];
EXPORT("khPtr") int *khPtr(void) { return KH; }
EXPORT("fb1hyp") float fb1hyp(uint32_t a) {
    if (AVA != a) { for (int v = 0; v <= A_VMAX; v++) AOK[v] = 0; AVA = a; }
    int v = KH[0]; if (v < 0 || v > A_VMAX) return -1e30f; if (!AOK[v]) fb1variant(a, v);
    float sc = AINIT[v]; for (int n = 3; n < N; n++) { int k = KH[n]; if (k < 0 || k > A_KM) return -1e30f; sc += AG[v][k][n]; }
    return sc;
}
/* the end of a hypothesis: gRandSeed at the start of frame `upto` and the next coin frame, from a (after A's base draw),
 * given the extra draws per frame: XB[n] = bolts before the script on frame n, XC = the first coin frame (q), and the
 * aura counts XA[n] (after the coin); same order as the game (t14model.py). END[0..2] as fb2end. */
static uint8_t XB[NMAX + 8], XA[NMAX + 8];
EXPORT("xbPtr") uint8_t *xbPtr(void) { return XB; }
EXPORT("xaPtr") uint8_t *xaPtr(void) { return XA; }
EXPORT("fb1end") void fb1end(uint32_t a, int q, int upto) {
    uint32_t s = (a - 1u) * 0x6A76AE6Du; Eff A, B; A.alive = B.alive = 0; int coin_next = q; float sc = 0;
    for (int n = 0; n < upto; n++) {
        if (n > 0) for (int k = 0; k < XB[n]; k++) r359(&s);      /* frame 0's bolts came before a */
        if (n == 0) eff_init(&A, &s, 1.2f);
        if (n == 3) eff_init(&B, &s, 0.8f);
        if (n == coin_next) { int v = r100(&s); coin_next = n + (v >= 70 ? 48 : 24); }
        for (int k = 0; k < XA[n]; k++) r359(&s);
        if (A.alive) eff_update(&A, &s);
        if (n >= 3 && B.alive) eff_update(&B, &s);
        r1(&s);
        if (n < N) sc += eff_score(&A, n) + (n >= 3 ? eff_score(&B, n) : 0);
    }
    END[0] = s; END[1] = (uint32_t)coin_next; union { float f; uint32_t u; } c; c.f = sc; END[2] = c.u;
}
/* the structured fit after a lock: for candidate a and B-offset v (fb1path's), every lightning pattern p (setPatterns) x
 * first coin q (0..47) x second coin (q + 24 or none, for q < 24): the best aura pattern by dynamic programming over
 * the 20 residues j (frames j, j + 20, j + 40 share c_j; state = the prefix P_j = c_0 + .. + c_j, P_19 = 16, c_j <=
 * A_CMAX, P_2 set by v). Scores into SC3[(p * 48 + q) * 2 + branch] (-1e30: impossible); fb1aura(p, q, br) rebuilds
 * that best aura pattern into XA (20 counts by rays frame mod 20) and returns its score. */
#define A_CMAX 4
static float SC3[NPATMAX * 96]; static float TD[20][17]; static int8_t TF[20][17];
EXPORT("sc3Ptr") float *sc3Ptr(void) { return SC3; }
static int A3V = 0, LBc[NMAX], LP2 = 0;
static float lterm(int v, int j, int P) {
    float t = 0;
    for (int l = 0; l < 3; l++) { int n = j + 20 * l; if (n < 3 || n >= N) continue; int k = LBc[n] + 16 * l + P - LP2; if (k < 0 || k > A_KM) return -1e30f; t += AG[v][k][n]; }
    return t;
}
static float fb1lanes(int v, const uint8_t *pt, int q, int br, int keep) {
    /* Bc[n]: bolts on 4..n + coins on 3..n; the coins at q and (br) q + 24; P_2 = v - coins(0..2) - bolts(1..3) */
    int *Bc = LBc, acc = 0, c0 = 0, b13 = pt[1] + pt[2] + pt[3];
    int c2 = br ? q + 24 : -1; if (q <= 2) c0++; if (c2 >= 0 && c2 <= 2) c0++;
    int P2 = v - c0 - b13; if (P2 < 0 || P2 > 3 * A_CMAX) return -1e30f; LP2 = P2;
    for (int n = 3; n < N; n++) { acc += (n >= 4 ? pt[n] : 0) + (n == q) + (n == c2); Bc[n] = acc; }
    for (int j = 0; j < 20; j++) for (int P = 0; P <= 16; P++) {
        float t = 0; int ok = 1;
        for (int l = 0; l < 3; l++) { int n = j + 20 * l; if (n < 3 || n >= N) continue; int k = Bc[n] + 16 * l + P - P2; if (k < 0 || k > A_KM) { ok = 0; break; } t += AG[v][k][n]; }
        float b = -1e30f; int bc = 0;
        if (ok) { if (j == 0) { if (P <= A_CMAX) b = 0, bc = P; }
                  else for (int c = 0; c <= A_CMAX && c <= P; c++) { float x = TD[j - 1][P - c]; if (x > b) { b = x; bc = c; } } }
        if (j == 2 && P != P2) b = -1e30f;
        TD[j][P] = b > -1e29f ? b + t : -1e30f; TF[j][P] = (int8_t)bc; }
    float r = TD[19][16];
    if (keep && r > -1e29f) { int P = 16; for (int j = 19; j >= 0; j--) { int c = TF[j][P]; XA[j] = (uint8_t)c; P -= c; } }
    return r > -1e29f ? AINIT[v] + r : -1e30f;
}
EXPORT("fb1struct") float fb1struct(uint32_t a, int v) {
    if (AVA != a) { for (int w = 0; w <= A_VMAX; w++) AOK[w] = 0; AVA = a; }
    if (!AOK[v]) fb1variant(a, v); A3V = v; float best = -1e30f;
    for (int p = 0; p < NPAT; p++) for (int q = 0; q < 48; q++) for (int br = 0; br < 2; br++) {
        float x = (br && q >= 24) ? -1e30f : fb1lanes(v, PAT[p], q, br, 0);
        SC3[(p * 48 + q) * 2 + br] = x; if (x > best) best = x; }
    return best;
}
EXPORT("fb1aura") float fb1aura(int p, int q, int br) { return fb1lanes(A3V, PAT[p], q, br, 1); }
/* fb1score over v in [vlo, vhi] only (the joint stage's best B offset for the candidate, +-1) */
EXPORT("fb1scorev") float fb1scorev(uint32_t a, int vlo, int vhi) {
    if (AVA != a) { for (int v = 0; v <= A_VMAX; v++) AOK[v] = 0; AVA = a; }
    if (vlo < 0) vlo = 0; if (vhi > A_VMAX) vhi = A_VMAX;
    float best = -1e30f; for (int v = vlo; v <= vhi; v++) { if (!AOK[v]) fb1variant(a, v); float x = fb1dp(v, 0); if (x > best) { best = x; ABV = v; } }
    return best;
}

/* every aura pattern of hypothesis (p, q, br) whose score is within tol of that hypothesis' best (the rays' faded and
 * offscreen respawns leave neighbouring residues' split open): up to max patterns into ALTS (20 counts each, rays frame
 * mod 20), by depth-first search on the dynamic programme's table with its best-prefix bound */
static uint8_t ALTS[4096 * 20]; static float ALTSC[4096]; static int NALT, ALTMAX; static uint8_t CUR[20]; static float ABEST, ATOL;
EXPORT("altPtr") uint8_t *altPtr(void) { return ALTS; }
EXPORT("altScPtr") float *altScPtr(void) { return ALTSC; }
static void altdfs(int j, int P, float suffix) {
    if (NALT >= ALTMAX) return;
    float t = lterm(A3V, j, P); if (t < -1e29f) return; suffix += t;
    if (j == 0) { if (P > A_CMAX) return; if (suffix < ABEST - ATOL) return; CUR[0] = (uint8_t)P; for (int i = 0; i < 20; i++) ALTS[NALT * 20 + i] = CUR[i]; ALTSC[NALT] = AINIT[A3V] + suffix; NALT++; return; }
    for (int c = 0; c <= A_CMAX && c <= P; c++) { int Pp = P - c; float b = TD[j - 1][Pp]; if (b < -1e29f || b + suffix < ABEST - ATOL) continue; CUR[j] = (uint8_t)c; altdfs(j - 1, Pp, suffix); }
}
EXPORT("fb1alts") int fb1alts(int p, int q, int br, float tol, int max) {
    float r = fb1lanes(A3V, PAT[p], q, br, 0); if (r < -1e29f) return 0;
    ABEST = TD[19][16]; ATOL = tol; NALT = 0; ALTMAX = max > 4096 ? 4096 : max; altdfs(19, 16, 0); return NALT;
}
/* the score of a given aura pattern (XA[0..19], by rays frame mod 20) for candidate a with lightning pattern p, first
 * coin q and second coin br: the rays of several Charges together tell the fight's one pattern apart where one Charge's
 * respawns do not (fb14_live.js fb14Joint) */
EXPORT("fb1cscore") float fb1cscore(uint32_t a, int p, int q, int br) {
    if (AVA != a) { for (int w = 0; w <= A_VMAX; w++) AOK[w] = 0; AVA = a; }
    const uint8_t *pt = PAT[p]; int c2 = br ? q + 24 : -1, P[20], acc = 0;
    for (int j = 0; j < 20; j++) { acc += XA[j]; P[j] = acc; }
    if (acc != 16) return -1e30f;
    int v = (q <= 2) + (c2 >= 0 && c2 <= 2) + pt[1] + pt[2] + pt[3] + P[2]; if (v > A_VMAX) return -1e30f;
    if (!AOK[v]) fb1variant(a, v);
    float sc = AINIT[v]; int Bc = 0;
    for (int n = 3; n < N; n++) { Bc += (n >= 4 ? pt[n] : 0) + (n == q) + (n == c2); int k = Bc + 16 * (n / 20) + P[n % 20] - P[2]; if (k < 0 || k > A_KM) return -1e30f; sc += AG[v][k][n]; }
    return sc;
}
