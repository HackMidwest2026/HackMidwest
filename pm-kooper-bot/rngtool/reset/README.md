# Reset / reload: does it narrow the RNG seed?

Question: save at a Save Block (outside Peach's Castle after Jr. Troopa, or before Final Bowser), reset the console and
reload the file — or "save and quit" after Chapter 7 — so the page knows the seed nearly at once. JP ROM, emulator +
decomp.

## How the seed is set at boot

- `src/main.c` (`boot_main`): `gRandSeed += osGetCount();` with `gRandSeed = 1` in the data segment. That is the only
  place the seed is set; everything else is `advance_rng()` (decomp grep).
- The data segment is reloaded from the cartridge on every boot, cold or reset, so the seed starts at `1 + Count`.
- IPL3 (the cartridge's boot code, ROM 0x44) starts with `mtc0 $zero, Count`, so Count restarts at 0 on every boot,
  power-on and reset button alike. The seed is therefore `1 + (CPU time from IPL3 start to that line)`, about 0.59 s.
  Time played before the reset does not matter.

## Emulator measurements (`boot_seed.py`, `soft_reset.py`; no RAM writes)

- Boot osGetCount, cold boot (6 runs): 0x01A84563–0x01A8669F. Reset button (`M64CMD_RESET` soft, 4 runs):
  0x01A868FD–0x01A87874. Pooled spread ≈ 13,000 ticks; the emulator itself is not cycle-exact here.
- From the seed being set to field control the RNG takes 1 step per game frame plus **15–16 extra steps**, the same for
  every input timing tried (A every 13/17/20/25/31 frames, first press at frame 0–90). Title, file select and file load
  add no timing-dependent draws.
- Seed at control = LCG^(F + 15..16)(1 + C), where F = game frames from the seed line to control and C = boot Count.
- Fastest tested reset-to-control: 462 game frames (15.4 s) after the seed line, ≈ 16.5 s from the button; mashing at
  human speed ≈ 17–20 s.

## Save and Quit (no reset)

Returning to the title does not run `boot_main`, so the seed just continues. Nothing is gained unless the console is reset.

## What it would buy (estimate, not tested end to end)

- Candidates ≈ Count spread × frame uncertainty × 2. With the emulator's spread (13 k ticks) and ±3 frames from video
  timestamps: ≈ 180 k candidates ≈ 17.5 bits; with the page's ~6-bit safety margin ≈ 24 bits ≈ 20–25 s of coin.
  A fresh lock needs ~38 bits (25–40 s standing in a battle menu).
- Reset costs ≈ 17–20 s of wall time (plus the save itself), so it only wins if the coin watching overlaps with walking
  to the fight (osr_02 Save Block → Hallway Bowser; the rooms in between were measured clean, and the Hallway Bowser
  intro is fixed). Then it trades ~20 s of reset for 25–40 s of standing.
- Final Bowser: the Save Block is before phase 1; phase 1's battle is not modelled, so FB2 needs its own lock anyway.
  A reset there does not help.
- Speedrun rules may or may not allow a reset or save-and-quit; that is the runner's call.

## Not verified

- **Real-console Count spread** — the deciding number. If the console's boot is as steady as the emulator (≤ ~10⁴ ticks)
  the idea saves 5–20 s at Hallway Bowser; if it varies by ~10⁶ ticks or more it saves nothing. To measure: reset,
  get a normal lock, then `python3 unwind.py SEED MAX_STEPS` (walks the LCG back; the hit near frames-since-reset + 16
  gives that boot's Count). A handful of resets gives the spread.
- Whether the status bar coin can be shown right after the file loads, and the walk from the osr_02 Save Block
  (no savestate of that room).
- Reset-button timing on hardware (pre-NMI to NMI ≈ 0.5 s).
