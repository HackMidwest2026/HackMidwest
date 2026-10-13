/*
* host test for the kz-lite state compressor (kz/src/state_lz.c).
*
* compresses thousands of chunks of mixed data into a stream made of small,
* randomly sized blocks (so tokens are split across block boundaries), reads
* it back the same way, and checks the round trip.  also checks that running
* out of blocks fails cleanly without writing past the last block.
*
* usage: lztest [file...]   files are also round tripped and their ratio printed
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state_lz.h"

static unsigned rnd_state = 12345;
static unsigned rnd(void) { rnd_state = rnd_state * 1103515245 + 12345; return rnd_state >> 8; }

#define GUARD 16

/* output: a list of blocks of random size, with guard bytes after each */
typedef struct {
    unsigned char **blocks;
    size_t         *sizes;      /* bytes used */
    size_t         *alloc;      /* bytes allocated, guard bytes follow */
    size_t          cnt, max_cnt, max_block, budget;
} blocks_t;

static int out_next(lz_stream_t *s) {
    blocks_t *b = s->data;
    if (b->cnt > 0) b->sizes[b->cnt - 1] = s->p - b->blocks[b->cnt - 1];
    if (b->cnt == b->max_cnt) return 0;
    size_t size = 1 + rnd() % b->max_block;
    if (size > b->budget) size = b->budget;
    if (size == 0) return 0;
    b->budget -= size;
    unsigned char *blk = malloc(size + GUARD);
    memset(blk + size, 0xAA, GUARD);
    b->blocks[b->cnt] = blk;
    b->sizes[b->cnt] = size;
    b->alloc[b->cnt] = size;
    b->cnt++;
    s->p = blk;
    s->end = blk + size;
    return 1;
}

typedef struct { blocks_t *b; size_t idx; } reader_t;

static int in_next(lz_stream_t *s) {
    reader_t *r = s->data;
    r->idx++;
    if (r->idx >= r->b->cnt) { printf("READ PAST END\n"); exit(1); }
    s->p = r->b->blocks[r->idx];
    s->end = s->p + r->b->sizes[r->idx];
    return 1;
}

static void blocks_free(blocks_t *b) {
    for (size_t i = 0; i < b->cnt; i++) free(b->blocks[i]);
    free(b->blocks); free(b->sizes); free(b->alloc);
}

static blocks_t blocks_new(size_t max_cnt, size_t max_block, size_t budget) {
    blocks_t b = { calloc(max_cnt, sizeof(void*)), calloc(max_cnt, sizeof(size_t)), calloc(max_cnt, sizeof(size_t)),
                   0, max_cnt, max_block, budget };
    return b;
}

static int guards_intact(blocks_t *b) {
    for (size_t i = 0; i < b->cnt; i++)
        for (int g = 0; g < GUARD; g++)
            if (b->blocks[i][b->alloc[i] + g] != 0xAA) return 0;
    return 1;
}

int main(int argc, char **argv) {
    static lz_hash_t hash[LZ_HASH_SIZE];
    size_t nchunks = 4000, total = 0;
    unsigned char **chunks = malloc(nchunks * sizeof(*chunks));
    size_t *lens = malloc(nchunks * sizeof(*lens));

    /* chunks of various kinds and sizes, including 0..3 byte chunks */
    for (size_t i = 0; i < nchunks; i++) {
        size_t len = (i % 7 == 0) ? rnd() % 200000 : rnd() % 64;
        if (i % 11 == 0) len = rnd() % 4;
        unsigned char *c = malloc(len + 1);
        int kind = rnd() % 4;
        for (size_t j = 0; j < len; j++) {
            switch (kind) {
                case 0: c[j] = 0; break;
                case 1: c[j] = rnd(); break;
                case 2: c[j] = (j % 16 < 4) ? 0x80 : (j % 16 < 8 ? (rnd() & 3) : 0); break; /* struct-like */
                default: c[j] = (rnd() % 10 < 7) ? 0 : rnd(); break;
            }
        }
        if (len > 1000 && kind == 1) memcpy(c + len / 2, c, len / 4); /* far repeats */
        chunks[i] = c; lens[i] = len; total += len;
    }

    for (int max_block = 1; max_block <= 4096; max_block *= 8) {
        blocks_t b = blocks_new(total * 2 + 1024, max_block, (size_t)-1);
        lz_stream_t out = { NULL, NULL, out_next, &b };
        for (size_t i = 0; i < nchunks; i++) {
            if (!lz_compress(&out, chunks[i], lens[i], hash)) { printf("unexpected overflow\n"); return 1; }
        }
        b.sizes[b.cnt - 1] = out.p - b.blocks[b.cnt - 1];
        if (!guards_intact(&b)) { printf("wrote past a block (blocks <= %d)\n", max_block); return 1; }
        size_t comp = 0;
        for (size_t i = 0; i < b.cnt; i++) comp += b.sizes[i];

        reader_t r = { &b, 0 };
        lz_stream_t in = { b.blocks[0], b.blocks[0] + b.sizes[0], in_next, &r };
        for (size_t i = 0; i < nchunks; i++) {
            unsigned char *d = malloc(lens[i] + 1);
            lz_decompress(&in, d, lens[i]);
            if (memcmp(d, chunks[i], lens[i])) { printf("MISMATCH chunk %zu len %zu (blocks <= %d)\n", i, lens[i], max_block); return 1; }
            free(d);
        }
        if (r.idx != b.cnt - 1 || in.p != in.end) { printf("stream length mismatch (blocks <= %d)\n", max_block); return 1; }
        printf("roundtrip ok, blocks of 1-%d bytes: %zu -> %zu bytes (%.1f%%) in %zu blocks\n",
               max_block, total, comp, 100.0 * comp / total, b.cnt);
        blocks_free(&b);
    }

    /* running out of space must fail cleanly, without writing past any block */
    for (size_t budget = 0; budget < 6000; budget += 37) {
        blocks_t b = blocks_new(100000, 300, budget);
        lz_stream_t out = { NULL, NULL, out_next, &b };
        int ok = 1;
        for (size_t i = 0; i < nchunks && ok; i++) ok = lz_compress(&out, chunks[i], lens[i], hash);
        if (ok) { printf("expected failure with budget %zu\n", budget); return 1; }
        if (!guards_intact(&b)) { printf("wrote past a block with budget %zu\n", budget); return 1; }
        blocks_free(&b);
    }
    printf("overflow checks ok\n");

    for (int a = 1; a < argc; a++) {
        FILE *f = fopen(argv[a], "rb"); if (!f) continue;
        fseek(f, 0, SEEK_END); long n = ftell(f); rewind(f);
        unsigned char *buf = malloc(n);
        if (fread(buf, 1, n, f) != (size_t)n) { fclose(f); continue; }
        fclose(f);
        blocks_t b = blocks_new(n + 1024, 512, (size_t)-1);
        lz_stream_t out = { NULL, NULL, out_next, &b };
        lz_compress(&out, buf, n, hash);
        b.sizes[b.cnt - 1] = out.p - b.blocks[b.cnt - 1];
        size_t comp = 0;
        for (size_t i = 0; i < b.cnt; i++) comp += b.sizes[i];
        reader_t r = { &b, 0 };
        lz_stream_t in = { b.blocks[0], b.blocks[0] + b.sizes[0], in_next, &r };
        unsigned char *d = malloc(n);
        lz_decompress(&in, d, n);
        printf("%s: %ld -> %zu (%.1f%%) %s\n", argv[a], n, comp, 100.0 * comp / n, memcmp(buf, d, n) ? "MISMATCH" : "ok");
        blocks_free(&b);
    }
    return 0;
}
