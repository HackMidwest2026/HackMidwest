#!/bin/bash
# omo_10 (PRE actions) -> omo_11 -> route2 -> route3 (DELAY) -> Super Block hit; prints the menu fields.
# usage: apg_pipeline.sh TAG [DELAY]   env PRE, MARK passed to omo10_to_omo11.py
cd "$(dirname "$0")"; export M64P_DATA=/usr/share/games/mupen64plus
T=$1; D=${2:-0}; W=${PIPE_DIR:-/tmp/apg_pipe}/$T; mkdir -p $W
timeout 600 python3 omo10_to_omo11.py $W/e1.st 2>$W/log.txt >/dev/null || { echo "$T omo10 fail"; exit; }
START=$W/e1.st timeout 900 python3 omo11_route2.py $W/h.st 2>&1 | grep -v core: >> $W/log.txt
[ -f $W/h.st ] || { echo "$T route2 fail $(tail -1 $W/log.txt)"; exit; }
timeout 900 python3 omo11_route3.py $W/h.st $W/ub.st "" $D 2>&1 | grep -v core: >> $W/log.txt
[ -f $W/ub.st ] || { echo "$T route3 fail $(tail -1 $W/log.txt)"; exit; }
START=$W/ub.st timeout 300 python3 omo11_superblock_probe.py 2>&1 | grep -v core: | tail -1 | sed "s/^/$T /"
