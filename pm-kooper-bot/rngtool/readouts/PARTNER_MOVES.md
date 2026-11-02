# Partner moves as gRandSeed readouts (Goombario, Bombette, Sushie, Lakilester)

Question: which partner moves show gRandSeed draws on screen, so a runner could lock the seed from S-Video footage?
Scope: the three moves up to Super rank for each partner. Ultra-rank moves are covered briefly at the end.

**Short answer**
- **Spiny Surge (Lakilester, 4 FP)** is the best partner readout on the current route. Each thrown spiny takes
  4 draws: rest point x 10..150 and y 10..90, a spin angle 0..360 and a spin speed of 5..15 deg/frame. The spiny
  is a large sprite that flies straight to that rest point in 30 frames and hangs there before it falls. 10
  spinies at full mash, one every 6 frames, take about 2.5 s on screen. The rest points pile up on real footage,
  but each launch track is clean, so expect ~80-120 bits per Surge (emulator diff + real S-Video clip checked).
- **Cloud Nine (Lakilester, 4 FP)** is the cleanest one: always exactly 20 draws, one puff per frame for 10 frames.
  Each puff's centre is a `RandInt(40)`, `RandInt(30)` offset from Mario. The count is fixed even when the action
  command fails.
- **Goombario's Charge (1 FP)** is the same effect pair as Mario's Charge: 2 x `energy_in_out` type 6, 45 frames,
  about 110 ray-angle draws. It carries the same information as the current best readout, from a closer camera.
- **Sushie's Water Block** has the most draws: 5 sparkle bursts of 32 draws, then a **persistent** bubble effect
  that keeps drawing about every 30 frames for as long as the block lasts. Code-read only, and Sushie is not on the
  route.
- **Tattle does not help.** The tattle window, its camera and the zoom are fixed. The only gRandSeed draws it adds
  are a `rand_int(15)` speech-sound *volume* per printed character. That is an invisible RNG sink, and its count
  depends on how the text is advanced.
- Headbonk, Belly Flop, Body Slam, Bomb and Power Bomb draw nothing themselves. Each damaging hit only spawns the
  standard hit `firework`: 6/8/10/11 `rand_int(359)` ray yaws for 1-2/3-4/5-8/9+ damage, visible for about
  13 frames.

## How the RNG calls resolve
- `rand_int` / `rand_float` (`src/43F0.c`) both step `gRandSeed` (`seed * 0x5D588B65 + 1`). `rand_int(max)` returns
  0..max inclusive, using rejection sampling (so a draw can step the seed more than once, rarely). `rand_int(1)` is
  `rand_int_internal(1000) > 500`; `rand_int(0)` makes no draw.
- Effects call `rand_int` through `shim_rand_int` (`include/effect_shims.h: #define rand_int shim_rand_int`), which
  is the same gRandSeed function. The separate `effect_rand_int` (`effect_utils.c`) and the stateless
  `effect_simple_rand(max, idx)` LUT do not touch gRandSeed. Of the effects below, only `water_block` (vertex
  wobble) and `sparkles` type 0 (not used here) call `effect_simple_rand`, and that part is seed-independent.
- `Call(RandInt, n, var)` in an EVT script is `rand_int(n)` (`src/evt/f8f60_len_1560.c`; JP caller ra 0x802D46E0
  in the logs below).

## Ranked table
"Bits" means usable seed information per use through S-Video (~4.2 MHz luma, so ~2.25 capture samples per
320-wide game pixel horizontally; 1.3 MHz chroma, which is useless for small features). Ranges are a model-error
discount on the theoretical value. A lock needs ~38 bits (see README).

| # | Move (FP) | gRandSeed draws per use | What shows it | Bits (theory / realistic) | On screen | Count fixed? | Verified |
|---|---|---|---|---|---|---|---|
| 1 | **Lakilester Spiny Surge** (4) | 4 per spiny (`rand_int(140)`, `(80)`, `(360)`, `(10)`), 10 spinies at full mash = 40, + hit firework 6-11 | each spiny's rest point (x, y) and spin angle/speed | ~17-22 per spiny / ~8-12 per spiny: **~80-120 per Surge** | ~2.5 s (throws every 6 frames, each flies 30 frames) | No: spinies = mash; but each one is visible, so countable | draws + screenshot diff: emulator; real S-Video clip |
| 2 | **Goombario Charge** (1) | 2 x 21 init + ~70 respawn `rand_int(359)` (same as Mario's Charge) | long light rays, angle = draw | hundreds / 150-200 (README) | ~1.5 s | Yes (fixed 45-frame effect) | code-read; Mario's version emulator-verified in README |
| 3 | **Lakilester Cloud Nine** (4) | exactly 20: 10 x (`RandInt(40)`, `RandInt(30)`) | each puff's centre, x +-20, y +-15 units from Mario | ~10 per puff = 103 / ~40-60 | 10 frames of spawning, each puff lives 20 | **Yes** (thread runs even on a failed AC) | draws + screenshot diff: emulator |
| 4 | Sushie Water Block (3) | 1 + 12 + 5 x 32 = 173 at the cast, then ~4 per bubble cycle while the block lasts | sparkle positions (40 sparkles, staggered 2 frames apart); bubbles' size, drift, speed, respawn delay | ~10 per sparkle / ~4-6 per sparkle; bubbles ~10 per cycle (low contrast) | cast ~1 s; bubbles for 1-3 turns | Cast: yes if the AC succeeds (fails: none). Bubbles: seed-determined | code-read only |
| 5 | Lakilester Spiny Flip (0) | `energy_in_out` type 0 aim glow (21 init + ~1 per frame), hit firework | faint short streaks, firework | see README | ~2-3 s | No (aim time) | emulator (README) |
| 6 | Sushie Squirt (3) | `water_splash` type 0 on a damaging hit: 20 droplets x 3 `rand_int(10)` = 60 | droplet velocities (screen x/y) | ~6.9 per droplet / ~1-3 per droplet (faint refraction blobs) | ~10-15 frames | Yes (if it hits) | code-read |
| 7 | Headbonk (0), Belly Flop (0), Body Slam (0), Bomb (3), Power Bomb (6) | firework per damaging hit: 6/8/10/11 `rand_int(359)` | firework ray lengths (yaw foreshortening) | ~3-4 per ray / ~1-2 per ray: ~10-20 per hit | ~13 frames | Yes per hit; hits vary (miss = none) | firework draws: emulator (README) |
| 8 | **Goombario Tattle** (0) | 0 visible; `rand_int(15)` per printed character (voice volume) | nothing | 0 | - | No (text speed) | code-read |

## Per-move notes

### Goombario
**Headbonk** (`EVS_Attack_Headbonk1/2/3`, goombario.c)
- No `rand_int` in the script or its helpers (`JumpOnTarget`, `OnMissHeadbonk`). There are no `PlayEffect` calls.
- Each damaging hit goes through `PartnerDamageEnemy` -> `calc_partner_damage_enemy` -> `show_damage_fx`, which spawns
  `fx_firework(0, ..., intensity)` for non-fire/shock/water damage. `firework_main`: numParts = (5*intensity+20)/3 + 1,
  and each ray takes `unk_24 = rand_int(359)`. That gives **6 / 8 / 10 / 11 draws** for damage 1-2 / 3-4 / 5-8 / 9+.
  Two hits = two fireworks.
- Visible: each ray sits at a fixed in-plane angle `unk_1C = i*360/(n-1)`, with yaw `unk_24` about the local Y axis
  before that. So its on-screen length is ~|cos(yaw)| of full length (the whole burst is drawn three times, rotated
  120 deg about (1,1,1), which breaks some of the cos symmetry). The rays are white, short and gone in ~13 frames.
  Realistic: a couple of bits per ray.
- The enemy's hit-reaction script may draw too (Bowser: `RandInt(80)`, `RandInt(60)` about 35 frames after the
  hit), but that depends on the enemy.
- Count: fixed per hit, but a missed action command or a miss changes the number of hits/fireworks.

**Tattle** (`EVS_Move_Tattle`)
- Script: `OpenTattleWindow` -> `fx_tattle_window` (`tattle_window.c`: no `rand_int`); `SetCamEnabled(CAM_TATTLE)`,
  fixed perspective and viewport; `GetTattleCamPos` is pure arithmetic on the target's size and the
  `bActorOffsets` table; `GetTattleMessage` / `save_tattle_flags` touch no RNG. So the zoom, the window and the
  enemy picture in it are seed-independent.
- `ActorSpeak` prints the tattle text in `MSG_STYLE_TATTLE`, which sets `MSG_STATE_FLAG_800000` (speech sounds).
  `msg_play_speech_sound` (msg.c:619) then draws **`rand_int(15)` per printed character** for the blip volume
  (78..93% of the base). This is skipped when the printer is fast-forwarding (`MSG_DELAY_FLAG_2|4`), so the count
  depends on the text and on how the runner advances it. The README's 124 x `rand_int(15)` in the B-held hallway
  scene is the same mechanism. Audio volume steps of ~0.8 dB under the BGM are not readable.
- No text effect in tattles uses the `MSG_FX_FLAG_SHAKE` / `SIZE_JITTER` / `BLUR` paths in `msg_draw.c`. Those
  do draw gRandSeed per character per frame, and so would be a readout in any message that uses them.
- **Verdict: no help. It costs RNG steps the runner cannot see, and its count is only fixed if the text input is.**
  The status-bar coin keeps running behind it, so Tattle is no better than standing still.

**Charge** (`EVS_Move_Charge`, Super)
- `PlayChargeFX` = `fx_energy_in_out(6, x, y+15, z, scale, 45)`, called twice (scales 1.2 and 0.8, 3 frames apart).
  This is byte-for-byte the same call as Mario's Jump/Hammer Charge (`world/common/todo/UnkMoveFunc2/3.inc.c`:
  type 6, 45 frames, 1.2 / 0.8). Per effect at init: 1 x `rand_int(360)`, then 10 x (`rand_int(10)` speed,
  `rand_int(10)` phase) = 21 draws. Then every ray re-picks `unk_3C = rand_int(359)` each time its 10-frame cycle
  wraps, for ~46 updates. **~110 draws per Charge**, as measured for Mario in the README.
- Also `EFFECT_ENERGY_ORB_WAVE` (no rand) and `fx_stat_change` (no rand).
- Camera `BTL_CAM_PARTNER_GOOMPA` is a close-up on Goombario, so the rays are at least as large as Mario's.
- Practical: 1 FP and a partner turn. It only matters if the route has Goombario; the Hallway route has Lakilester.
  Mario's own Charge already gives the same readout.

### Bombette
**Body Slam** (`EVS_Attack_BodySlam`): no rand in the script. The body-slam action command (`action_cmd/body_slam.c`)
has no rand. One firework on a damaging hit (6-11 draws). Rank 7 in the table.

**Bomb / Power Bomb** (`EVS_Attack_Bomb`)
- `PlayExplosionFX` spawns `fx_smoke_ring` and `fx_explosion`; neither has any rand. `EFFECT_RED_IMPACT` has no
  rand. Nor do `action_cmd/bomb.c` or `ShakeCam`. The big explosion is seed-independent.
- Each damaged enemy gets a firework (`DAMAGE_TYPE_BLAST` is not fire/shock/water). Power Bomb hits every enemy,
  so it gives one firework per enemy: 1 on Hallway Bowser.
- The fuse timing is fixed (45 / 50 frames + 6 / 12 shakes), so the draw count is deterministic apart from the
  per-frame step and the coin.

### Sushie
**Belly Flop** (`EVS_Move_BellyFlop`): `DAMAGE_TYPE_JUMP`, no rand, no effects. One firework per hit.

**Squirt** (`EVS_Move_Squirt`)
- `EFFECT_SQUIRT` type 0 has no rand inside (`squirt.c`). The `rand_int(10)` stream-width draw is only in
  `PlaySquirtFX`, which is used by Water Block.
- The hit is `DAMAGE_TYPE_WATER`, so `show_damage_fx` spawns `fx_water_splash(0, ..., 1.0, 24)`: 20 droplets, each
  with velocity (`rand_int(10)-2`, `rand_int(10)-5`, `rand_int(10)-5`). That is **60 draws, 11 values each**. The
  droplets are drawn in billboard space, so vx/vy map straight to screen x/y (vz only changes depth slightly). The
  drift is damped by 0.98/frame, and y also gets -0.1/frame gravity.
- Visibility is the problem. Each droplet samples the framebuffer (`gDPLoadMultiTile` of `nuGfxCfb_ptr`) and is
  drawn as a pale cyan refraction blob, alpha x0.98 and scale x0.9 every frame (2.0 -> 0.7 in 10 frames). It is
  low contrast and short-lived. Code-read only.

**Water Block** (`EVS_Move_WaterBlock`, Super)
- At the cast, only if the "three chances" action command scores > 0 (otherwise it jumps to `Label(10)` and draws
  nothing):
  - `PlaySquirtFX`: 1 x `rand_int(10)`, the arc's width multiplier `unk_50` = 1.0..1.9 (`squirt.c` scales the
    stream's cross-section by it). A wide water arc, so plausibly ~3 bits.
  - `EFFECT_WATERFALL`: 12 x `rand_int(10)` (velocities -1.00..-0.91; differences of <=0.09/frame, hard to see).
  - **5 x `EFFECT_SPARKLES` type 4**, 5 frames apart. Each makes 8 sparkles with `rand_int(50000)`,
    `rand_int(8000)`, `rand_int(359)` and `rand_int(50)` (the last is discarded: `rand_int(50)/1000` is integer 0).
    That is **32 draws per burst, 160 in all**. Sparkle *k* sits at (r1*sin a, r2*cos a), with r1 in [0,50] and
    r2 in [0,8] world units (i.e. +-~95 px by +-~15 px at camera distance 277). All sparkles then fall at the same
    rate. Sparkle *k* becomes visible at frame 2k of its burst and lasts 21 frames, so each one can be identified
    by when it appears.
  - `PlayWaterBlockFX` -> `fx_water_block(CREATE)`: no draws at creation.
- **Persistent bubbles** (`water_block_update`): 4 bubbles. Each, when it respawns, draws x-drift
  (`rand_int(10)-5)*0.2`, rise speed `rand_int(10)+2`, size `rand_int(10)+1`, and on leaving the top a respawn
  delay `-rand_int(10)-1`. That is **4 draws per cycle of ~25-35 frames, for every frame the block exists** (1-3
  turns, including enemy turns and probably the menus; offscreen at `NPC_DISPOSE_POS_Y` when decorations are
  hidden, but still drawing). As a stream that is ~0.5 draws/frame. The bubbles are small translucent shapes inside
  the blue block, so contrast is low. Unverified. The draw schedule is seed-determined (no input dependence).
- When the block expires: `fx_water_block(DESTROY)` (on its own end: 2 x 20 x 3 splash draws) plus three
  `fx_water_splash` (2 x 60 + type 1 60).
- Practical: 3 FP and a Super-rank Sushie. Sushie is not in the route party, so this is only of academic interest.

### Lakilester
**Spiny Flip** - unchanged from README: no rand in the script. `EFFECT_ENERGY_IN_OUT` type 0 for the aim
(`80*DT` frames; 11 parts, rays cycle every 20 frames) gives 38-66 draws of faint streaks, and the variable count
depends on aim time. A firework is spawned on the hit.

**Spiny Surge** (`EVS_Move_SpinySurge`)
- Per thrown spiny, `ThrowSpinyFX`: `rand_int(140)+10` = rest x, `rand_int(80)+10` = rest y (world coordinates, z
  fixed at 20), then `throw_spiny_main`: `yaw = rand_int(360)` and `rotSpeed = rand_int(10)+5`. In the logs these
  are callers 0x80238AD0, 0x80238AE8, 0xE00C819C and 0xE00C81B4, always in that order, **4 draws per spiny**.
- Motion (`throw_spiny_update`): a straight line to (x, y, 20) over 30 frames while spinning `rotSpeed` deg/frame
  (rotation about the screen axis, `guRotateF(yaw, 0, 0, 1)`). Then a 7-frame squash at the rest point
  (yaw -= 40/frame), then a fall with gravity to y = 14.3. Camera distance is 400 (~1.35 px per world unit at 320
  wide), so x spans ~190 px and y ~108 px. A scale-1.5 spiny sprite's centroid is good to well under a pixel in
  S-Video luma, which gives about log2(141) + log2(81) = 13.5 bits from position alone. Spin speed is a further
  3.5 bits (30 frames x 1 deg/frame steps). Spin phase is 0-8 bits, depending on the spiny sprite's symmetry.
  On real footage the rest points overlap and some leave the screen, so read the launch tracks (see Emulator
  checks).
- The number of spinies is set by the stick-flick mash (`action_cmd/spiny_surge.c`: flick left, return to neutral).
  It is not fixed, but every spiny is on screen, so the page just counts them. Throws are 6 frames apart.
- Then one hit (all enemies) with a firework per damaged enemy.
- Practical: 4 FP, Lakilester's turn on Hallway Bowser T1 instead of Spiny Flip. Whether its damage fits the route is
  a separate question (Spiny Flip is the planned T1 move).

**Cloud Nine** (`EVS_Move_CloudNine` -> `cloudNine_normal`/`_immobile`)
- After the action command, a thread spawns 10 `EFFECT_FLOATING_CLOUD_PUFF` one frame apart. Each puff is at Mario's
  position + (`RandInt(40)-20`, `RandInt(30)-15`). **Exactly 20 draws**, also when the action command fails
  (`LVarA = 0`): only `SpawnCloudNineFX`/`ApplyCloudNine` are skipped.
- `floating_cloud_puff` has no rand. It rises 0.6/frame on a fixed scale curve, white, and lives 20 frames.
  Camera distance is ~275 at that point (~2 px per world unit), so each puff is offset over +-40 px by +-30 px, one
  new puff per frame. The page can difference consecutive frames to isolate each new puff. The theoretical limit
  is log2(41) + log2(31) = 10.3 bits per puff (103 bits in all). Puffs are soft, overlap each other and Mario, so
  assume roughly half of that.
- Once Cloud Nine is up, each enemy attack also rolls `rand_int(100) < 50` (`1A5830.c:181`). A dodge is a visible
  ~1 bit per attack (seen as caller 0x802774B0 in the log, 1 per attack).
- Practical: 4 FP. It uses Lakilester's turn, but it is a defensive buff, so a route would not spend that turn
  anyway unless it wants Cloud Nine.

### Ultra-rank moves (brief)
- **Multibonk**: `AdjustMultibonkChance`: `rand_int(100)` per bounce against a shrinking chance (it is never reset
  between uses: `@bug`). The number of bonks is a visible outcome, ~1 bit per bounce, plus a firework per hit. The
  count is variable.
- **Mega Bomb**: like Power Bomb, bigger explosion (no rand); one firework per enemy.
- **Tidal Wave**: `rand_int(4)` per hop (`bounceDivisor`) plus splashes; the count depends on the button prompts.
- **Hurricane**: `rand_int(10)+11`, `rand_int(1000)` and, per cloud, 2 x `rand_int(100)` + 2 x `rand_int(1000)` for
  `fx_moving_cloud`. Lots of draws, and a blow-away roll `rand_int(99) < actionQuality` per enemy.

## Emulator checks (JP, `partner_moves_diff.py`, boss_2302_route_menu.st, Lakilester at Super rank)
DIAGNOSTIC RAM write: gRandSeed (both words) set at Mario's first menu; Mario does Charge, Lakilester the move.
Every `rand_int` is logged per frame with max and caller (the status-bar coin, `rand_int(100)` at 0x80146D54,
is ignored below).
- **Spiny Surge**: 10 spinies, one every 6 frames (frames 72-126 after picking the move). Each throw logs exactly
  (140, 0x80238AD0), (80, 0x80238AE8), (360, 0xE00C819C), (10, 0xE00C81B4). Then 6 x (359, 0xE00861EC) firework
  at the hit (frame 152), and Bowser's `RandInt(80)`, `RandInt(60)` at 217. Same counts for 2 seeds.
- **Cloud Nine**: 10 consecutive frames (225-234) of (40, 0x802D46E0) + (30, 0x802D46E0), with no other draws
  in between. Then on Bowser's attack: (100, 0x802774B0), the dodge roll, followed by a firework.
- **Screenshot diff** (glide64, 640x480, seed 0x12345678 vs 0x9ABCDEF1, pixels differing by more than 24 grey levels):
  - Spiny Surge: 0 differing pixels until the first throw (frame 73). From then on, 1.7k pixels per frame, growing
    to **30-41k per frame over frames 110-160**, with the bounding box spreading to the right screen edge
    (x = 616 of 640). Still 3-10k at frame 200, while the spinies bounce and pile up on the enemy.
  - Cloud Nine: 0 differing pixels except during **frames 226-252**, confined to a ~140x120 px box around Mario:
    165 px on the first puff, then 4.7-7.5k per frame through frame 244, fading out by 253. Nothing else in the
    frame depends on the seed.
- **Real console S-Video clip** (Duplighost fight, 1280x720 60 fps capture, Spiny Surge at 100%; not committed):
  - The game picture spans ~940 capture px for 320 game px (x2.9). A spiny is ~100 capture px across (~34 game px),
    red with silver spikes on a dark blue/grey wall: high contrast, with sharp spike edges even through S-Video.
  - Distinguishable: each spiny leaves Lakilester alone, 6 frames after the previous one, and the first ~10 frames of
    its straight 30-frame flight are well separated. That launch line alone gives the direction and speed to
    (x, y). Spike rotation is clearly visible, so spin speed (5-15 deg/frame) is readable. The spike count looks
    like ~8-fold symmetry, which would leave spin phase modulo ~45 deg.
  - Problems: (1) the "100%" burst popup sits right over the launch area during a full mash; (2) at the rest
    points, 6-12 spinies overlap heavily, and those with large x leave the right screen edge; (3) after the fall
    they bounce into a pile on the enemies. So read each spiny from its launch track, not its rest point. Expect
    ~8-12 usable bits per spiny rather than the ~20 theoretical. With 10 spinies that is still ~80-120 bits, far
    above a lock.
  - **Duplighost disguise**: the pulsing ring is `EFFECT_GATHER_ENERGY_PINK` (`effect_rand_int(360)`), and the smoke is
    `EFFECT_BIG_SMOKE_PUFF` (`effect_rand_int(6)`). **Neither touches gRandSeed.** What does is the Duplighost's
    decision in `EVS_TakeTurn`: `RandInt(1000) < 600` to copy the partner. That is a visible ~1 bit per
    Duplighost turn (copy or attack).

## Not verified
- Goombario's Charge and Tattle in the emulator (Goombario is in the party at level 0 in this save, so it has no
  Charge). Charge is the same call as Mario's verified one.
- Sushie's Squirt and Water Block (Sushie is not in the save). Water Block bubble visibility, and whether the block is
  drawn during the battle menus, are unknown.
- A real S-Video capture of any of these. The bit estimates are geometry plus the README's S-Video model, not
  measured.
- The spiny sprite's exact rotational symmetry (looks ~8-fold on the clip), which limits the spin phase.
- A detector for any of these. The Spiny Surge clip shows the spinies are visible and separable at launch, but
  nothing has been fitted to it.
