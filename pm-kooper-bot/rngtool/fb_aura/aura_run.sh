#!/bin/sh
# Full aura readout + lock on one prepared stretch (README section 8). Needs `aura_table.py prep CLIP T0 T1 PRE`.
#   1. camera: matched-filter peak tracks (cam), camera-scale evidence scan (scan: a camera a few % small fits every
#      star one frame early with a faster speed), restart table + part table, refinement of the camera and the
#      per-size amplitude gains from the parts (refine); with RENDER_DIR, the camera is then replaced by the emulator
#      route camera registered onto the clip background (aura_register.py; gains kept);
#   2. per-frame terms stored once (terms), missing logic frames fitted (steps auto), restart table on logic frames;
#   3. part table, readings, frame-exact seed search (aura_lock2).
# usage: sh aura_run.sh PRE [RENDER_DIR]
set -e
D=$(dirname "$0"); PRE=$1; RD=${2:-}
gcc -O2 -fopenmp -o "$PRE.lock2" "$D/aura_lock2.c" 2>/dev/null
rm -f "$PRE"_cam.json "$PRE"_peaks_*.json "$PRE"_map.json
python3 "$D/aura_table.py" cam "$PRE" 0 120 > "$PRE"_cam.log; head -3 "$PRE"_cam.log
python3 "$D/aura_table.py" scan "$PRE" 0 150 | tail -1
python3 "$D/aura_table.py" table "$PRE" | grep -v "^  frame"
python3 "$D/aura_table.py" parts "$PRE" | tail -2
python3 "$D/aura_table.py" refine "$PRE"
[ -n "$RD" ] && python3 "$D/aura_register.py" "$RD" "$PRE"
python3 "$D/aura_table.py" terms "$PRE"
python3 "$D/aura_table.py" steps "$PRE" auto | grep -v "^  round\|^  start"
python3 "$D/aura_table.py" parts "$PRE" > "$PRE"_parts.log; tail -2 "$PRE"_parts.log
python3 "$D/aura_table.py" obs "$PRE" "$PRE"_obs.txt 8 3 0 0
"$PRE.lock2" 5 < "$PRE"_obs.txt | tee "$PRE"_lock.log
