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
