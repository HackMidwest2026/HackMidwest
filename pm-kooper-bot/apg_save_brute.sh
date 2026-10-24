#!/bin/bash
# Save-block brute force: for each post-load wait W10, rush omo_10 save block -> omo_11 Super Block, then run the
# final approach grid (dir +-1, D 0..4 steps, wait 0..7) from under the block. usage: apg_save_brute.sh W10...
cd "$(dirname "$0")"; export M64P_DATA=/usr/share/games/mupen64plus
P=${PIPE_DIR:-/tmp/apg_pipe}
for w in "$@"; do
  [ -f $P/save_w$w/ub.st ] || START10=states/omo10_saveload.st WAIT10=$w PIPE_DIR=$P ./apg_pipeline.sh save_w$w > $P/res_w$w.txt 2>&1
  [ -f $P/save_w$w/ub.st ] || continue
  for d in 1 -1; do
    START=$P/save_w$w/ub.st timeout 1800 python3 omo11_apg_grid.py $d 0 5 8 $P/grid_w$w.jsonl > /dev/null 2>&1
  done
done
