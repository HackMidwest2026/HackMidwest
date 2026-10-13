/*
* host test for kz's macro storage and file format (kz/src/macro_store.c).
*
* records random input across many pages with overwrites, trims and seeds,
* keeping a plain array as the reference, then checks:
*   - every frame and seed reads back as recorded
*   - write -> read round trips exactly, and the file size matches
*   - bad magic, wrong version, wrong mm version and truncated files are rejected
*   - a failed read leaves the store empty
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "macro_store.h"

static unsigned rs = 3;
static unsigned rnd(void) { rs = rs * 1103515245 + 12345; return rs >> 8; }

struct buf { unsigned char *p; size_t len, pos, cap; };
static int buf_write(void *ctx, const void *b, size_t len) {
    struct buf *f = ctx;
    if (f->len + len > f->cap) { f->cap = (f->len + len) * 2; f->p = realloc(f->p, f->cap); }
    memcpy(f->p + f->len, b, len); f->len += len; return 1;
}
static int buf_read(void *ctx, void *b, size_t len) {
    struct buf *f = ctx;
    if (f->pos + len > f->len) return 0;
    memcpy(b, f->p + f->pos, len); f->pos += len; return 1;
}

static int same_input(const macro_input_t *a, const macro_input_t *b) {
    return a->pad == b->pad && a->pressed == b->pressed && a->released == b->released &&
           a->x == b->x && a->y == b->y && a->adjusted_x == b->adjusted_x && a->adjusted_y == b->adjusted_y;
}

static int check(macro_store_t *s, macro_input_t *ref, uint32_t len, uint32_t *seed_ref, int *has_seed) {
    if (s->length != len) { printf("length %u != %u\n", s->length, len); return 0; }
    for (uint32_t f = 0; f < len; f++) {
        macro_input_t *in = macro_store_get(s, f);
        if (!in || !same_input(in, &ref[f])) { printf("frame %u differs\n", f); return 0; }
        uint32_t seed;
        int got = macro_store_get_seed(s, f, &seed);
        if (got != has_seed[f] || (got && seed != seed_ref[f])) { printf("seed at %u differs\n", f); return 0; }
    }
    if (macro_store_get(s, len) != NULL) { printf("frame past the end readable\n"); return 0; }
    return 1;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    enum { MAX = 5000 };
    static macro_input_t ref[MAX];
    static uint32_t seed_ref[MAX];
    static int has_seed[MAX];
    macro_store_t s;
    macro_store_init(&s);
    uint32_t len = 0;

    for (int round = 0; round < 200; round++) {
        /* record a stretch from some frame, like rerecording after loading a state */
        uint32_t start = len ? rnd() % (len + 1) : 0;
        uint32_t n = rnd() % 700;
        for (uint32_t f = start; f < start + n && f < MAX; f++) {
            macro_input_t in = { rnd(), rnd(), rnd(), rnd(), rnd(), rnd(), rnd() };
            if (!macro_store_set(&s, f, &in)) { printf("set failed\n"); return 1; }
            ref[f] = in;
            if (f >= len) { len = f + 1; has_seed[f] = 0; }
            if (rnd() % 97 == 0) {
                uint32_t seed = rnd();
                macro_store_set_seed(&s, f, seed);
                seed_ref[f] = seed; has_seed[f] = 1;
            }
        }
        if (macro_store_set(&s, len + 1, &ref[0])) { printf("set past the end accepted\n"); return 1; }
        if (rnd() % 5 == 0) {
            uint32_t t = len ? rnd() % len : 0;
            macro_store_trim(&s, t);
            for (uint32_t f = t; f < len; f++) has_seed[f] = 0;
            len = t;
        }
        if (!check(&s, ref, len, seed_ref, has_seed)) { printf("round %d\n", round); return 1; }

        /* file round trip */
        struct buf f = { 0 };
        if (!macro_store_write(&s, 2, buf_write, &f) || f.len != macro_store_size(&s)) { printf("write size\n"); return 1; }
        macro_store_t r;
        macro_store_init(&r);
        if (macro_store_read(&r, 2, f.len, buf_read, &f) != 0 || !check(&r, ref, len, seed_ref, has_seed)) {
            printf("read back differs, round %d\n", round); return 1;
        }

        /* rejected files leave the store empty */
        struct buf g = { f.p, f.len, 0, f.cap };
        if (macro_store_read(&r, 3, g.len, buf_read, &g) != MACRO_READ_VERSION || r.length) { printf("wrong mm version accepted\n"); return 1; }
        g.pos = 0;
        if (macro_store_read(&r, 2, g.len - 1, buf_read, &g) != MACRO_READ_FORMAT || r.length) { printf("wrong size accepted\n"); return 1; }
        g.pos = 0; g.len = f.len / 2;
        int e = macro_store_read(&r, 2, f.len, buf_read, &g);
        if ((e != MACRO_READ_IO && e != MACRO_READ_FORMAT) || r.length) { printf("truncated file accepted (%d)\n", e); return 1; }
        g.pos = 0; g.len = f.len; f.p[0] ^= 0xFF;
        if (macro_store_read(&r, 2, g.len, buf_read, &g) != MACRO_READ_FORMAT || r.length) { printf("bad magic accepted\n"); return 1; }
        macro_store_clear(&r);
        free(f.p);
    }

    printf("macro store ok: %u frames, %u seeds, %u pages at the end\n", s.length, s.seed_cnt, s.page_cnt);
    macro_store_clear(&s);
    return 0;
}
