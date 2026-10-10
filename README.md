# HackMidwest: kz-lite with save states

`kz/` is a copy of [krimtonz/kz](https://github.com/krimtonz/kz) (the Majora's Mask practice ROM) at commit `30a965b`, changed so that **kz-lite supports save states**. Upstream, only the full version (custom Project64) and the Wii VC version have them.

`patches/kz-lite-savestates.patch` holds the same change as a patch against upstream kz. Apply it with `git apply`.

## Why kz-lite didn't have save states

Majora's Mask needs the Expansion Pak and uses nearly all 8MB of RDRAM. kz-lite has two places to live:

| region | size | used for |
|---|---|---|
| `0x8003DF60`–`0x80080000` (end of the low framebuffer/skybox buffer) | ~270KB | kz code + small heap |
| `0x80700000`–`0x80780000` (taken from the end of the game's actor heap) | 512KB | kz heap |

The full version's save state code copies raw game memory: the `PlayState` alone is ~103KB, `SaveContext` is ~18KB, and on top of that come every live actor/overlay allocation in the arena, display lists, collision and particles. A state comes to roughly 300KB–1MB, which is more than kz-lite has free.

## How this version does it

1. **Compressed states, no scratch buffer** (`kz/src/state_lz.c`). The lite build reuses the full version's save/load code in `state.c`. Each chunk written with `st_write` goes through a small LZ77 compressor. Each `st_read` decompresses straight into game memory. Matches only reference earlier bytes of the same chunk, so neither side needs a history window, and the raw state never has to exist in RAM. The compressor uses a 16KB hash table only while saving, and loading allocates nothing.
2. **Allocate the largest block, then shrink it.** The compressed size isn't known in advance. So `save_state_alloc()` compresses into the largest free block, leaving a reserve (`STATE_MEM_RESERVE`, 96KB) for kz's own menu textures. It then `realloc`s the block down to the real size. If the state doesn't fit, it gives up cleanly.
3. **Keep the old state until the new one exists.** Saving over a slot first tries to fit the new state alongside the old one. Only if that fails is the old state freed and the save retried.
4. **Allocator fixes** (`kz/src/mem.c`). Two existing bugs in kz-lite's allocator would break this:
   - **`realloc` shrink corrupted the block.** It placed the new free header inside the block's own data.
   - **`malloc` leaked bytes** whenever it handed out a block without splitting it.

   `free` also never restored a heap's free list once that heap had been completely full. All three are fixed.
5. **Commands, binds and menu.** "save state", "load state", "prev state" and "next state" now exist in lite, with default binds of D-left to save and D-right to load, same as full. The states menu is enabled in lite: 5 slots, naming, and clear. It shows the selected state's compressed size and kz's free memory. SD import/export stays full/VC-only. The settings version is bumped for lite only, because the bind table grew.

`kz/USAGE.md` documents this in the "Lite Version" section.

## Building

Same as upstream (see `kz/BUILDING.md`): install glankk's [n64 toolchain](https://github.com/glankk/n64), then from `kz/` run

    build/makerom-lite /path/to/vanilla/rom.z64

The `homeboy` submodule isn't included here; it's only needed for Wii VC builds.

## What has been verified

- The three lite builds (`kz-lite-NZSE`, `kz-lite-NZSJ`, `kz-lite-NZSJ10`) and the VC builds compile with no errors or warnings. I couldn't fetch glankk's toolchain in my environment, so I used Ubuntu's `mips-linux-gnu-gcc` with `-march=vr4300 -mabi=32` plus glankk's n64 headers. The lite binary grows by ~13.7KB, which comes out of the ~270KB region and leaves the rest for heap.
- `tests/run_tests.sh` runs host-side tests:
  - **Compressor:** round-trips thousands of mixed chunks (zero runs, random data, struct-like data, empty and 1–3 byte chunks). It also checks that a too-small output buffer fails without writing past its end.
  - **Allocator:** runs a 200k-operation random workload on kz-lite's allocator under AddressSanitizer. This covers the largest-block-then-shrink pattern, checks every block's contents, and checks that all memory is recovered at the end. The unmodified upstream allocator segfaults on the same workload.

## Not verified yet

- **Not run on a console or emulator.** I didn't have a ROM or an N64 emulator. The first thing to try is save and load in a few scenes (Clock Town, a dungeon, the pause screen) on real hardware or an accurate emulator such as ares.
- **Real compression ratio.** I had no Majora's Mask RAM dump to measure against. Game memory is mostly zeros and repeated structures, so it should compress well; I'd guess 25–50%. Whether that means one state or several fit depends on the scene. The states menu shows the actual numbers.
- **Save/load speed.** A rough estimate is ~0.1–0.3s to save and well under 0.1s to load on the VR4300. A save or load causes a visible hitch, as it does in the full version.
- **Reserve size.** `STATE_MEM_RESERVE` in `kz/include/state.h` is a guess at how much kz's menus need for textures. If menus misbehave after saving states, raise it. If states don't fit, try lowering it.
