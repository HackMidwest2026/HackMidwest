#!/usr/bin/env python3
"""Turn kz/src/mem.c into a host-testable allocator (memt.c).

The kz-lite heaps live at fixed n64 addresses, so they are swapped for static
buffers, and the allocator functions get a t_ prefix so they don't replace
the host's libc allocator.
"""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
reps = [
    ('{ (void*)0x80700000, 0x80000 }, // actor heap end', '{ (void*)heap0_buf, sizeof(heap0_buf) },'),
    ('{ (void*)&end, 0x80080000 },', '{ (void*)heap1_buf, 0 },'),
    ('hdr->size = heap_heads[HEAP_CNT - 1].size - (uint32_t)hdr - HDR_SIZE;', 'hdr->size = sizeof(heap1_buf) - HDR_SIZE;'),
    ('extern char end;\nvoid *sbrk(int size);',
     'static _Alignas(16) char heap0_buf[0x80000];\nstatic _Alignas(16) char heap1_buf[0x20000];\n'
     'static char *brk_p = heap1_buf;\nstatic void *sbrk(int size){ void *r = brk_p; brk_p += size; return r; }'),
    ('(uint32_t)blk + HDR_SIZE', '(uintptr_t)blk + HDR_SIZE'),
    ('uint32_t blk_addr', 'uintptr_t blk_addr'),
    ('uint32_t align_pad', 'uintptr_t align_pad'),
]
for old, new in reps:
    if old not in s:
        sys.exit('mem.c changed, could not find: ' + old)
    s = s.replace(old, new)
s = re.sub(r'\b(malloc|free|realloc|calloc|memalign)\(', r't_\1(', s)
open(dst, 'w').write(s)
