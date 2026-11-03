#!/bin/bash
# Compile kernel.c to WebAssembly for the page's search workers; build_page.py inlines kernel.wasm.b64.
# Needs clang with the wasm32 target and wasm-ld (Ubuntu: clang, lld).
set -e; cd "$(dirname "$0")"
clang --target=wasm32 -O3 -msimd128 -nostdlib -Wl,--no-entry -Wl,--initial-memory=33554432 -Wl,--max-memory=33554432 -o /tmp/chg_kernel.wasm kernel.c
base64 -w0 /tmp/chg_kernel.wasm > kernel.wasm.b64; rm /tmp/chg_kernel.wasm; wc -c kernel.wasm.b64
