#!/bin/bash
# Full re-setup for a shifted stale target: rock-jump state -> arc search -> corner states -> ledge search ->
# aimed top-wall push -> top-right state -> simple-ending window test. usage: pipeline_left.sh TAG PA PRE R MINUTES
set -u
TAG=$1; PA=$2; PRE=$3; R=$4; MIN=$5
export M64P_DATA=/usr/share/games/mupen64plus
D=/dev/shm/pmbot/pl_$TAG; mkdir -p $D
PA=$PA STOP=fill FILL_OUT=states/pra01_rockjump_$TAG.st python3 make_setup_left.py $PRE $R 8 x 2>&1 | grep -E "^(rock|fill)"
python3 rev_aim_explore2.py $D/ax $MIN states/pra01_rockjump_$TAG.st 2>&1 | grep -v ^core | tail -1
python3 save_corners.py $D/ax/arch.json states/pra01_rockjump_$TAG.st $D/corner_ 2>&1 | grep -v ^core
for c in $D/corner_*[0-9].st; do
  n=$(basename $c .st)
  CORNER=$c python3 rev_ledge4.py $D/ledge_$n.json >/dev/null 2>&1
  plan=$(python3 -c "import json; r=json.load(open('$D/ledge_$n.json')); g=[x for x in r if x[0] > 440]; print(json.dumps(g[0][1]) if g else '')")
  [ -z "$plan" ] && { echo "$n: no ledge plan"; continue; }
  for th in 0 -10 10 20 -20; do
    out=$(AIM=$th python3 make_topright_from_corner.py $c "$plan" states/pra01_topright_$TAG.st 2>&1 | grep -v ^core)
    echo "$n plan $plan aim $th: $out"
    echo "$out" | grep -q saved && echo "$out" | grep -q "L (98[3-9]" && break 2
  done
done
[ -f states/pra01_topright_$TAG.st ] && SHOWSPD=1 BASE=states/pra01_topright_$TAG.st python3 rta_shift_win.py 0 2>&1 | grep -v ^core
