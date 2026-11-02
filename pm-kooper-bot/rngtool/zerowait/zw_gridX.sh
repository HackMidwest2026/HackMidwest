#!/bin/bash
# zero-wait grid with B held and the hallway scene modelled exactly (EXACT=1): a walk lock / candidate set is carried
# through the scene; only the console lag at the battle start (0-8 frames) is enumerated
N=${N:-200}
B="WALK=60 M1=150 M2=90 LEAD=15 WMAX=30 HID=440 EXACT=1"
run() { echo "== $*"; node zw_sim.js $N "$@" | tail -3; }
{
run $B
run $B WALK=45
run $B WALK=80
run $B M1=60 M2=60
run $B WMAX=0
run $B WMAX=10
run $B ERR=walk_miss
run $B ERR=scene_x
run $B ERR=turn_steps
run $B PRESS=wide
} > zw_gridX.txt 2>&1
