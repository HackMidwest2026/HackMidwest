#!/bin/sh
# Host-side tests for the kz-lite save state support.
#   lztest  - round trips the state compressor over thousands of mixed chunks,
#             and checks that a too-small output buffer fails without overrunning it.
#   memtest - random malloc/free/realloc workload against kz-lite's allocator,
#             including the "grab the largest block, then shrink it" pattern used
#             when saving a state.  Checks block contents and that all memory is
#             recovered at the end.
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
echo "all tests passed"
