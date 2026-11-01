# Time Out Timer (Hallway Bowser RNG manipulation)

`timeout_timer.html` is the tool (single file; open it in a browser). Built from `page_template.html` with
`pmrng_core.js` spliced in at `/*CORE*/`.

- `pmrng_core.js`: RNG model, coin pattern from shine taps, seed search, resync, Time Out planner.
- `timeout_model.py`: the same Time Out model in Python (validated frame by frame against the emulator).
- `tool_cli.js`: Node front end used by `e2e_timeout.py`.
- `e2e_timeout.py SEED`: emulator end-to-end test (watch in the turn-1 menu, find the seed, play turn 1 with random
  waits, resync in the turn-2 menu, plan, confirm on the planned frame). Seeds 2468ace0, 13579bdf, 0f0f1e1e: all WORKED.

Model (JP): seed*0x5D588B65+1, one step per frame. Status-bar coin draws rand_int(100) every 24 frames (48 after a
shine, which happens on 70+). Time Out confirm on frame C: effect draws on C+24, C+73, C+112, roll first on C+386,
works if <= 30. In-frame order: battle script (roll, effect spawns), coin, per-frame step.
