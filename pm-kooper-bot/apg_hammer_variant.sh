#!/bin/bash
# one variant: HAMMER_AT=$1 HAMMER_N=$2 from the wait-210 rush; route3 then the final grid
cd "$(dirname "$0")"; export M64P_DATA=/usr/share/games/mupen64plus
T=$1_$2; W=${HAM_DIR:-/tmp/apg_ham}/$T; mkdir -p $W
HAMMER_AT=$1 HAMMER_N=$2 timeout 1500 python3 omo11_route3.py ${H_STATE:-/tmp/apg_pipe/save_w210/h.st} $W/ub.st "" 0 > $W/route.txt 2>&1
[ -f $W/ub.st ] || { echo "$T route fail: $(grep -v core: $W/route.txt | tail -1)"; exit; }
for d in 1 -1; do START=$W/ub.st timeout 2000 python3 omo11_apg_grid.py $d 0 5 8 $W/grid.jsonl >/dev/null 2>&1; done
echo "$T done"
