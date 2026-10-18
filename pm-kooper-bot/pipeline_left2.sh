#!/bin/bash
# Re-run arc search -> corners -> ledge -> aimed top-wall push from an existing rock-jump state, keeping the chosen
# arc sequence and ledge plan in states/ (persistent). usage: pipeline_left2.sh TAG ROCKJUMP_STATE MINUTES
set -u
TAG=$1; RJ=$2; MIN=$3
export M64P_DATA=/usr/share/games/mupen64plus
D=/dev/shm/pmbot/pl_$TAG; mkdir -p $D
python3 rev_aim_explore2.py $D/ax $MIN $RJ 2>&1 | grep -v ^core | tail -1
cp $D/ax/arch.json states/arch_$TAG.json
python3 save_corners.py $D/ax/arch.json $RJ $D/corner_ 2>&1 | grep -v ^core
for c in $D/corner_*[0-9].st; do
  n=$(basename $c .st)
  CORNER=$c python3 rev_ledge4.py $D/ledge_$n.json >/dev/null 2>&1
  plan=$(python3 -c "import json; r=json.load(open('$D/ledge_$n.json')); g=[x for x in r if x[0] > 440]; print(json.dumps(g[0][1]) if g else '')")
  [ -z "$plan" ] && { echo "$n: no ledge plan"; continue; }
  for th in 0 -10 10 20 -20; do
    out=$(AIM=$th python3 make_topright_from_corner.py $c "$plan" states/pra01_topright_$TAG.st 2>&1 | grep -v ^core)
    echo "$n plan $plan aim $th: $out"
    if echo "$out" | grep -q saved && echo "$out" | grep -q "L (98[3-9]"; then
      cp ${c%.st}_seq.json states/arc_$TAG.json; echo "{\"plan\": $plan, \"aim\": $th}" > states/ledge_$TAG.json; break 2
    fi
  done
done
