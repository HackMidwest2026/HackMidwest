#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state_lz.h"
static unsigned rnd(void){ static unsigned s=12345; s=s*1103515245+12345; return s>>8; }
int main(int argc, char **argv){
    static lz_hash_t hash[LZ_HASH_SIZE];
    size_t nchunks = 4000, total = 0, comp = 0;
    unsigned char **chunks = malloc(nchunks * sizeof(*chunks)); size_t *lens = malloc(nchunks*sizeof(size_t));
    /* chunks of various kinds and sizes, including 0..3 byte chunks */
    for(size_t i=0;i<nchunks;i++){
        size_t len = (i%7==0) ? rnd()%200000 : rnd()%64;
        if(i%11==0) len = rnd()%4;
        unsigned char *c = malloc(len+1);
        int kind = rnd()%4;
        for(size_t j=0;j<len;j++){
            switch(kind){
            case 0: c[j]=0; break;
            case 1: c[j]=rnd(); break;
            case 2: c[j]=(j%16<4)?0x80:(j%16<8?(rnd()&3):0); break; /* struct-like */
            default: c[j]= (rnd()%10<7)?0:rnd(); break;
            }
        }
        if(len>1000 && kind==1) memcpy(c+len/2, c, len/4); /* far repeats */
        chunks[i]=c; lens[i]=len; total+=len;
    }
    size_t cap = total + total/64 + nchunks*4 + 16;
    unsigned char *out = malloc(cap), *p = out;
    for(size_t i=0;i<nchunks;i++){ p = lz_compress(p, out+cap, chunks[i], lens[i], hash); if(!p){printf("overflow\n");return 1;} }
    comp = p - out;
    const unsigned char *q = out;
    for(size_t i=0;i<nchunks;i++){
        unsigned char *d = malloc(lens[i]+1);
        q = lz_decompress(q, d, lens[i]);
        if(memcmp(d, chunks[i], lens[i])){ printf("MISMATCH chunk %zu len %zu\n", i, lens[i]); return 1; }
        free(d);
    }
    if(q != p){ printf("stream length mismatch\n"); return 1; }
    printf("roundtrip ok: %zu -> %zu bytes (%.1f%%)\n", total, comp, 100.0*comp/total);
    /* overflow handling: every truncated buffer must fail cleanly without writing past the end */
    for(size_t lim=0; lim<comp && lim < 5000; lim+=7){
        unsigned char *o = malloc(lim+64); memset(o+lim, 0xAA, 64);
        unsigned char *r = o; memset(hash,0,sizeof(hash));
        for(size_t i=0;i<nchunks && r;i++) r = lz_compress(r, o+lim, chunks[i], lens[i], hash);
        for(int k=0;k<64;k++) if(o[lim+k]!=0xAA){ printf("wrote past end at lim %zu\n", lim); return 1; }
        if(r){ printf("expected overflow at lim %zu\n", lim); return 1; }
        free(o);
    }
    printf("overflow checks ok\n");
    /* file input: compress whole files as a single chunk */
    for(int a=1;a<argc;a++){
        FILE *f=fopen(argv[a],"rb"); if(!f) continue; fseek(f,0,SEEK_END); long n=ftell(f); rewind(f);
        unsigned char *b=malloc(n); fread(b,1,n,f); fclose(f);
        unsigned char *o=malloc(n+n/64+64); unsigned char *e=lz_compress(o,o+n+n/64+64,b,n,hash);
        unsigned char *d=malloc(n); lz_decompress(o,d,n);
        printf("%s: %ld -> %ld (%.1f%%) %s\n", argv[a], n, (long)(e-o), 100.0*(e-o)/n, memcmp(b,d,n)?"MISMATCH":"ok");
    }
    return 0;
}
