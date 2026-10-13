/*
* host test for kz-lite state memory (kz/src/state_chunk.c) on top of kz-lite's
* own allocator (kz/src/mem.c, made host-runnable by make_memt.py), with the
* state compressor (kz/src/state_lz.c).
*
* the heap is fragmented first, so states have to be split across chunks.
* checks, over many random rounds:
*   - saving: data compressed into chunks decompresses back to the original
*   - export/import: state_write_file -> state_read_file gives identical bytes
*   - a state that does not fit fails cleanly, and frees what it allocated
*   - freeing everything gives all memory back
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "memt.c"
#include "state.h"
#include "state_chunk.h"

/* state_chunk.c is built with malloc/free mapped to the kz-lite test heap.
 * the test's own buffers come from the host allocator. */
#undef malloc
#undef free

static unsigned rs = 7;
static unsigned rnd(void) { rs = rs * 1103515245 + 12345; return rs >> 8; }

/* game-like data: mostly zeros and small repeating structures */
static void fill(unsigned char *p, size_t n) {
    for (size_t i = 0; i < n; i++) {
        int k = (i / 512) % 4;
        p[i] = k == 0 ? 0 : k == 1 ? (unsigned char)(i * 7) : k == 2 ? (rnd() % 8 == 0 ? rnd() : 0) : (unsigned char)rnd();
    }
}

/* a save: header + compressed data, the way save_state_alloc builds it */
static kz_state_hdr_t *save(const unsigned char *data, size_t n) {
    static lz_hash_t hash[LZ_HASH_SIZE];
    chunk_alloc_t alloc;
    if (!chunk_alloc_init(&alloc)) return NULL;
    state_chunk_t *first = chunk_new(&alloc, 0);
    if (!first) return NULL;
    memset(hash, 0, sizeof(hash));
    lz_stream_t out;
    kz_state_hdr_t *hdr = (kz_state_hdr_t *)first->data;
    chunk_out_open(&out, &alloc, sizeof(*hdr));
    /* write it in pieces, like save_state does */
    for (size_t off = 0; off < n;) {
        size_t len = 1 + rnd() % 30000;
        if (len > n - off) len = n - off;
        if (!lz_compress(&out, data + off, len, hash)) { chunks_free(alloc.first); return NULL; }
        off += len;
    }
    hdr->size = chunk_out_close(&out, &alloc);
    hdr->z2_version = 2;
    hdr->state_version = STATE_HDR_VERSION;
    strcpy(hdr->name, "test");
    return hdr;
}

static int check_load(kz_state_hdr_t *hdr, const unsigned char *data, size_t n) {
    unsigned char *out = malloc(n);
    lz_stream_t in;
    state_stream_open(&in, hdr, (char *)hdr + sizeof(*hdr));
    lz_decompress(&in, out, n);
    int ok = memcmp(out, data, n) == 0;
    free(out);
    return ok;
}

struct buf { unsigned char *p; size_t len, pos; };
static int buf_write(void *ctx, const void *b, size_t len) {
    struct buf *f = ctx; memcpy(f->p + f->len, b, len); f->len += len; return 1;
}
static int buf_read(void *ctx, void *b, size_t len) {
    struct buf *f = ctx;
    if (f->pos + len > f->len) return 0;
    memcpy(b, f->p + f->pos, len); f->pos += len; return 1;
}

static size_t chunk_count(kz_state_hdr_t *hdr) {
    size_t c = 0;
    for (state_chunk_t *ch = STATE_CHUNK(hdr); ch; ch = ch->next) c++;
    return c;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    size_t total0;
    mem_largest_free(&total0);

    /* fragment the heap: allocate lots, free every other one */
    void *frag[400];
    for (int i = 0; i < 400; i++) frag[i] = t_malloc(64 + rnd() % 1500);
    for (int i = 0; i < 400; i += 2) { t_free(frag[i]); frag[i] = NULL; }
    size_t total1, largest1 = mem_largest_free(&total1);
    printf("fragmented heap: %zu free, largest block %zu\n", total1, largest1);

    size_t max_chunks = 0, saves = 0, imports = 0, nomem = 0;
    for (int round = 0; round < 300; round++) {
        size_t n = 1000 + rnd() % 600000;
        unsigned char *data = malloc(n);   /* host memory, not the test heap */
        fill(data, n);

        kz_state_hdr_t *a = save(data, n);
        if (!a) { nomem++; free(data); continue; }
        saves++;
        if (!check_load(a, data, n)) { printf("MISMATCH after save, round %d\n", round); return 1; }
        if (chunk_count(a) > max_chunks) max_chunks = chunk_count(a);

        /* export, then import into a second state while the first is still held */
        struct buf f = { malloc(a->size), 0, 0 };
        if (!state_write_file(a, buf_write, &f) || f.len != a->size) { printf("export size mismatch\n"); return 1; }
        kz_state_hdr_t hdr;
        buf_read(&f, &hdr, sizeof(hdr));
        int err;
        size_t free_before;
        mem_largest_free(&free_before);
        /* chunks need not be contiguous, so this much free memory must be enough */
        int must_fit = free_before > STATE_MEM_RESERVE + hdr.size + 0x2000;
        kz_state_hdr_t *b = state_read_file(&hdr, buf_read, &f, &err);
        if (!b && must_fit) {
            printf("import ran out of memory with %zu free for a %u byte state, round %d\n", free_before, (unsigned)hdr.size, round);
            return 1;
        }
        if (b) {
            imports++;
            if (!check_load(b, data, n)) { printf("MISMATCH after import, round %d\n", round); return 1; }
            struct buf g = { malloc(b->size), 0, 0 };
            state_write_file(b, buf_write, &g);
            if (g.len != f.len || memcmp(g.p, f.p, f.len)) { printf("re-export differs, round %d\n", round); return 1; }
            free(g.p);
            state_free(b);
        } else if (err != STATE_READ_MEMORY) {
            printf("import failed with error %d, round %d\n", err, round); return 1;
        }

        /* a truncated file must fail with an io error and leak nothing */
        size_t before; mem_largest_free(&before);
        struct buf t = { f.p, f.len / 2, sizeof(hdr) };
        kz_state_hdr_t *c = state_read_file(&hdr, buf_read, &t, &err);
        size_t after; mem_largest_free(&after);
        if (c || (err != STATE_READ_IO && err != STATE_READ_MEMORY) || after != before) {
            printf("truncated import not handled, round %d (err %d, leak %zd)\n", round, err, (ssize_t)(before - after)); return 1;
        }

        free(f.p);
        state_free(a);
        free(data);
    }

    for (int i = 1; i < 400; i += 2) t_free(frag[i]);
    size_t total2, largest2 = mem_largest_free(&total2);
    printf("%zu saves, %zu imports, %zu too big for memory, up to %zu chunks per state\n", saves, imports, nomem, max_chunks);
    if (total2 != total0) { printf("LEAK: %zu free at start, %zu at end\n", total0, total2); return 1; }
    if (saves == 0 || imports == 0 || max_chunks < 2) { printf("test did not exercise chunking\n"); return 1; }
    printf("all memory returned (%zu free, largest %zu)\n", total2, largest2);
    return 0;
}
