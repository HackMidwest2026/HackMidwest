# HackMidwest: kz-lite with save states

`kz/` is a copy of [krimtonz/kz](https://github.com/krimtonz/kz) (the Majora's Mask practice ROM) at commit `30a965b`, changed so that **kz-lite supports save states**. Upstream, only the full version (custom Project64) and the Wii VC version have them.

`patches/kz-lite-savestates.patch` holds the same change as a patch against upstream kz. Apply it with `git apply`.

## Patch your ROM (no tools needed)

1. Download [`release/dist/kz-lite-savestates-v1.zip`](release/dist/kz-lite-savestates-v1.zip) and unzip it.
2. **Windows:** drag your ROM onto `build-rom-lite.bat`, or copy the ROM into the unzipped folder and double-click `build-rom-lite.bat`.
   **Linux:** run `./build-rom-lite.sh /path/to/rom.z64`. **macOS:** the same, after installing [`gru`](https://github.com/glankk/n64).
3. The patched ROM appears in the same folder as `kz-lite-<version>-savestates.z64`.

Supported ROMs: unmodified NTSC-U 1.0, NTSC-J 1.0 or NTSC-J 1.1, in `.z64`, `.n64` or `.v64` byte order. The package contains no game data; everything is applied to your own ROM.

Controls: D-left saves a state, D-right loads it, R + L opens the kz menu.

The package holds prebuilt kz-lite binaries for all three ROMs, a standalone `gru` (`gru.exe` for Windows, a static Linux build), and `lua/patch.lua`. That script is kz's `make.lua` changed to use the prebuilt files and to generate the small loader stub itself. To rebuild the package, see `release/build-gru.sh` and `release/make-release.sh`.

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

Notes from building it for real:
- **Version string:** outside a git checkout, set `PACKAGE_VERSION` first (e.g. `export PACKAGE_VERSION=lite-savestates`). Otherwise the version string contains spaces and every compile fails.
- **libstdc++:** kz links with `mips64-g++`. If your toolchain was built without libstdc++, create an empty one with `mips64-ar rcs <prefix>/mips64/lib/libstdc++.a`; kz is pure C.

## What has been verified

**In an emulator** (mupen64plus 2.5.9, Japanese 1.0 ROM, built with a real GCC 13.2 + newlib toolchain), using the attract-mode demo, which runs as normal gameplay:
- **Save:** saving works. Message: `saved state 0 (untitled, 115kb)`. A Clock Town state compresses to about 113–115KB.
- **Load across scenes:** loading after the demo had moved to a different scene restores the saved frame almost pixel for pixel.
- **Game continues:** the game keeps running afterwards, through the fade and into the Stock Pot Inn scenes, the same sequence as the unpatched ROM.
- **Repeated use:** loading the same state twice, then saving over the slot and loading again, all work.
- **Menu:** the states menu shows `size 115kb free 148kb`.

**Release package:**
- **Same ROM as kz's own build:** the JP 1.0 ROM it produces is byte-for-byte identical to kz's own `build/makerom-lite` output from the same binaries. That holds for the Linux `gru` and for `gru.exe` running `build-rom-lite.bat` under Wine, both by dragging the ROM onto it and by double-clicking with the ROM in the folder.
- **Byte-swapped dumps:** a `.n64` dump gives the identical result.
- **Wrong ROM:** a modified ROM is rejected with a clear message.
- **In the emulator:** the package's ROM saves and loads correctly.
- **NTSC-U 1.0 and NTSC-J 1.1:** these use the same code path but haven't been patched or run, because I didn't have those ROMs.

`tests/emulator/` has the scripts used. They drive mupen64plus under Xvfb with xdotool and take screenshots.

**Host-side tests** (`tests/run_tests.sh`):
- **Compressor:** round-trips thousands of mixed chunks (zero runs, random data, struct-like data, empty and 1–3 byte chunks). It also checks that a too-small output buffer fails without writing past its end.
- **Allocator:** runs a 200k-operation random workload on kz-lite's allocator under AddressSanitizer. This covers the largest-block-then-shrink pattern, checks every block's contents, and checks that all memory is recovered at the end. The unmodified upstream allocator segfaults on the same workload.

## Known limitations / not verified yet

- **One state at a time.** With the 96KB `STATE_MEM_RESERVE`, there's room for one ~115KB state. Re-saving the same slot always works; saving to a second slot reports "not enough memory". Lowering the reserve (in `kz/include/state.h`) would allow two states, at some risk of menus running out of texture memory.
- **Not run on a console, and only lightly in real gameplay.** Testing used the attract demo, not a save file. Things to try: dungeons, the pause screen, Deku/Goron/Zora forms, and saving during cutscenes or scene transitions.
- **Save/load speed on hardware** is unmeasured. Expect a visible hitch, as in the full version.
