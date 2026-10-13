# HackMidwest: kz-lite with save states

`kz/` is a copy of [krimtonz/kz](https://github.com/krimtonz/kz) (the Majora's Mask practice ROM) at commit `30a965b`, changed so that **kz-lite supports save states**, including exporting and importing them on a flashcart's SD card, and **input macros** like gz's. Upstream, only the full version (custom Project64) and the Wii VC version have save states.

`patches/kz-lite-savestates.patch` holds the same change as a patch against upstream kz. Apply it with `git apply`.

## Patch your ROM (no tools needed)

1. Download [`release/dist/kz-lite-savestates-v3.zip`](release/dist/kz-lite-savestates-v3.zip) and unzip it.
2. **Windows:** drag your ROM onto `build-rom-lite.bat`, or copy the ROM into the unzipped folder and double-click `build-rom-lite.bat`.
   **Linux:** run `./build-rom-lite.sh /path/to/rom.z64`. **macOS:** the same, after installing [`gru`](https://github.com/glankk/n64).
3. The patched ROM appears in the same folder as `kz-lite-<version>-savestates.z64`.

Supported ROMs: unmodified NTSC-U 1.0, NTSC-J 1.0 or NTSC-J 1.1, in `.z64`, `.n64` or `.v64` byte order. The package contains no game data; everything is applied to your own ROM.

Controls: D-left saves a state, D-right loads it, R + L opens the kz menu. The menu's **states** page exports/imports states to the SD card. **settings** does the same for memfiles and positions. The **macro** page records and plays back input; the `record macro` and `play macro` commands have no default binding and can be bound under settings → commands.

The package holds prebuilt kz-lite binaries for all three ROMs, a standalone `gru` (`gru.exe` for Windows, a static Linux build), and `lua/patch.lua`. That script is kz's `make.lua` changed to use the prebuilt files and to generate the small loader stub itself. To rebuild the package, see `release/build-gru.sh` and `release/make-release.sh`.

Older releases are kept so existing links keep working: `v1` (save states only) and `v2` (adds SD card support).

## Why kz-lite didn't have save states

Majora's Mask needs the Expansion Pak and uses nearly all 8MB of RDRAM. kz-lite has two places to live:

| region | size | used for |
|---|---|---|
| `0x8003DF60`–`0x80080000` (end of the low framebuffer/skybox buffer) | ~270KB | kz code + small heap |
| `0x80700000`–`0x80780000` (taken from the end of the game's actor heap) | 512KB | kz heap |

The full version's save state code copies raw game memory: the `PlayState` alone is ~103KB, `SaveContext` is ~18KB, and on top of that come every live actor/overlay allocation in the arena, display lists, collision and particles. A state comes to roughly 300KB–1MB, which is more than kz-lite has free.

## How this version does it

### Save states

1. **Compressed states, no scratch buffer** (`kz/src/state_lz.c`). The lite build reuses the full version's save/load code in `state.c`. Each chunk written with `st_write` goes through a small LZ77 compressor. Each `st_read` decompresses straight into game memory. Matches only reference earlier bytes of the same chunk, so neither side needs a history window, and the raw state never has to exist in RAM. The compressor uses a 16KB hash table only while saving, and loading allocates nothing.
2. **States don't need contiguous memory** (`kz/src/state_chunk.c`). kz's heap is already fragmented at boot (in testing: 318KB free, but the largest block was 149KB). A lite state is therefore a list of chunks, filled from the largest free blocks first, and the compressor reads and writes through a stream that moves between chunks. A state can use all free memory except a 64KB reserve (`STATE_MEM_RESERVE`) kept for kz itself. The `.kzs` file format doesn't depend on the chunking.
3. **Keep the old state until the new one exists.** Saving over a slot first tries to fit the new state alongside the old one. Only if that fails is the old state freed and the save retried. Import works the same way.
4. **Running out of memory doesn't crash.** kz-lite's menu icons are 8KB each, and loading one with no memory left used to write through a NULL pointer. Texture loading now fails cleanly and the icon just isn't drawn. In lite, all item icons are freed once their menu has been closed for a moment.
5. **Allocator fixes** (`kz/src/mem.c`). Existing bugs in kz-lite's allocator would break this:
   - **`realloc` shrink corrupted the block.** It placed the new free header inside the block's own data.
   - **`malloc` leaked bytes** whenever it handed out a block without splitting it.
   - **`free` lost the free list.** It never restored a heap's free list once that heap had been completely full.

   All three are fixed. `mem_shrink()` now shrinks a block in place, and `mem_largest_free()` reports free memory.
6. **Commands, binds and menu.** "save state", "load state", "prev state" and "next state" now exist in lite, with default binds of D-left to save and D-right to load, same as full. The states menu is enabled in lite: 5 slots, naming, clear, export and import. It shows the selected state's compressed size and kz's free memory. The settings version is bumped for lite only, because the bind table grew.

### SD card on flashcarts

kz-full and kz-VC reach the SD card through homeboy (the Wii VC's helper). kz-lite now does it on real N64 flashcarts:

- **[libcart](https://github.com/devwizard64/libcart)** (MIT, `kz/src/libcart.c`) talks to the cartridge. It supports the 64drive, EverDrive-64 X-series, EverDrive-64 v1–v3 and ED64+, and SummerCart64. It's adapted so kz shares the cartridge bus safely with the game's own loading thread:
  - **PI lock:** libcart holds libultra's PI access lock around every card operation. kz finds the lock functions at runtime inside `osEPiReadIo`, and checks they really call `osRecvMesg`/`osSendMesg`, so it works on all three ROM versions without hard-coded addresses.
  - **DMA:** transfers are polled with interrupts disabled, and the PI interrupt is cleared afterwards, so the game's PI manager never sees a completion it didn't ask for.
- **[FatFs](http://elm-chan.org/fsw/ff/)** (`kz/src/ff.c`) is the FAT filesystem: FAT12/16/32 with long file names. exFAT is left out to save 7KB.
- **`kz/src/sd.c`** implements kz's existing `sys.h` file API (open/read/write/opendir/...) on top of them. kz's own file browser, and the state/memfile/position export and import code, work unchanged.
- **Lite states are tagged** (`state_version` 0x8008) so a compressed lite `.kzs` and an uncompressed full/VC `.kzs` are never loaded by the wrong build.

The SD code costs about 39KB of kz-lite's memory.

### Macros

Macros work like gz's (built from its documentation, not its code; gz has no license): record controller input frame by frame, then play it back from a save state.

- **Recording** (`kz/src/macro.c`) happens in kz's input hook, after the game has read and calibrated the controller. Each frame stores the held, pressed and released buttons and the raw and adjusted stick (10 bytes per frame). **Playback** writes the same values back in the same place, so the game sees exactly what it saw while recording.
- **Save states remember the macro frame.** A state saved while a macro is recording or playing stores the current macro frame. Loading it moves the macro back to that frame. This gives gz-style rerecording: load an earlier state while recording, and recording continues from there.
- **RNG:** MM only reseeds its RNG in `Play_Init`, through `Rand_Seed`, using the console's clock. kz patches `Rand_Seed` (after checking its three instructions are what they should be) to record the seed while recording and give the game the recorded seed while playing.
- **Storage** (`kz/src/macro_store.c`) is in pages of 512 frames (5KB), so a macro doesn't need contiguous memory and grows as it's recorded. At MM's usual 20 frames per second, a minute of gameplay takes 12KB.
- **Export/import** to the SD card as `.kzmc` files: header (`kzmc`, format version, mm version, frame count, seed count), then the frames and seeds.
- **Menu and commands:** a **macro** menu (record, play, rewind, trim, clear, frame counter, export, import), `record macro` and `play macro` commands, and a `rec`/`play` counter on screen. The macro code adds about 6KB to kz-lite.

What gz has that this doesn't: the virtual controller, room-load and ocarina sync hacks, and macro frames in exported states.

### Other fixes found along the way

- **`cache.S`:** `osWritebackDCache` and `osInvalDCache` looped forever on buffers under 8KB. kz had never used those paths; the SD code needs them.
- **makefile:** it generated header dependency files but never included them, so changing a header didn't rebuild the files using it. A stale build of this kind produced a ROM that hung at boot. The makefile now includes them, and `release/make-release.sh` always builds from clean.

`kz/USAGE.md` documents the user-facing side in "Lite Version", "States", "SD Features", "Macro" and "Macros".

## Building

Same as upstream (see `kz/BUILDING.md`): install glankk's [n64 toolchain](https://github.com/glankk/n64), then from `kz/` run

    build/makerom-lite /path/to/vanilla/rom.z64

The `homeboy` submodule isn't included here; it's only needed for Wii VC builds.

Notes from building it for real:
- **Version string:** outside a git checkout, set `PACKAGE_VERSION` first (e.g. `export PACKAGE_VERSION=lite-savestates`). Otherwise the version string contains spaces and every compile fails.
- **libstdc++:** kz links with `mips64-g++`. If your toolchain was built without libstdc++, create an empty one with `mips64-ar rcs <prefix>/mips64/lib/libstdc++.a`; kz is pure C.

## What has been verified

All with the Japanese 1.0 ROM, built with a real GCC 13.2 + newlib toolchain.

**Save states, in mupen64plus 2.5.9**, using the attract-mode demo, which runs as normal gameplay:
- **Save:** saving works. Message: `saved state 0 (untitled, 115kb)`. Clock Town states compress to 95–115KB.
- **Load across scenes:** loading after the demo had moved to a different scene restores the saved frame almost pixel for pixel.
- **Game continues:** the game keeps running afterwards, the same sequence as the unpatched ROM.
- **Repeated use:** loading the same state twice, then saving over the slot and loading again, all work.

**SD card, in [gopher64](https://github.com/gopher64/gopher64)**, which emulates a SummerCart64 with an SD card:
- **Detection and mount:** kz detects the cart, finds the PI lock, mounts the card, and the file browser lists it.
- **Export:** writes `untitled.kzs`. Read back outside the emulator with `mtools`, the file is 96,841 bytes, with the lite tag and a size field matching its length.
- **Import across sessions and builds:** a fresh session with a newer build, and the card from the earlier session, imports that file (`imported to state 0`). Loading it (`loaded state 0`) jumps from the scene the demo was in back to the exact moment saved in the earlier session.
- **Memory:** with that 95KB state loaded, kz still has 220KB free.

**Macros, in mupen64plus 2.5.9:** In South Clock Town I started recording, saved a state, then walked, turned, rolled and turned again, and stopped recording. I then loaded the state and played the macro, twice. A debug build recorded Link's position and facing on the last recorded frame and on the last played frame. Both playbacks matched the recording exactly, bit for bit (`x=c4f24788 y=c3180000 z=43ca0000`, facing `8793`).

`tests/emulator/` has the scripts. They drive the emulators under Xvfb with xdotool and take screenshots: scripted save/load runs for mupen64plus, and `interactive/` helpers (start, press keys, screenshot) used to step through the menus in gopher64.

**Release package (v1 and v2):**
- **Same ROM as kz's own build:** the JP 1.0 ROM it produces is byte-for-byte identical to kz's own `build/makerom-lite` output from the same binaries. That holds for the Linux `gru` and for `gru.exe` running `build-rom-lite.bat` under Wine.
- **Byte-swapped dumps:** a `.n64` dump gives the identical result.
- **Wrong ROM:** a modified ROM is rejected with a clear message.
- **In the emulator:** the v2 package's ROM saves and loads correctly.

**Host-side tests** (`tests/run_tests.sh`):
- **Compressor:** round-trips thousands of mixed chunks through output split into blocks as small as 1 byte. It also checks that running out of space fails without writing past any block.
- **Allocator:** runs a 200k-operation random workload on kz-lite's allocator under AddressSanitizer, checking every block's contents, and checks that all memory is recovered. The unmodified upstream allocator segfaults on the same workload.
- **State memory:** saves, export/import round trips, truncated files and out-of-memory cases on a fragmented kz-lite heap. States end up split across chunks, and all memory is returned. The test is strict enough to catch an import bug found during development.
- **Macro storage:** records random input across many pages with rerecording and trimming, and checks every frame and RNG seed against a reference. It also checks file round trips, and that bad, truncated and wrong-version files are rejected and leave no macro behind.

## Known limitations / not verified yet

- **Not run on a console.** Everything above was tested in emulators.
- **Only lightly tested in real gameplay.** Testing used the attract demo, not a save file. Things to try: dungeons, the pause screen, Deku/Goron/Zora forms, and saving during cutscenes or scene transitions.
- **Only the SummerCart64 SD path was tested** (in gopher64). The 64drive and EverDrive drivers come from libcart and use the same code around them, but haven't been run.
- **SD cards must be FAT32 (or FAT16).** exFAT isn't supported in lite.
- **Lite and full/VC `.kzs` files aren't interchangeable.** Lite states are compressed.
- **How many states fit depends on the scene.** With one 95KB state loaded, kz had 220KB free, which leaves room for a second similar state above the 64KB reserve. I didn't hold two states at once in-game; the host test does. A save that doesn't fit says "not enough memory", and clearing another slot frees memory. When memory is very low, some menu icons may not be drawn.
- **NTSC-U 1.0 and NTSC-J 1.1** are built and patched the same way, but haven't been run, because I didn't have those ROMs.
- **Macros were tested only in the one short run above.** Longer macros across scene loads (where the recorded RNG seed matters), and playback on hardware, haven't been tried.
- **Save/load speed on hardware** is unmeasured. Expect a visible hitch, as in the full version.
