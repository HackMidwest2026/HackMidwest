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

## First real-console boot clip (Nov 2, S-Video → GV-USB2 → OBS, 60 fps, 48.4 s)

**Bottom line: the clip can't give the console's boot Count, so the Count spread is still unmeasured.** It holds one
boot, not five. There is no pause menu in it: after the file loads, Mario stands in the field for 37 s with the
status-bar coin showing. The room is kzn_03 (Mt. Lava Lava, Save Block room), where three Spike Tops and a Putrid
Piranha draw from gRandSeed about twice a second. That breaks the coin model, so no seed can be locked from this footage.

### What is in the clip (`boot_clip.py`, video frame numbers at 60 fps)
| Video frame | Time | What |
|---|---|---|
| 0–107 | 0–1.8 s | GV-USB2 blue screen (no signal) |
| 108 | 1.80 s | Signal appears (grey). The console has started its video by now. |
| 142 | 2.37 s | N64 logo starts fading in |
| ~295 | 4.9 s | Title screen. The logos were skipped with a button press (JP only). |
| ~330–575 | 5.5–9.6 s | File select and load |
| 588–639 | 9.8–10.7 s | Black screen while the file loads |
| 643 | 10.7 s | kzn_03 fades in; Mario is at the Save Block |
| 695–2905 | 11.6–48.4 s | Status bar up (36.9 s), Mario standing still, coin always visible |

- **Boots: 1.** The other clips uploaded that day are star-spirit and Bowser scenes, not boots.
- **Time in the pause stats tab: 0 s.** The pause menu is never opened.
- **Coin:** 13 shines, all at the regular cadence (48 + 24k game frames apart, ±1). The draw pattern from the first
  shine is `SS...S..S..SSS.SS...SS..S.S`, with up to 6 plain spins before it. That is ≈ 33 draws, ≈ 32 bits if the
  room were clean.
- **Seed line in video frames:** by the emulator's Count, the seed line comes about 13–17 VIs before the logos'
  game mode starts (`boot_anchor.py`), so it falls at about video frame 125 ± 5. Power-on to field control took
  ≈ 8.6 s ≈ 259 ± 6 game frames, faster than the emulator's 462 because the JP build lets a button skip the logos.

### Q1: Do the room's NPCs and enemies draw while the game is paused? No.
- Decomp (`state_pause.c`): for the first ~5 frames after Start (state 0 plus a 4-frame delay), the game still calls
  `update_npcs()`. After that, `clear_script_list()`, `clear_npcs()` and `clear_worker_list()` remove every
  NPC, enemy AI and map script, and the map is rebuilt on unpause. Only the per-frame step and the HUD coins run while
  paused.
- Emulator (`kzn03_draws.py`, kzn_03 made with the same warp as `make_state_kpa.py`, 4 seeds): over 260–860 paused
  frames, the only calls are the frame step and the coin (two coin streams, one draw per ~16 frames in all). In 2 of 4
  seeds, one Spike Top wander group (3 draws) landed in the first 40 frames after Start, during the frames
  before the clear.
- So once the menu is up, a pause-coin stretch is clean in any room.

### Q2: kzn_03 before the pause, and the unwind
- Field, Mario standing still, 1800 frames, 4 seeds: besides the frame step and the coin there were 55–66
  `rand_int` calls from the wander AI (callers 0x80049298/2b8, 0x8004978c/83c/85c, 0x80049aa8; ranges 31, 60, 1000,
  180). They come in groups of 1, 2 or 3, every ~40–60 frames, at seed-dependent times. That is ≈ 2 draws/s
  (1–5 per second, varying), and the count over 30 s changes by ±10 % with the seed. Kolorado's walk is a fixed lerp
  and draws nothing.
- **Field coin in kzn_03: unusable.** Each 24-frame coin interval gets 0–5 unknown extra steps. That costs more bits
  than a coin roll gives (≤ 0.88 bits), so neither the page's lock nor a boot-prior search can work. Checked on this
  clip: `boot_search` with an emulator-like window (C 0x01A70000–0x01A9FFFF, n0 280–420, 0.005 chance fits expected)
  finds no fit. That is the expected result when the model is wrong.
- **Pause coin after a kzn_03 load: usable, but worse.** The steps from boot to the lock become frames + 15..16 +
  field coin draws + E, where E ≈ 2 per second spent in the field before the menu is cleared (unknown, seed-dependent).
  An unwind then has to scan a step window about ±(E + video timing) wide. Expected false hits = window × (Count
  window) / 2³²: with a 2²⁵ Count window (0x01000000–0x02FFFFFF), 20 steps give 0.16 per boot, and 60 steps (about
  10 s in the field) give 0.5. Pausing within ~2 s of control keeps it near 0.1. Several boots then check each other,
  because true Counts cluster and false hits spread over the whole window. The pause also has a second, hidden
  coin stream with an unknown phase, which needs ~6 more bits than one stream. So a full ~38-bit lock (≈ 40 s
  in the menu) is the realistic route there.
- **Is a no-enemy room needed?** It isn't strictly needed for the pause method, but it is much better. In a clean
  room the field status-bar coin is one stream with no unknown steps, so the boot-prior forward search
  (`boot_search.c`) works straight from the video. It doesn't need a full lock.

### Clean rooms with a Save Block on the route
Emulator, Mario standing. "Clean" means only the frame step and the coin draw. Checked with `kzn03_draws.py`
(per caller) and the existing `../kpa_roomsteps.py` (steps per frame; 600 frames standing, then walking).
| Room | Result | Note |
|---|---|---|
| osr_02 (outside Peach's castle, STORY 95 state) | 0 odd frames in 1200 (`kpa_roomsteps`) | clean; the reset idea's own Save Block |
| kpa_63 (Save Block room after door 1) | 0 other calls in 1200 frames; pause clean too | clean |
| kpa_33 (stair hall, Save Block) | 0 odd frames in 667 (left the room) | clean |
| kzn_03 (this clip) | 55–66 wander-AI calls per 1800 frames | not clean |

`kzn03_draws.py` (debugger core) stalls on the osr_02 and kpa_33 states, so those two have only the step-count check.
- The coin model in `boot_search.c` (draw = rand_int(100), then the frame step; next draw 24 frames later, 48 after a
  shine) reproduces all 50 draws (frames and shines) in kpa_63 from the seed before the first draw
  (`coin_model_check.py`).

### Q3/Q4: Count per boot and spread
- **Recovered: none.** The clip has one boot, the room is not clean, and there is no pause stretch. The console's
  Count spread compared with the emulator's ~13 k ticks stays **unmeasured**, and the reset idea stays undecided.
- `boot_search` self-tests (synthetic boots, C window 0x01000000–0x02FFFFFF = 2²⁵):
  - C = 0x01A86000, n0 = 600 ± 8, 33 draws ≈ 31.6 bits (2^29.1 candidates, 0.17 chance fits expected): it finds
    the true (C, n0) and nothing else, in ~20 s. A clean-room clip as long as this one would have been enough.
  - C = 0x01B3C5A7, n0 = 1234 ± 25, 45 draws ≈ 41.5 bits: it finds the true fit **and an alias**, C = 0x01DD1339 at
    n0 = 1212, with the **same seed at the first draw**. The LCG path from the true boot passes through 1 + 0x01DD1339
    22 steps later. More coin doesn't help with this: the seed is right, but the split into (C, n0) is ambiguous. Expected
    aliases per boot = Count window × n0 window / 2³² (0.39 here; 0.13 for ±8 steps). This is the unwind's
    false-hit rate from Q2. Only a tighter n0 (good video anchors) or a tighter Count window removes it. Across boots
    the true Counts cluster and aliases scatter over the whole window, so 3–5 boots settle it.

### What to record next
1. **Room:** a Save Block room with no enemies, saved with Mario at the block. Use osr_02 (outside Peach's castle,
   the reset idea's own Save Block) if the file is there; otherwise kpa_63 or kpa_33. Don't use kzn_03.
2. **Per boot:** turn the power on with the capture already running, so the blue no-signal screen and the logo fade
   are in the clip. Press A through to the file (skipping the logos is fine). After the file loads, **do not touch the
   controller and do not pause**. Stand for **≥ 45 s** with the status bar up. That gives ≈ 40 bits: enough for
   `boot_search` with a wide Count window and for the page's ordinary lock as a cross-check. 60 s gives margin.
3. **Boots:** 5 (3 is the minimum for a spread). Power-cycle each time. Also do 2 with the reset button, since the
   emulator separates the two. One file per boot, or one long file with a gap between boots.
4. Per boot, run `boot_clip.py` (pattern + video frames), then
   `boot_search 01000000 02FFFFFF NLO NHI PATTERN` with n0 = (draw video frame − logo frame + 13..17) / 2 + 15..16
   + coin draws between field control and that draw. Use ± 8 if the anchors are clear and ± 25 if not; the alias rate goes up with the window.
   Fits that share one first-draw seed are one seed. Count spread = max − min of the fitted C. In the emulator it is ≈ 13 k ticks.
   If the console stays within ~10⁴–10⁵ ticks, the reset idea is worth building. If the fits scatter by 10⁶ or more,
   drop it.

Files: `boot_clip.py` (video timeline + coin pattern), `boot_anchor.py` (emulator VI anchors around the seed line),
`boot_search.c` (boot-prior forward search; `gcc -O2 -fopenmp -o boot_search boot_search.c -lm`),
`make_state_kzn03.py`, `kzn03_draws.py` (per-caller RNG draws, field and pause), `coin_model_check.py`.

## Second boot clip (Nov 2, 16:02, "console boot into reload, in chapter 1"): first console boot Count

**Result: boot Count C = 0x02079874 (34.0 M ticks, 0.726 s at 46.875 MHz), n0 = 306 steps to the first used coin
draw. The seed is certain; the (C, n0) split is very likely but not proven.** That is 6.23 M ticks (+22 %) above
the emulator's 0x01A84563–0x01A87874. One boot gives no spread.

### The clip
- **JP:** the title is マリオストーリー and the file select is in Japanese.
- **Room:** trd_00, the Koopa Bros. Fortress exterior with a Save Block. Mario has Bombette (STORY ≥ BOMBETTE_JOINED).
  At that story the room's NPCs are the Koopa Bros. (removed once STORY ≥ SPOTTED_BY_KOOPA_BROS) and Eldstar (only
  after the boss), so there are **no enemies and nothing wandering**.
- **Measured clean** with `make_state_warp.py trd_00 0 -83 3` (DIAGNOSTIC warp, story and Bombette written) and
  `kzn03_draws.py`. Over 1800 field frames the only calls are the frame step and 56 coin draws. The pause is clean
  too. `coin_model_check.py` reproduces all 48 draws.
- **Timeline (video frames):** blue screen to 85, black signal from 86, N64 logo fade-in from 124, title, file select,
  black load 558–602, field from 603, status bar up from 665 to the end (3330). That is **44.4 s** standing, with the
  bar and scene steady (no input, no pause).
- **Against the recording instructions:**
  - Capture before power-on: yes.
  - A through to the file, with the logos skipped: yes.
  - No input and no pause: yes.
  - Stand ≥ 45 s: 44.4 s, just short but enough.
- **Coin:** 15 shines, all on cadence. The pattern with 3 plain spins before the first shine (`boot_clip.py`) is
  `...SS...SS.SSS.....SSSS..S.S...S.......S`: 40 draws, 38.9 bits.

### Search
- `boot_search 01A70000 01A9FFFF 280 400` (an emulator-like window): **no fit**. The console is not inside the
  emulator's window.
- `boot_search 01000000 02FFFFFF 300 360`: **one fit, C = 0x02079874, n0 = 306**, seed at that draw 0xD74B7923.
  Expected chance fits 0.004, so the seed is right (≈ 8 bits of margin).
- **Aliases** (`unwind.py D74B7923 1000 01000000 03000000`): along the same path the window is also hit at n0 = 487
  (C = 0x019BEAB7) and n0 = 641 (0x01457DF9). Both are impossible: the game makes at most 1 step per 2 VIs plus the
  fixed extras, so n0 ≤ (727 − 86) / 2 + 16 + 3 ≈ 340. With no limit on C, n0 = 333 (C = 0x0354C685, 1.19 s) and
  n0 = 243 (0x0468F923, 1.58 s) also fit.
- **Why n0 = 306** (`boot_anchor.py`, which now also counts RNG steps per game mode):
  - In the emulator the seed line comes 13–17 VIs before the logos, so here it falls at about video frame 109.
    Seed line to that draw (video 727) is ≈ 309 game frames at 2 VIs each, + 15..16 extras + ~3 field coin draws
    ≈ 328 with no lag.
  - The emulator loses ~32 game frames to lag in the file load (mode 15 → 4: 252 VIs, 94 steps). n0 = 306 means
    ≈ 22 lag frames, about the console's 45-frame black load.
  - n0 = 333 would need zero lag during the load and a seed line before video frame 99. n0 = 243 would need ~85 lag
    frames. So C = 0x02079874 is the only reading that fits the video.
- **What it means:** the console's boot takes ~0.13 s more CPU time to reach the seed line than this emulator. The
  emulator's absolute Count is no prior for the console. Only the console's own spread around ~0x0207xxxx matters for
  the reset idea, and it is still unknown.

### Record next
- **Same room** (trd_00 Save Block, the same file) and the same procedure: 4 more power-cycle boots, then 2 with the
  reset button.
- Stand **≥ 50 s** each (this one, at 44 s, had 8 bits of margin).
- Keep the button pattern to the file about the same, so lag and n0 stay comparable.
- Search each boot with the wide window first (`01000000 02FFFFFF`, n0 ± 30 around 306 + the frame difference).
  Once two boots agree, use C ± 2²⁰ around them: aliases drop to ~0.001.
- Spread = max − min of the C values. If it is ≤ ~10⁵ ticks the reset idea is worth building; if it is ~10⁶ or more,
  drop it.
