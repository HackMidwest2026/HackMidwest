#!/bin/bash
# Fast setup: corners from the fast arc archive -> ledge plan (rev_ledge4) -> fastest aimed top-wall push
# (fast_wall.py) -> hold-up ending check (rta_holdup2.py). Keeps the first corner whose state clips, with its arc,
# ledge plan and wall parameters in states/. usage: pipeline_fast.sh TAG ARCH.json SEED.st
set -u
TAG=$1; ARCH=$2; SEED=$3
export M64P_DATA=/usr/share/games/mupen64plus
D=/dev/shm/pmbot/pf_$TAG; mkdir -p $D
python3 save_corners.py $ARCH $SEED $D/corner_ 2>&1 | grep -v ^core
for c in $D/corner_*[0-9].st; do
  n=$(basename $c .st)
  CORNER=$c python3 rev_ledge4.py $D/ledge_$n.json >/dev/null 2>&1
  plan=$(python3 -c "import json; r=json.load(open('$D/ledge_$n.json')); g=[x for x in r if x[0] > 440]; print(json.dumps(g[0][1]) if g else '')")
  [ -z "$plan" ] && { echo "$n: no ledge plan"; continue; }
  python3 fast_wall.py $c "$plan" $D/top_$n.st 2>&1 | grep -E "fastest|^th" | grep -E "OK|fastest" | head -4
  [ -f $D/top_$n.st ] || { echo "$n: no wall push"; continue; }
  res=$(START=$D/top_$n.st python3 rta_holdup2.py 2>&1 | grep CLIP)
  echo "$n ($plan): ${res:-no clip}"
  if [ -n "$res" ]; then
    cp $D/top_$n.st states/pra01_topright_$TAG.st; cp $D/top_${n}_wall.json states/wall_$TAG.json; cp ${c%.st}_seq.json states/arc_$TAG.json
    echo "kept $n"; break
  fi
done
