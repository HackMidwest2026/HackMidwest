# Kooper skip bot (Paper Mario, JP 1.0)

A bot that searches for out-of-bounds routes in **nok_14** (Pleasant Path, "Path to Fortress 1"): get from the left loading zone to the right one without hitting the switch that raises the bridge, using loading zone storage (LZS) jumps.

It runs the real game in a headless mupen64plus, reads Mario's state from RAM using addresses from the [pmret/papermario](https://github.com/pmret/papermario) decomp, and tries jump sequences many times faster than real time.

No ROM or savestates are included. You need your own *Mario Story* (J) ROM. The decomp's JP baserom has SHA-1 `b9cca3ff260b9ff427d981626b82f96de73586d3`.

## The room

![nok_14 collision](nok14_map.png)

Collision read from RAM after the room loads (`dump_collision.py`, `draw_map.py`). The camera looks toward −z, so the top of the image is the back of the room.

| collider | what it is |
|---|---|
| 5 `deili1` | left exit floor (to nok_13), x −970…−870, y 75 |
| 21 `deili2` | right exit floor (to nok_15), x 450…550, y 0 |
| 4, 20 `deilit`, `deilit2` | walls behind each exit, disabled on load (`COLLIDER_FLAGS_UPPER_MASK`) |
| 12 | wall at x=−100 that stops Mario reaching the unbuilt bridge. Kooper's shell passes through it (`IGNORE_SHELL`). |
| 14 | floor across the bridge gap, x −100…100, y 0 |

Every wall in the room is vertical and every floor is flat. So an out-of-bounds route can only use pieces of floor that extend past the walls, which several do.

## How loading zone storage works (from the decomp, confirmed in the emulator)

1. Both exits are `TRIGGER_FLOOR_ABOVE` triggers (`src/trigger.c`). They fire as soon as the floor under Mario's shadow (`gCollisionStatus.floorBelow`) is the exit collider, even in midair. The trigger starts `EVT_EXIT_WALK_NOK`.
2. That script first calls `UseExitHeading` (`src/evt/player_api.c`). It blocks until `can_trigger_loading_zone()` (`src/7BB60.c`) is true, which needs Mario's action state to be idle, walk, run, tweester or spin. Until then the exit is **stored**.
3. Each frame, `step_game_loop` runs scripts *before* the player update. So the exit fires on the first frame that **starts** with Mario grounded.
4. Landing:
   - **Stick held:** `player_handle_floor_collider_type` goes straight to walk/run and the frame ends grounded, so the exit fires on the next frame.
   - **Stick neutral:** the landing frame ends in `ACTION_STATE_LAND`, which doesn't count as grounded.
5. On the next frame, the LAND update falls through to idle. `phys_update_action_state` runs the idle update in the same frame (its `do … while (ACTION_STATE_CHANGED)` loop), and idle checks for a jump. Pressing A on that frame makes Mario jump without ever ending a frame grounded, so the exit stays stored.

So each LZS jump needs a **neutral stick on the landing frame** and **A on the next frame**. The JP game reads input one game frame late, so with the inputs as sent to the emulator, A goes on the frame after the one where Mario is first seen in LAND.

If Mario walks or falls off the collision, the cubic gravity integrator eventually flips sign and launches him upward, and the game puts him back at his last landing spot. The stored exit survives this.

## How the bot works

- **`harness.c` + `emu.py`:** a mupen64plus core driven one rendered frame at a time from Python. Savestates are synchronous and uncompressed, and RDRAM is read directly. The game renders twice per game frame, so the bot always steps two callbacks at a time. `harness.c` doubles as the input plugin.
- **`mupen64plus-core-headless.patch`:** two changes to mupen64plus-core (commit `ba95bab`):
  - raise the RDP "frame done" interrupt itself, since no video plugin runs and the game would otherwise wait forever
  - make savestates synchronous and uncompressed
- **`make_state.py`:** boots, starts a new file, and redirects its first map load to nok_14 entry 0 with story progress set to "arrived at Koopa Village". It then saves `states/nok14_start.st`.
- **`lzs.py`:** the LZS jump primitive. From a "ready" state (Mario just landed with the exit stored), it jumps with a stick direction and an A-hold length. It runs once to find the landing frame, then replays with a neutral stick on that frame. The result is a new ready state, `exit` (the stored exit fired), or `void` (Mario never landed).
- **`explore.py`:** a Go-Explore search over ready states, using 4 worker processes.
  - **Cells:** (floor collider, x/12, z/12, y/30).
  - **Each try:** pick a cell (weighted toward ones tried less often) and try a random jump. There are 32 stick angles, 3 stick strengths and 6 A-hold lengths, plus a jump in place.
  - **Archive:** any landing in a new cell is kept, with the shortest input path that reached it. States are stored as XOR diffs against the first ready state, about 136KB each.
  - **Goal:** the floor below Mario becomes `deili2` (collider 21) while the nok_13 exit is still stored.

## Running it

```sh
# 1. build mupen64plus-core with the patch
git clone https://github.com/mupen64plus/mupen64plus-core && cd mupen64plus-core
git checkout ba95bab && git apply ../mupen64plus-core-headless.patch
make -C projects/unix all NETPLAY=0 OSD=0 NEW_DYNAREC=1 && cd ..
# 2. build the harness (needs mupen64plus-rsp-hle, e.g. from the distro's mupen64plus packages)
gcc -O2 -shared -fPIC -o harness.so harness.c -Imupen64plus-core/src/api -ldl -lpthread
# 3. make the start state and search
export PM_ROM=/path/to/mario-story-jp.z64
python3 make_state.py
python3 explore.py runs/r1 6        # run directory, hours
```

`M64P_CORE`, `M64P_RSP` and `PM_TMP` (scratch directory, default `/dev/shm/pmbot`) override the default paths. A `.n64` (byte-swapped) dump has to be converted to `.z64` first.

## Hammer clip (no LZS): what applies in nok_14

`make_state2.py` makes a start state closer to a real run: boots, hammer and Goombario, entering nok_14 by walking in from nok_13. `walk.py` steers Mario through waypoints and stops if a battle starts.

**Why a push during the hammer clips:** in `ACTION_STATE_HAMMER`, `phys_update_lateral_collision` (`src/7BB60.c`) tests walls only in the direction Mario is facing. `npc_do_player_collision` (`src/npc.c`) moves Mario's position directly, with no wall check. So an NPC pushing Mario backward or sideways while he hammers can move him through a wall.

**Why it doesn't work here:**
- `npc_do_player_collision` skips partners and any NPC with `NPC_FLAG_IGNORE_PLAYER_COLLISION`.
- When enemy NPCs are created (`src/encounter.c`), the game sets that flag on every enemy that isn't `ENEMY_FLAG_PASSIVE`.
- Everything that moves in nok_14 is a non-passive enemy: Koopa Troopa, Spiked Goomba, Paratroopa. The only passive NPC is hidden and also ignores player collision.
- In the emulator, the Spiked Goomba chases Mario (2.5 units/frame) and stops at touching distance without moving him. It then attacks.
- `pushVel` is only set by moving platforms and conveyors in other areas, and `overlapPushAmount` is never set.

**Useful target if Mario can get through the wall at x=−100 some other way:** the floor across the bridge gap (collider 14) is solid while the bridge is down. Placing Mario on it and holding right walks him onto `deili2` and loads nok_15. So a clip anywhere through that wall (x=−100, z −100…−20) is a Kooper skip.

## Clip searches without LZS (results)

- **`explore_clip.py`:** random stick/jump/spin/hammer segments, Go-Explore style. On every frame it checks whether Mario's movement crossed a solid wall taller than a step.
  - First run, whole room: about 38,000 attempts.
  - Second run, spots within 40 units of a solid wall east of x=−480: about 162,000 attempts.
  - No clips.
- **`corner_sweep.py`:** an exhaustive sweep at the two corners of the bridge wall, (−100, −100) and (−100, −20).
  - **Start positions (80):** Mario settled into each corner from several directions, and run-ups from 20, 40 and 80 units at 10° steps across each corner's wedge.
  - **Inputs:** every stick angle (1° steps when settled, 2° for run-ups), at 4 stick strengths, with walk, spin, jump or hammer on the first frame.
  - **Battles:** enemy contact is switched off with the game's own `debugEnemyContact = DEBUG_CONTACT_CANT_TOUCH`. Enemies can't push Mario, so this changes nothing about collision.
  - **Result:** 262,080 attempts with no clip from in bounds. All 109 hits came from two run-up starts, at 80 units and 127°/137°. Those placed Mario on floor that sticks out past the front wall, so he was already out of bounds before any input. From there he walked off the floor and drifted under the map.
- **`probe_start.py`:** replays every input from one sweep start and lists frames where Mario is east of x=−100.

## Rip Cheato's room (tik_15): clipping past the bombable wall

The room behind the blue house pipe in Toad Town (Toad Town Tunnels B3). The bombable wall is collider 11 at x=−250, z −50…50. Behind it is the exit floor to tik_14 (collider 12).

- **Start state** (`make_state_tik15.py`):
  - **Why the detour:** tik_15's code searches for the partner NPC with `get_npc_unsafe`, which loops forever if he doesn't exist, so the room hangs about 4 seconds after loading without a partner.
  - **How:** the script loads the nok_14 Goombario state, rewrites that map's left exit, `GotoMap("nok_13", 2)`, in RAM to `GotoMap("tik_15", 0)`, and walks through it.
- **Rip Cheato** is passive and doesn't ignore player collision, so unlike the enemies in nok_14 he does push Mario. But he never moves and stands 170 units from the bombable wall. A push only moves Mario to 25 units from his center, so it can't carry Mario through any wall.
- **`rooms.py`** holds the per-room settings: start state, goal floors, goal box, goal map and corners. Run the searches with `ROOM=tik15`.
- **`corner_sweep.py`** (`RING_STEP=15 ACT_STEP=3 MAGS=80,40,15`):
  - **Where:** the two seams where the bombable wall meets the rest of the west wall (same plane, separate colliders) at (−250, ±50), and the two outer corners of the low ledges at (−230, ±50).
  - **Size:** 192 in-bounds start positions, 391,680 attempts.
  - **Result:** no hits. 16 run-up starts landed behind the wall on the exit floor and were skipped.
- **`explore_clip.py`:** 99,087 attempts from 5,825 spots next to walls. No clips and no exit to tik_14. The pipe to Toad Town was taken 17 times, which is normal and ignored.
- **Harness fix:** `h_load` now reports when a savestate load didn't happen. The sweep also checks Mario's position after every load, after one load in a worker silently failed and produced a false hit.

## Spin-jump landing at the north corner (nok_14)

**The speed boost.** Jumping out of a spin keeps the spin's `curSpeed` (8.0) while airborne, where Mario only moves 4 units/frame. On the landing frame, run movement uses the stored 8.0 plus the stick's 0.547, so Mario moves **8.547 units in one frame**; normal running is 4.547. Measured in the emulator, the landing frame is 8.547 whichever spin frame the jump starts on.

- **`spin_land_sweep.py`:**
  1. **Landings near the corner:** 15,120 spin-jump setups. Start points across the corner's opening, spin direction toward the corner ±30°, jump on spin frame 1–8, five in-air steering choices. 7,552 landings ended within 22 units of the north corner, 579 of them in distinct spots.
  2. **Landing-frame sweep:** from each, every stick angle (1°) at 3 strengths for the landing frame and 7 frames after.
  - **Result:** 625,320 attempts, no clips.
- **`spin_land_depth.py`:** replays the 120 landings closest to the corner at every angle and records how far east Mario gets beside the bridge wall (−100 < z < −20). The best is exactly **x = −113.000**, Mario's 13-unit radius from the wall, the same as walking into it.
- **Why the speed doesn't help:** moves faster than 4 units are wall-tested in sub-steps of 4 and then the remainder (`speed - 4` = 4.547). Each sub-step is tested over Mario's full radius (13), so even 8.547 never moves him further than the test covers in one go. Afterwards `collision_check_player_intersecting_world` pushes him back out to the radius.

## North corner landing grid (nok_14)

`corner_grid.py` takes one real airborne state from a spin-jump (`curSpeed` 8.0, one frame before landing) and moves only Mario's x and z to every point of a 0.5-unit grid around the north corner: x −122…−104, z −114…−94, 1,517 spots. It skips the first 13 units around the bridge wall. From each spot it plays the landing frame and 5 more frames with every stick direction from straight up (away from the camera) clockwise through right to straight down, in 2° steps, at strengths 80 and 40.

![corner grid](fig7_corner_grid.png)

- **The corner is a thin wedge.** The short lip wall (−110, −102)–(−100, −100) and the diagonal wall to (−52, −118) meet at a point at (−110, −102). Between them is solid.
- **Every landing spot outside that wedge stays in bounds.** The 37 spots that push Mario east onto the gap floor (collider 14) all start *inside* the wedge. So do 3,800+ "crossed wall" hits, which are Mario being pushed back out of a wall he was placed in.
- **No real spin-jump gets there.** Of the 579 real landings from inputs (blue), the closest is 3.46 units from the wedge's walls, outside it. The grid shows that being outside is enough to stay in bounds. To clip here, something would have to put Mario's center inside the wedge first. The landing frame's 8.547 move doesn't, because each 4-unit sub-step is wall-tested.
- `grid_figure.py` draws the figure from `grid.json` and the real landings.

## Why the Jade Jungle log clip works (jan_04), for comparison

`make_state_jan04.py`, `dump_collision_jan04.py`, `t_logclip*.py`, `record_logclip.py` and `make_logclip_video.py` reproduce and explain the known log clip (`log_clip_explained.mp4`).

1. The wall at x = −150 is underground-only for z < 30 and full height for z ≥ 30. Mario's wall rays (feet and feet + 27.75) pass over the low part, so he can stand on the line x ≈ −149 at z just under 30.
2. Landing on the log's sloped side (collider 26) shoves him +2.3 in z, with no wall check. His center is now behind the full-height section.
3. Push-out then sends him to the wrong side: x = −163, then z = 43, out of bounds.

With collider 26 disabled the shove disappears and there is no clip. nok_14 and tik_15 have no sloped floor triangles at all (jan_04 has 51), so this mechanism doesn't exist in either room.

## Blue House Skip (mac_02, Toad Town south)

Getting into the locked blue house (the Odd Key door) by clipping in at its front-right corner. `make_state_mac02.py` makes the start state (same exit-redirect trick as tik_15) and `dump_collision_mac02.py` dumps the collision.

**The house's collision** (collider 45):
- **The walls are two-sided and lean outward.** The east wall goes from x = −397 at the floor (y 20) to x = −389 at y 105. The front wall's right edge leans out the same way.
- **The top band is one-sided.** The band from y 105 to 120 and the roof ceiling (collider 46) face into the house only, so from outside they don't block anything.
- **The exterior has no other walls.** The only other piece is the door.

**Why it works:**
1. **The leaning wall is a floor from the inside.** A two-sided triangle can be hit from either side. A downward ray that starts on the inner side of the leaning east wall's plane, somewhere above the floor, hits the wall's inside face, and the game treats it as floor. Mario's floor check casts five downward rays: one at his center and four 7.28 units away (`player_raycast_below`). In the notch at the corner (just east of the front wall's edge, z > −147), one of those rays reaches z < −147, under the leaning wall. Walking in gives `STEP_UP` (action 34, about +11). Falling in lands him on the wall face at the height where the plane crosses his x (y ≈ 39 at x = −395.2).
2. **Snap up and hover.** Jumping off the wall face, Mario reaches x ≈ −390.2. Each time he falls, the floor check hits the face higher up (y 91.9) and snaps him up to it. This repeats every 5 frames, so he hovers at the corner (y 86–92) for as long as nothing changes.
3. **Over the top.** Holding up and slightly right (world angle 274–278° at full tilt, 279–294° at half tilt) moves him 1–2 units east, so the next snap puts him at y ≈ 101–107. That's above the two-sided part of the front wall. Moving up (−z), he passes the one-sided top band. The front wall now pushes him to the inside (z = −160), and he falls onto the block inside the house (collider 53, y 50).

**Searches:**
- **Walking or spinning into the corner** (`house_probe*.py`): about 160,000 tries, 5,300 step-ups, none inside.
- **Single jumps from a standing spot** (`house_simple.py`, `house_stageA.py`, `house_eastwall.py`): about 380,000 jumps, no wall-face landings. The landing needs the speed of a spin-jump.
- **`house_explore.py`** (Go-Explore at the corner) found the wall-face landing. Spin right along the house front, past the corner. Jump holding down-left lightly; the spin speed carries Mario back into the notch, and he lands on the face at y 39.
- **`house_hover.py` / `house_hold.py`:** from the hover, 121 of 7,200 single held directions get in, at every phase of the 5-frame loop. The hover lasts indefinitely, so this last input has no timing.
- **`house_stageB.py`:** from that wall-face landing, the jump that reaches the hover is narrow. Stick 296–300° at low strength for the first 6 frames, then up-slightly-right.
- **`record_house.py`** renders `blue_house_clip.mp4` and `blue_house_clip_slow.mp4`.

### A setup a human can try (`house_setup_tol.py`, `blue_house_setup.mp4`)

World angles below assume the default camera: 0° = right, 90° = toward the camera (down), 180° = left, 270° = away (up).

1. **Start:** walk up into the house front a few units left of the corner (x = −406, z = −134).
2. **Spin:** spin (Z) holding up-right (world 340°). Mario slides along the house front, round the corner, and out to about (−353, −162).
3. **First jump:** jump on spin frame 9, holding down-left (world 150°). Let go of the stick after 10 frames, before landing; holding it into the corner makes the front wall push him off the notch. The spin speed carries him back round the corner, and he lands on the leaning wall face at about (−394.6, 45, −140.1).
4. **Second jump:** jump again holding a light up-right (world 304° at 30% tilt) for 6 frames. Then hold up, slightly right (276°, full tilt). He snaps up the wall to y 100.7, gets pushed inside, and lands on the block inside and then the house floor (collider 47).

**How forgiving it is:** over 50,400 variations of steps 1–3 (start x −426…−400, spin angle 316–344°, jump on spin frame 6–10, air stick angle and strength, release frame):
- 1,783 (3.5%) land on the wall face.
- 516 (1.0%) end up inside, using one of 5 second jumps.

The best setups still only have about 1 in 6 of their neighbours working (start ±4 units, spin ±4°, jump ±1 frame). The second jump is the narrowest step: from one landing, only about 5° of stick angle at light tilt works. So the clip is reproducible, but it isn't consistent yet. The hover (when the second jump reaches it) removes the timing from the last input.

### Low entry through the bottom of the corner (`blue_house_low.mp4`)

The TAS doesn't go over the top: Mario rises only about 10 at the corner and is inside. This route does the same, and stays below y 32 the whole way.

**Why normal movement can't get in.** The push-out (`collision_check_player_intersecting_world`) casts four rays at Mario's height (y+10.6 on the ground, y+1 in the air). If those hit nothing, it casts them again 27.75 higher. The front wall's edge leans out a little more than the east wall (6 in 61 against 8 in 85). So at that higher pass, the front wall always reaches past the east wall's line. `house_capture.py` shows that once Mario's center is past z −147.25 and west of the east wall's line, the push-out takes him inside. But every move that crosses the front wall line west of the east wall's line is pushed back out first. Searches that only use normal movement and jumps never get closer than 0.26 units:
- `house_explore_low.py`
- `house_low_sweep.py` (86 wall-face landings × 864 inputs)
- `house_hug.py`
- `house_capture_search.py` (about 100,000 tries)

**What does get in: `STEP_UP`.** Step-up skips the movement test: it moves Mario 3 units along the stick direction from the frame it triggered. Its push-out also runs only the low pass. Step-up triggers when one of Mario's five floor rays (cast from 18.5 above his feet, 7.28 units from his center) hits the inside face of the leaning east wall at least 6 units up. That happens in a narrow strip of the corner notch (x about −395.96 to −395.26, z from −139.7 back to the wall line). Mario can't stand in that strip, because the higher push-out pass sees the front wall there; he can only pass through it while moving.

**Where it works.** `house_stepgrid.py` places Mario on every stable spot in front of the corner (0.1 × 0.25 grid) and tries every stick direction:
1. Mario stands at x −395.2 (the last column east of the strip) with z between −141.5 and −140.
2. Holding up, slightly left (raw stick −8, 80), the first frame's run takes him 5.4 units up to (−395.38, −146.44), inside the strip.
3. Step-up triggers facing straight up. Its 3-unit move takes his center past both wall lines, and the push-out puts him at (−408.1, y 29, −160).
4. He drops onto the house floor (collider 47).

Mario's sprite is still drawn in front of the wall on the first frames inside. That's why in the TAS he seems to land next to Kooper and then vanish.

`house_lowwin.py` maps how wide this window is (starting x and z, stick direction). `record_house_low.py` renders the video.

**How forgiving the low entry is:**
- **From a standstill** (`house_lowwin.py`): Mario has to start with x between −395.24 and −395.18, a window 0.06 units wide, and z between −141.5 and −138.5. He also has to hold exactly raw stick (−8, 80). In total, 15 of about 136,000 tries worked.
- **Holding one direction from a rough spot** (`house_lowhold.py`): no successes in about 20,000 tries.
- **Sliding along the house front and then switching the stick** (`house_slide.py`): one combination works, with a 1-frame switch window. That's sliding with raw (12, 80), switching to (−8, 70) at x −395.07.
- **Single-frame stick taps** move Mario at least 2 units, so they can't be used to line him up.

So the low entry is real but TAS-precise. Lining Mario up to within 0.06 units is the hard part.

**Simple held directions, with Speedy Spin equipped** (badge 0x11F written to the first equipped-badge slot; spin speed 10.8):
- **Close to the working spot** (`house_simplehold.py`): x −397…−393 in 0.02 steps, z −146.9…−120.4 in 0.5 steps, every standable spot. Holding full up, up-left or left, plain or with a spin on the first frame, got in 0 times.
- **Long approaches** (`house_simplehold2.py`): 4,004 up-left starts placed on the 45° line through the step-up strip, and 2,204 left starts at every z from −147 to −136. Plain or spinning, 0 got in.

**Why:** step-up only triggers in the strip x −395.96…−395.26. At any x in that strip, the front wall stops Mario at z −134 before he reaches it, so straight up never gets there. He has to start just east of the strip (x ≥ −395.24) and drift about 0.1 left during the final 5.4-unit frame. That's the raw stick (−8, 80), roughly 6° left of up. Left and up-left reach the strip moving too far sideways, so the step-up's 3-unit move doesn't carry him past z −147.25.

**Gentler sticks** (`house_walkwin.py`): 96 stick positions from a light walk (y = 10) to full tilt (y = 80), each with x from 0 to about 35% left. Every standable spot with x −395.30…−394.60 (0.01 steps) and z −146.9…−130.4 (0.5 steps) was tried, 198 hits in all. A walk at (−5, 20) is the most forgiving:

| stick | start x | start z | hits |
|---|---|---|---|
| (−5, 20) walk | −395.25 … −395.13 | −145.4 … −140.9 | 78 |
| (−7, 60) | −395.25 … −395.18 | −142.4 … −138.4 | 48 |
| (−8, 80) | −395.25 … −395.18 | −142.4 … −138.4 | 48 |
| (−6, 40) | −395.25 … −395.22 | −143.9 … −140.9 | 24 |

In every case the clip happens on the first frame. Very small x values don't register. On open ground, (−1, 10), (−3, 10) and (0, 10) all walk the same direction, about 2.8° left of straight up (the camera is turned slightly). That's the same as pure up and too straight. The entry needs Mario moving about 5–7° left of up.

### Looking for an RTA setup with up/down/left/right only (`house_rta.py`, `house_rta_local.py`)

Moves allowed, starting from the left loading zone entrance:
- **Run until stopped:** hold up, down, left or right at full tilt until a wall stops Mario. The result doesn't depend on timing.
- **Spin:** press Z holding one of those four directions, then let go.

From a standstill a spin always travels the same whole number of units: right +41, left −81, up −25, down +48. With Speedy Spin it's +41.4, −84.6, −30.6 and +48.4. After every move the search tries the final inputs: pure up at 3 strengths, and up with a slight left tilt.

**Results:**
- `house_rta.py` reached 903 distinct positions within 6 moves, and 388 with Speedy Spin. 0 setups.
- `house_rta_local.py` continued from the 64 positions near the house. It saturates at 123 positions, so more moves only revisit the same spots. 0 setups.
- **Closest:** (−394.863, −134), 4.4 units from the clip window, reached by spin right, run up, spin right, spin right, spin left, spin left, run up. Its x is 0.27 units too far right, and it sits against the house front instead of about 5 units in front of it.

**Why it fails:** the only walls that stop Mario sideways near the corner are the house's east wall (x −383.004) and a few fixed spots along the front. Adding whole-number spin distances to those never lands in the 0.12-unit-wide x window (−395.25 … −395.13).

## Reverse mirror clip (Crystal Palace entrance, pra_01): first look

`make_state_pra01.py` makes a pra_01 state with Lakilester out. It uses the same exit redirect as before, and before the map load it marks Lakilester as recruited and makes him the current partner. `dump_collision_pra01.py` dumps the collision.

**The room:** x 400…1050, z −225…225. The mirror is a two-sided wall (collider 0) at z = 0, spanning x 500…1000 and y −60…150. The real side is z > 0 and the reflected side is z < 0. The floor steps up from y −60 to −30 to 0 toward the palace doors at x ≈ 1000.

**How mounting Lakilester (C-down) places Mario** (`world/partner/lakilester.c`, RIDE_STATE_MOUNT_1): the target starts at Mario's position. It is then moved four times, in the directions −z, +x, +z, −x. Each move is wall-tested and has length equal to **Lakilester's current speed**. Mario ends up at the result. At normal speed the four moves cancel out. A fast Lakilester next to a wall leaves the target displaced.

**Lakilester's speed** (`partner_flying_follow_player`): when he's 50+ units from Mario and not below him, his speed is a quarter of that distance. Following Mario's move history can add 1/16 of the distance per frame.

**Results so far:**
- **Highest speed reached:** `laki_maxspeed.py` (Go-Explore over walking, spinning and jumping) reached about **17**. That was on the right side of the room, just after Mario turns down with Lakilester trailing.
- **Forced speeds, high** (`laki_speedmap.py`): Lakilester's speed is set to S from the C-down press until the mount starts, from every standable spot on both sides. With S 15…200, the only crossings need very high speeds. From the reflected side at (880, −126), S = 150 puts Mario at (778.6, −19, 18.5) on the real side. At the left end of the mirror, (500, 44), S = 200 crosses but isn't reproducible.
- **Forced speeds, realistic:** with S 8…25 on a 4-unit grid over the whole room, the only crossings start at x 1004. That's behind the palace's front wall, where Mario can't really stand.

## Mirror clip (Crystal Palace entry hall, pra_02): reproduced

`make_state_pra02.py` makes the state (Lakilester out). The hall's mirror is a two-sided wall at z = 0 (colliders 19, 20), split into triangles that meet at x = 266, 500 and 734. Half-octagon pillars stand against it on the south side: the left pillar is collider 1 (x 234–266) and the right pillar is collider 11 (x 734–766).

**Setup** (`t_pra02.py`, saved as `states/pra02_leftpillar.st`): come back left along the mirror from the far right, then hold up-left. Mario stops against the mirror and the left pillar at (275.0, 13). Lakilester ends up on his right, facing left, at (313.8, 13).

**Stop-and-go push:** go 1 frame right, stop 2. Each frame Mario overlaps Lakilester on screen, `partner_do_player_collision` nudges Lakilester away from him. Lakilester stays idle about 19–20 units ahead, still facing left, at z 12.8, while Mario advances 18.2 units per cycle.

**Why it gives speed:** while Lakilester is idle he doesn't advance through Mario's 40-entry move history. When Mario walks away from the pinned Lakilester, he chases a stale history point. His speed is up to a quarter of that distance: 22–122 in practice, peaking for one or two frames.

**Why it clips** (`mirror_corner.py`): with Lakilester's speed forced to S, C-down puts Mario behind the mirror only from just right of the right pillar (x 762–766). That's 26 spots at S = 25 and 239 spots at S = 50, but none at S ≤ 10. The mount moves Mario's position four times, each step S long, and the long steps slide off the pillar's slanted face past the point where it meets the mirror.

**Simple inputs** (`mirror_route.py`, video `mirror_clip.mp4`):
1. Push from the left pillar until Mario x ≥ 712.
2. Walk down 10 frames, then right 4 frames. Mario is now at x 734.3, the line of the right pillar's left corner.
3. Walk up slowly (stick 0, 20 or 0, 40) and press C-down on frame 0–3 or 7–10 of the walk-up. That's 8 working frames, with Lakilester at 23–122 speed.
4. Mario rides Lakilester at z −20, behind the mirror.

Several other routes around the pillar's right side also work (listed by `mirror_route.py`). `mirror_local.py` (random inputs from the push) found 52 hits in 1,024 sequences.

## Reverse mirror clip (behind the mirror → front): search so far

**Outside (pra_01)**, forced-speed maps (`rev_map.py`, `rev_map2.py`; `data/rev_map_pra01.json`):
- Real side: the only crossings are next to the left rock, at x 493–499, z 12–40 (S ≥ 50), and x 506–509, z 51–80 (S ≥ 90).
- The x 493–499 pocket is walled off from the playable area (`rev_grid.py`).
- A long stop-and-go push along the mirror (`rev_push13.py`, `rev_local2.py`) reaches mount-delay speeds of about 97, but in 704 sequences it never hit.

**Inside the palace (pra_02).** `make_state_pra02_back.py` does the normal clip, gets off, and sets up behind the mirror. This mirrors the front setup: Mario is against the back wall (z −212) just right of the back-left pillar (collider 65), with Lakilester on his right facing left (`states/pra02_back_pillar.st`, not committed).
- **The push** (`rev_push_back.py`): the back-wall stop-and-go push works with go 1–3 frames and stop 2. Go 4 loses Lakilester. Lakilester gets stuck at the back-right pillar (collider 66), x ≈ 722, so Mario stops at x 712.
- **Release speed** (`rev_release.py`): when Mario walks away from there, Lakilester peaks at about 70–93 speed, roughly 20 frames later. The stale history point is the push start, about 440 units back, so the cap is about 110.
- **Forced speeds from behind the mirror** (`rev_map_pra02*.py`; `data/rev_map_pra02w.json`, `data/rev_map_pra02r.json`): with S up to 200, x 0–1000, z −110 to −12, the only crossing is against the right wall. It needs x 980–981 at S ≥ 170, or x 940–987 at S ≥ 240. Every hit ends at (865, 12, 121). The back side has no pillar against the mirror, so there's no low-speed spot like the front's x 762–766.
- **Random search** (`rev_local_pra02.py`): random inputs from 6 push-end states, with C-down tried every frame, gave 0 hits in 1,344 sequences (about 120k C-down tries).

### Reverse mirror clip, the legend's route (pra_01 reflected side)

**Follow internals** (`follow_probe.py`; JP addresses = US + 0x1C0):
- `wPartnerFollowState` 0x8010D188, history pointer 0x8010D17C, history index 0x8010D178, `gPlayerMoveHistory` 0x8010CEF8 (40 × 16 bytes, position at +4).
- While Mario is within 40 units, Lakilester stays in follow state 5. His pointer stays on the history point where he stopped, while Mario's moves fill the ring buffer.
- In the front-room clip, the target stays at the push start (311, 13), and the distance to it grows the whole push (`dH` in the probe).
- **Pointer-0 quirk:** the "buffer full" check is `ptr != idx + 1`. With the pointer at 0 it never fires at the 39 → 0 wrap, so entry 0, the stale target, gets overwritten. Setups that leave the pointer at 0 lose the boost. `make_state_pra01_toprock.py` makes a start with the pointer at 2.
- **Speed formula,** once Mario is more than 40 away: if Mario is within 50, speed is 3 + dH/16; otherwise 0.25·dM, then capped to 0.25·dH, or + dH/16 if that's smaller.

**The push** (`rev_aim_explore2.py`): stop-and-go aimed at Lakilester, rotated by a chosen angle, with go 1–2 and stop 2/6/12. It keeps only states where state 5, the pointer and the target are all unchanged.
- From the bottom of the mirror by the left rock, (555, −13), it bends up and right into the top-right corner of the lower floor, (718, −212): the top wall and the 30-unit step at x ≈ 730.
- That is at most 236 units from the frozen target. Further is impossible: pushed straight up, he pins under the north rock (z −178); pushed sideways along the rock face he slips out of the push (the face leans, so he sits 2 units deeper than Mario); and he can't be pushed up the ramp at x 600–720.

**Release** (`rev_corner_release2.py`): running down from the corner gives 17.7 on the first frame (3 + 235/16), with peaks of 18–23. C-down on every frame 0–59 of six run angles gave no crossings.

**Speed needed** (`rev_map2.py`, `rev_map3.py`): from the reflected side, every crossing needs 110–140:
- x 769–823, z −32 at S 110
- x 760–823, z −22 to −19 at S 120
- x 751 at S 130
- x 691 at S 140

S 20–100 crosses nowhere in x 520–800, z −60 to −12, and S ≥ 150 crosses nowhere. A 236-unit push caps speed at about 60–75, so this route can't reach the crossing speeds in this ROM (JP).

**Front clip window** (`mirror_window.py`): the walk-up only clips when the down 10 / right 4 alignment leaves Mario at exactly x 734.3. C-down frames 0, 1 and 5–8 work there (6 frames). Faster pushes (go 2–3) end at other x values and the same alignment misses. Walking straight up from the end of the push never clipped.

**Video** (`reverse_mirror_attempt.mp4`, `_slow`): the closest attempt, rendered by `record_rev.py` and `render_states.py`. It shows the push from the rock into the top-right corner (pointer 2, target (592, −13) intact), then the run down and C-down on run frame 21. That frame gives the highest speed at the mount, 23.4. Mario mounts at (685, −148) with no clip.
- **Rendering gotcha:** loading the video plugin changes the emulation. With video, the same inputs end the push at Lakilester (655, −202) instead of (717, −212), probably from different lag frames. So the attempt runs without video, saves a state every frame, and a separate video-enabled process screenshots each state.

### Legend route, continued: the ledge jump and the stairs

- **Ledge** (`rev_ledge3.py`, `make_state_pra01_topright.py`): from the lower-floor corner, run right 1 frame and jump. That puts Lakilester onto the upper floor, still idle with the target intact. Then stop-and-go right along the top wall until he stops at the palace wall, (987, −212). That is **442.7 from the frozen target** (592, −13).
- **Where crossing is possible from up there** (`rev_map4.py`, `rev_map5.py`): with forced speed **≥ 120**, Mario crosses from a strip on the stairs, **x 872–884, z −145 to −79**. The top corridor itself (z −178 to −214) crosses nowhere, even at speed 260.
- **Getting down:** below the corridor is a wall at z ≈ −170, so a running jump down from the corner is needed to reach the platform and stairs (as the legend says).
  - Laki is capped at speed 6 while he's below Mario, which he is while Mario is up on the platform.
- **Where the speed comes from** (`follow_probe.py` on the fastest frames from `rev_speedspots.py`):
  - Once released, Lakilester flies to the stale target, works through the old history entries, then races back toward Mario's newest positions.
  - On that return he hits 100–131, but only while Mario stays in the corridor, about 400 units away.
- **Best so far** (`rev_jumpdown2.py`, video `reverse_mirror_legend_route.mp4`): running jump down from the corner, run down-left onto the stairs (x ≈ 893, y −10), stand while Lakilester returns, then C-down at the peak. The speed at the mount is **68**; the crossing needs ~120.
  - The strip is only ~300–340 from where the return starts, so the return speed is about 0.25 × dist + dist/16.
- **Video note:** the video plugin changes the emulation, so `record_rev2.py` saves states (every 2nd frame, every 6th along the top wall) and `render_states.py` screenshots them.

### Top step, smooth video, emulator settings

- **Top step** (`rev_topstep.py`): from the palace corner, a running jump down onto the top step by the doors, (987, 5, −165). Standing there while Lakilester returns gives **89 at the mount**, the best so far. The mount carries Mario to about (893, −120), with no crossing.
  - Forced speeds at that spot only slide him further down-left along the mirror: z −20 at speed 200+, never through (`t_force.py`).
  - `rev_map6.py`: nothing on the top step crosses at 150–300.
- **Smooth video:** `reverse_mirror_progress_smooth.mp4`, every frame at 30 fps, made with `record_rev3.py` (chunked per-frame states) and `render_states.py`.
- **Emulator:** the harness is the mupen64plus 2.5.9 core (Debian build) behind my own C frontend, with the rice video plugin used only to render.
- **Settings difference:** when `M64P_DATA` is set, the core finds its ROM database. That sets `CountPerOp=1` for Mario Story (J); without it the default is 2. That changes CPU timing, and with it the lag frames. This, not the video plugin, is why "video" runs drifted. All searches so far ran without the database.

### Running down to the mirror from the top step

- `rev_rundown.py`: running jump onto the top step, wait, then run down toward the mirror, with C-down tried on every frame.
  - Up to **112.7** at the mount on the way down.
  - **107** with Mario right at the mirror, (966, −13). Mario ends pressed on the back of the mirror at (875, 2.7, −20), with no crossing.
- `rev_local_rundown.py` (random sequences from the top step, 1,664 of them): 0 hits.
- `rev_rundown_left.py`, best mount speed with Mario near the mirror, by his x:

  | Mario x | 720 | 760 | 800 | 820 | 930–990 |
  |---|---|---|---|---|---|
  | best speed | 44 | 57 | 65 | 72 | ~107 |

  Laki is racing back toward Mario, so the further left Mario goes, the slower Laki is when he gets there. But the crossing spots near the mirror are x 691–823 and need 110–140, while x 900+ doesn't cross at any speed.
- Video: `reverse_mirror_rundown.mp4` (every frame).
- **Shorter corner wait** (`make_state_pra01_topright.py` now stops once Lakilester reaches x ≥ 984, after 49 push cycles, then waits 30 frames; `rev_rundown_fast.py`):
  - The results are the same: the mount peaks at 107.5, and Mario at the mirror reaches about 102 (x 949), with no crossing.
  - **Best mount speed by how long Mario waits on the top step:**

    | Wait (frames) | 0–12 | 16–24 | 28–60 | 64 | 68–104 | 108 | 112+ |
    |---|---|---|---|---|---|---|---|
    | Best speed | 34–38 | 17–23 | 6 | 71 | 101–108 | 64 | ≤ 20 |

    The 6 is the cap while Lakilester is below Mario. The 101–108 window is his flight to the stale target and back.
- **No stop after the jump down** (`rev_nostop.py`): the running jump flows straight into a continuous run, either one direction or switching angle partway, held up to 150 frames, with C-down on every frame. 22,680 C-downs, 0 hits.
  - Best speed at the mount is 85.4, around frame 124. Mario is against the back of the mirror at (910, −13) and ends at (897, −20).
  - The speed peak comes from Lakilester's round trip to the stale target, about 110–125 frames after Mario leaves the corner. A continuous run gets Mario to the mirror long before that, so he is pressing into it when the peak arrives.
