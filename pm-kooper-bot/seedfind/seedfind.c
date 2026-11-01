/* Paper Mario (JP) coin seed finder.
 * Input: the status-bar coin pattern, one character per coin draw in order: 'S' = shine (draw 70+), '.' = normal spin.
 * Model (measured): a coin draw is one rand_int(100) = internal(1009)/10; shine iff the advanced seed >= 700*4252443.
 * After a normal spin the next draw comes 24 seed steps later, after a shine 48 (one step per frame, 24-frame loops).
 * Output: every seed (value just before the first observed draw) that reproduces the whole pattern.
 * usage: seedfind PATTERN [threads]   build: gcc -O3 -pthread -o seedfind seedfind.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#define MUL 0x5D588B65u
#define SHINE_MIN (700u * 4252443u)
static const char *pat; static int plen, nthreads;
static uint32_t a24, c24, a48, c48;
static pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;
static uint32_t found[64]; static int nfound;
static void compose(int n, uint32_t *a, uint32_t *c) { uint32_t A = 1, C = 0; for (int i = 0; i < n; i++) { A *= MUL; C = C * MUL + 1; } *a = A; *c = C; }
static void *work(void *arg) {
    uint64_t t = (uint64_t)(uintptr_t)arg;
    for (uint64_t s = t; s < (1ull << 32); s += nthreads) {
        uint32_t x = (uint32_t)s; int i;
        for (i = 0; i < plen; i++) {
            x = x * MUL + 1;                              /* the coin draw */
            int shine = x >= SHINE_MIN;
            if (shine != (pat[i] == 'S')) break;
            if (shine) x = x * a48 + c48; else x = x * a24 + c24;
        }
        if (i == plen) { pthread_mutex_lock(&mtx); if (nfound < 64) found[nfound] = (uint32_t)s; nfound++; pthread_mutex_unlock(&mtx); }
    }
    return NULL;
}
int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: seedfind PATTERN [threads]\n"); return 1; }
    pat = argv[1]; plen = strlen(pat); nthreads = argc > 2 ? atoi(argv[2]) : 4;
    compose(24, &a24, &c24); compose(48, &a48, &c48);
    pthread_t th[64];
    for (int i = 0; i < nthreads; i++) pthread_create(&th[i], NULL, work, (void *)(uintptr_t)i);
    for (int i = 0; i < nthreads; i++) pthread_join(th[i], NULL);
    printf("%d seed(s)\n", nfound);
    for (int i = 0; i < nfound && i < 64; i++) printf("%08x\n", found[i]);
    return 0;
}
