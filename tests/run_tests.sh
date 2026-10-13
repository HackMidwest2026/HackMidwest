#!/bin/sh
# Host-side tests for the kz-lite save state support.
#   lztest  - round trips the state compressor over thousands of mixed chunks,
#             and checks that a too-small output buffer fails without overrunning it.
#   memtest - random malloc/free/realloc workload against kz-lite's allocator,
#             including the "grab the largest block, then shrink it" pattern used
#             when saving a state.  Checks block contents and that all memory is
#             recovered at the end.
#   statetest - lite state memory on a fragmented kz-lite heap: states split
#             into chunks, export/import round trips, out of memory and
#             truncated files, and that all memory is given back.
set -e
here=$(cd "$(dirname "$0")" && pwd)
kz="$here/../kz"
out="${TMPDIR:-/tmp}/kz-lite-tests"
mkdir -p "$out"

gcc -O2 -Wall -Wno-unused-result -DLITE -I"$kz/include" -o "$out/lztest" "$here/lztest.c" "$kz/src/state_lz.c"
"$out/lztest" "$kz/src/state.c"

python3 "$here/make_memt.py" "$kz/src/mem.c" "$out/memt.c"
gcc -O1 -g -w -DLITE -include stddef.h -fsanitize=address -I"$out" -o "$out/memtest" "$here/memtest.c"
"$out/memtest"

# state memory: chunks, export/import, on the kz-lite allocator
# (mem.h includes an n64 toolchain header that this test does not need)
mkdir -p "$out/vector" && : > "$out/vector/vector.h"
gcc -O1 -g -w -DLITE -include stddef.h -fsanitize=address -I"$out" -I"$kz/include" \
    -Dmalloc=t_malloc -Dfree=t_free -Drealloc=t_realloc -Dcalloc=t_calloc -Dmemalign=t_memalign \
    -o "$out/statetest" "$here/statetest.c" "$kz/src/state_chunk.c" "$kz/src/state_lz.c"
"$out/statetest"
echo "all tests passed"
