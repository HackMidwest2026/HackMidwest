# pra_18 mirror clips: where Lakilester's mount speed comes from (correction)

The mount (C-down from foot) steps with Lakilester's current `moveSpeed`. While he follows Mario
(`partner_flying_follow_player`, state 0, src/world/partners.c) that speed is about

    0.25 * dist(Laki, Mario)            (only when that distance is >= 50)
    + 0.0625 * dist(Laki, his next point in Mario's 40-entry position history)

The two "natural" clips recorded earlier (videos/pra18_south_to_north_clip.mp4, videos/pra18_north_to_south_clip.mp4)
got their 42.7 / 47.3 speeds because the test placed Mario and Lakilester in RAM: Lakilester's history cursor still
pointed at a position from before the placement (~600 units away, near the room entrance), and he dashed toward it.
The S->N case matches exactly: 3 + 0.0625 * 635 = 42.7, in the direction of the old point.
In real play the history is continuous, so these speeds do not occur that way. Those two videos are NOT RTA setups.

What is still valid: the speed-needed maps (figures/pra18_clip_speeds.png; N->S ~616-x with a 1-2 speed window,
S->N 22-40 at x 613-616), which force the speed directly and say nothing about how to get it.

Real-play speed sources measured so far: a 90k-try search over normal movement in pra_01 (laki_maxspeed.py) peaked at
17.3. Speeds of 42+ need Lakilester ~170+ units from Mario at C-down, e.g. left behind an obstacle.

## South -> north with real speed (later results)
- Clip needs Mario's x within ~612..616 (line south of the pillar's east corner); min speed ~20.5 at x 616, 27 at 615,
  34 at 614, 48 at 612; every higher speed up to 100 also clips (data/pra18/sn_minspeed.json).
- Holding the stick up-and-slightly-left (~(-21..-27, 47..71)) from just south of the corner parks Mario on the pillar's
  south face at x 612..615.5, z ~25, where speed >= 24..48 clips (data/pra18/sn_cornerpin.json). This fixes x without aiming.
- Real speed source: after a dismount Lakilester hovers ~32 frames, then his speed jumps to ~0.25 * distance to Mario and
  drops by a quarter per frame. C-down only works grounded and not spinning. Running gives ~80 units by then -> ~21-26.
- Best real-speed setup found: dismount at (644.6, 109.7) holding (-22, 57), keep holding 33 frames, C-down on frame 34 after the
  dismount press (speed ~21-22). 1-frame window and only 2/245 nearby dismount spots/stick variants clip -> not RTA-viable.
- Video: videos/pra18_south_to_north_real_speed.mp4 (Laki speed not edited; C-down on frame 34; frame 33 or 35 fails).
