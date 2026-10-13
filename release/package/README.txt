kz-lite with save states
========================

kz is a practice rom for The Legend of Zelda: Majora's Mask
(https://github.com/krimtonz/kz). This package patches your own rom with
kz-lite, the version that runs on a real N64 (with an Expansion Pak),
the Wii U VC and standard emulators, with save states added.

Supported roms (unmodified, .z64, .n64 or .v64):
  * NTSC-U 1.0  (USA)
  * NTSC-J 1.0  (Japan)
  * NTSC-J 1.1  (Japan)

Windows
-------
Drag your rom onto build-rom-lite.bat.
Or: copy your rom into this folder, then double click build-rom-lite.bat.
The patched rom is created in this folder, named kz-lite-<version>-savestates.z64.

Linux / macOS
-------------
./build-rom-lite.sh /path/to/rom.z64
(Linux x86-64 uses the included gru. On macOS, build gru from
https://github.com/glankk/n64 and put it in your PATH first.)

Using save states
-----------------
  D-Left        save state
  D-Right       load state
  R + L         open the kz menu; "states" selects the slot, renames, clears,
                exports/imports, and shows the state's size and free memory

kz-lite has very little free memory, so states are compressed.  A typical
state is around 100kb, and in testing there was room for two.  If a save says
"not enough memory", clear a state in another slot from the states menu.

SD card (flashcarts)
--------------------
On a 64drive, EverDrive-64 (X-series, v1-v3, ED64+) or SummerCart64, states,
memfiles and positions can be exported to and imported from the SD card:
states menu -> export / import, and settings -> memfile / position.
The SD card must be FAT32 (or FAT16); exFAT is not supported.
States from kz-lite and from the full/Wii VC versions of kz are not
interchangeable.

This package contains no game data. Everything is applied to your own rom.

Source: https://github.com/HackMidwest2026/HackMidwest (kz/)
kz is licensed under the GNU GPL v3, see LICENSE.txt.  kz-lite's sd card support
uses libcart (LICENSE.libcart.txt) and FatFs (LICENSE.fatfs.txt).
