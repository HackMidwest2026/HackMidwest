#!/bin/bash
# The Time Out Timer test suite (build first: python3 build_page.py), one test at a time so the CPU stays free (the seed
# search is timing-sensitive under load). Prints one line per test (exit code and the last output line); full output in
# $OUT/<test>.txt. Known broken before these changes: test_route.js (a removed profile option), test_press_sim.js (needs a
# file in /dev/shm). Then the two user log replays (run 2 must lock at 1379.7 s, run 3 at 655.7 s on 52467bd0).
OUT=${OUT:-/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/suite}; mkdir -p "$OUT"; cd "$(dirname "$0")"
T="test_core test_present test_chain_page test_wide test_relock_short test_pickup_lock test_lost test_plan_keep test_torch_page test_carry_page test_switch test_early_press test_dirty test_edges_page test_maze_dup_page test_edges_core test_chain_core test_torch_core test_turns test_hw_t1 test_hud_confirm test_carry_guard test_hw_carry test_zw_mix"
for t in ${ONLY:-$T}; do
  timeout ${TMAX:-2400} node $t.js > "$OUT/$t.txt" 2>&1; echo "$t rc=$? :: $(tail -1 "$OUT/$t.txt" | cut -c1-160)"
done
if [ -z "$ONLY" ]; then
  TORCH=1 timeout ${TMAX:-2400} node test_maze_dup_page.js > "$OUT/test_maze_dup_page_torch.txt" 2>&1; echo "test_maze_dup_page TORCH=1 rc=$? :: $(tail -1 "$OUT/test_maze_dup_page_torch.txt" | cut -c1-160)"
  U=/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887
  for L in $U/6de1b44c-timeout-timer-log-1793573065207.json $U/7d9e2092-timeout-timer-log-1793580159724.json; do
    timeout ${TMAX:-2400} node test_replay_log.js "$L" > "$OUT/replay_$(basename $L).txt" 2>&1; echo "replay $(basename $L) rc=$? :: $(grep -i lock "$OUT/replay_$(basename $L).txt" | head -3 | tr '\n' ' ' | cut -c1-240)"
  done
fi
