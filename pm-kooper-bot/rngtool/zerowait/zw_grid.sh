#!/bin/bash
# zero-wait simulation grid (node zw_sim.js); results in zw_grid.txt
N=${N:-200}
B="WALK=60 M1=150 M2=90 LEAD=15 WMAX=30"
run() { echo "== $*"; node zw_sim.js $N "$@" | tail -3; }
{
run $B
run $B WALK=45
run $B WALK=80
run $B M1=60 M2=60
run $B WMAX=0
run $B WMAX=10
run $B WMAX=60
run $B GUARD=known
run $B ERR=walk_miss
run $B ERR=scene_x
run $B ERR=impact
run $B ERR=turn_steps
run $B PRESS=wide
run $B WALK=80 M1=150 M2=90 CAP=4096
} > zw_grid.txt 2>&1
