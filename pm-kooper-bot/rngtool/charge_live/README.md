# Charge lock: the seed from the Charge rays, live on the page (Nov 2)

On Hallway Bowser turn 1 the page reads gRandSeed from Mario's (Super) Charge rays while the run goes on, carries it
through Lakilester's Spiny Flip and Bowser's attack with the zero-wait tracker, and on turn 2 beeps the best Time Out
confirm frame (or says No edge). Nothing here makes the runner wait: the only added time is the beep window.

## What the page does

1. **Arming.** On the route's Hallway T1 step, when the status bar hides (the Charge confirm hides it 3 frames after
   the confirm), the page starts keeping capture frames, each drawn into the 640x480 game raster (2 px per 320-space
   unit, the capture map fitted for this OBS setup: 1280x720, `CHG_MAP`) as luma.
2. **Trigger.** The burst (`radial_shimmer`) brightens the game area. The first frame 5 levels above the median of the
   frames before it is game frame 3 (frame 0 = Charge confirm + 13). Calibrated on all 7 route clips (the true frame 0
   from the seed's score). A trigger that does not keep rising (+15 by 0.35 s) is dropped.
3. **Game frames.** The browser drops pictures and its frame times jitter by +-17 ms, so each new picture is placed by
   dynamic programming on the burst's brightness curve (`CHG_BRIGHT`, the same in every Charge: sd < 0.7 levels over 7
   clips) and the time between pictures. Frames 0-2 and -2/-1 are taken by time.
4. **Mario's position.** In 2 of the 7 clips (15-14-09, 15-19-21) Mario stood 16.5 raster px (6.1 world units) to the
   right of the reference. That, not the burst, is why those two failed offline: the rays are centred on him. The page
   finds him by normalised cross-correlation of a high-passed patch (`mario_ref.json`, frame -1 of 15-15-06) on frames
   -2..1 and moves the ray centre by 0.37 units per px.
5. **Ray maps.** For each of the 48 frames, every integer angle and every 4-unit step from the centre: luma on the
   projected ray minus beside it (+-2 px in 320 space), through the per-frame camera table
   (`readouts/data/charge_cams_mario_route.json`). **The burst is removed per angle:** each angle's median over
   distance is subtracted (the burst's streaks run the whole radius, a ray is a 128-unit segment). No emulator render
   is needed. Tested against the old emulator-render subtraction on the 5 clips it handled: the same lock margins.
6. **Search** (`kernel.c`, WebAssembly in workers, all cores but one by default):
   - Stage 1, per effect (A: scale 1.2, frame 0; B: scale 0.8, frame 3, whose base draw is the 25th or 26th LCG step
     after the seed): an effect's 10 initial rays depend only on the state s1 after its base-angle draw, and s1 lies in
     that base's interval of 2^32/361 states. Each base has an upper bound (the best ray score at each part's angle).
     Bases are searched in decreasing bound with branch and bound against the running K-th best (K = 16384, parts in
     decreasing bound order, each part's two draws by LCG jump constants). A base whose bound is at or below the K-th
     best is skipped, so the top K of all 2^32 per effect is exact. 20-50 bases of 361 are searched.
   - Joint: each candidate's other effect's initial rays are scored exactly; the top 300 go to stage 2.
   - Stage 2: the full simulation of both effects over 48 frames for every first-coin frame q (0..47, then 24/48).
   - **Lock** if the best score is at least 3000 and 1.8 times the next (true seeds 3300-8300 at 2.3-5.4 times the
     runner-up on the route clips; wrong ones 750-1500 at 1.0-1.2).
7. **Tracker.** The lock starts the zero-wait tracker (`zw*` in page_template.html) at frame 0 with particles
   seed x q (every q within 0.5% of the best; late first coins barely move the rays) x console lag 0/1/2 frames after
   the rays (weights 0.7/0.2/0.1). The coin's shines and visible stretches seen while the search ran are added. The
   Spiny Flip confirm (read from the status bar hiding, `HUD_HIDE.hw_spiny = 2` frames, carried at -2..+1: a dropped
   picture only reads it late) splits each particle over impact +40..+175 (thrown with A) x guard. At most 6 q are
   kept (best first) and lag 0/1, so a split stays under the tracker's 40000. Shines may read up to 3.5 frames late. Particles merge once Bowser's AI has run and his attack's
   draws are done. The turn-2 menu's coin prunes them; Time Out's target screen beeps the best frame in the window
   (or No edge, as before).
8. **q from the turn-1 menu** (`chgQBack`): for each q the coins before frame 0 follow from the seed stepped back; the
   menu's seen shines must match. Not exercised by the route clips (they start ~1 s before the menu, so no menu stretch
   was long enough), so **unverified**.

Sidebar: "Charge lock: yes/no", time to lock after the rays end, the hypotheses left, the seed and q.

## Files
- `kernel.c`: the search (stage 1, joint, stage 2); `build_kernel.sh` compiles it to `kernel.wasm.b64` (clang wasm32),
  which `build_page.py` inlines.
- `charge_live.js`: the page side (capture, trigger, frames, Mario, maps, workers, lock, tracker start, sidebar).
- `mario_ref.json`: Mario's reference patch.
- `tools/gameframes.py` (clip -> game-frame rasters with the page's rule), `tools/jsmaps.js` (the page's own maps code
  in node), `tools/harness.c` (the kernel natively, single thread).
- `../test_charge_clips.js`: the 7 route clips through the page in headless Chromium in real time.

## Results

### Offline, the page's maps code + kernel (tools/, native, 1 thread)
| Clip | Seed | q | Score | x runner-up | Stage 1 |
|---|---|---|---|---|---|
| 15-14-09 | b400fca5 | 7 | 7088 | 3.92 | 3.8 s |
| 15-15-06 | cf5894f0 | 19 | 5878 | 3.79 | 5.8 s |
| 15-16-08 | 6d3b7b2b | 41 | 7045 | 5.18 | 4.7 s |
| 15-17-02 | b3fb9c3b | 18 | 6397 | 2.30 | 7.7 s |
| 15-18-30 | 2d5dd210 | 42 | 7467 | 4.38 | 5.3 s |
| 15-19-21 | ea113ee3 | 19 | 8235 | 4.94 | 5.4 s |
| 15-20-15 | 306686e9 | 16 | 7400 | 4.65 | 5.7 s |

All 7 lock, including the two that failed before (Mario's position). The 5 earlier seeds are reproduced.

### Live, in headless Chromium (test_charge_clips.js)
Each clip played in real time by a `<video>` and handed to the page as its capture (VP9 re-encode, crf 8). The page
starts on the Hallway T1 step with no walk lock: the rays are the only seed source. "Lock" is after the rays end;
Time Out's bar hides 11.8-12.6 s after the rays end in every clip, so that is the deadline. "At confirm" is the share
of the tracker's states for which Time Out works at the real confirm (bar hiding - 3 frames; -1 / 0 / +1). "Beep" is
the frame the page would have beeped had the runner waited on the target screen (lead 1.5 s, window 1 s), relative to
the real confirm, with the chance it showed.

**This machine was shared with another session running 4 CPU-bound threads for most of the testing (load 5-9 on 4
cores)**, so the browser dropped pictures and the search ran on what was left. Final build, run with the lowest load
(load 1.8 rising to 6):

| Clip | Lock | Seed, q | Time to lock (search, 3 workers) | States at plan | At confirm (-1/0/+1) | Predicted | Actual | Beep (shown) |
|---|---|---|---|---|---|---|---|---|
| 15-14-09 | yes | b400fca5, 3-9 | 4.0 s (3.7) | 11 | 0.39 / **0.09** / 0.08 | fails | fails | +50 (61%) |
| 15-15-06 | yes | cf5894f0, 19 | 5.5 s (5.3) | 8 | 0 / **0** / 0.02 | fails | fails | +66 (61%) |
| 15-16-08 | yes | 6d3b7b2b, 41-47 | 4.2 s (4.0) | 8 | 0.62 / **0.01** / 0.31 | fails | fails | +71 (91%) |
| 15-17-02 | yes | b3fb9c3b, 18 | 6.0 s (5.7) | 9 | 0.23 / **0.63** / 0.85 | works (wrong) | fails | +49 (90%) |
| 15-18-30 | yes | 2d5dd210, 35-42 | 5.1 s (4.9) | 20 | 0.18 / **0.04** / 0.17 | fails | fails | No edge (34% < 40%) |
| 15-19-21 | yes | ea113ee3, 19 | 10.0 s (9.7), load 6-8 | 3 | 0 / **0** / 0.78 | fails | fails | +47 (73%) |
| 15-20-15 | yes | 306686e9, 16 | 13.5 s (13.2), load 6-8 | 0 | - | No edge | works | No edge |

An earlier build (before the q cap and the -2..+1 Spiny shifts, at load ~3) gave all 7 with the tracker alive:
15-20-15 locked 5.2 s after the rays, **1.00 at the confirm (works, actual works)**, beep +46 (75%); 15-17-02 0.00
(fails, actual fails); the other five as above. Over 11 full runs of the 7 clips during development (several builds) the rays
locked the right seed in 68 of 77 clip runs and never locked a wrong one. The misses: 15-16-08 eight times (its true
seed is the weakest offline, ranked ~40th after the joint stage; every miss was at load 5-9) and 15-18-30 once (an
early build's frame placement).

Under heavy load the carry after the lock is what breaks: the bar-hiding read of the Spiny Flip confirm came 5-10
frames late twice, and a lock that lands after the turn-2 menu has nothing to prune with; both end as "No edge" (the
page never beeps on states that do not fit). 15-17-02's 0.63 at the confirm is the one wrong prediction; that clip had an
unexplained coin before the Charge in the offline fit too.

Lock time on this machine: 3.7-5.7 s of search with 3 workers at moderate load (single thread, native: 3.8-7.7 s).
Maps: 0.15-0.3 s. Capture: 3-4 ms per picture while armed (about 2 s).

## Not verified
- Only this capture: 1280x720 OBS of a GV-USB2, with this crop (`CHG_MAP`). Another crop or capture card needs the map
  refitted; the Mario check (NCC) and the trigger levels would show it (the sidebar says why there is no lock).
- Only Mario's Super Charge with Lakilester, at the route's camera. Goombario's Charge and other fights are not built.
- `HUD_HIDE.hw_spiny = 2` is from the A icon on the clips (bar hides 0-2 capture frames after the A); the tracker
  carries -2..+1 around it. The Time Out confirm in the table is the bar hiding - 3 frames (as Mario's actions), so the
  "predicted at the real confirm" column is read at that frame (+-1 shown).
- Bowser's attack is not read from the video (the coin on the turn-2 menu does the pruning).
- The q check against the turn-1 menu (unexercised, see above).
- The input display is not read: the press correction is not auto-calibrated.
- WebGPU is not used: the browser here has none; the WebAssembly search alone fits in the time available.

## Missing pictures (the aura finding, fb_aura/README.md section 8)
Some logic frames never get their own picture in the capture, and x264 sometimes re-encodes a duplicate so it looks
new. What that means here:
- **The rays window.** Frames are not counted: each new picture is placed on the burst's brightness curve (dynamic
  programming over n, steps of 0-3 frames), so a missing picture shows as a jump on the curve and a re-encoded
  duplicate as a step of 0. On the 7 source clips the curve, indexed by distinct pictures from the trigger, has sd < 0.7
  levels at every one of frames 3-45, so none of the 7 has a missing logic frame inside the rays (a skipped one would
  shift every later index by a whole step, 2-9 levels). That includes 15-17-02 and 15-18-30.
- **After the rays** the tracker's clock is time (the capture's frame times), not a picture count, so a logic frame with
  no picture costs nothing. What it cannot see is a lag frame (time passes, the game does not step); those are carried
  as 0/1 frame hypotheses after the rays and as the Spiny Flip confirm shifts.
- So a hidden missing picture does not explain the coin mismatches of 15-17-02 (a flash 24 frames before the Charge)
  and 15-18-30 (q before vs after the Charge): the offline check (readouts/charge_qback.py) also clocked by time. Not
  resolved; both are before the Charge, which the live page does not need.
