#!/bin/bash
# zero-wait grid with B held through the hallway scene: extra steps 124-125 (fixed schedule), scene 347 frames
N=${N:-200}
B="WALK=60 M1=150 M2=90 LEAD=15 WMAX=30 XT_LO=124 XT_HI=125 XLO=118 XHI=131 HID=440"
run() { echo "== $*"; node zw_sim.js $N "$@" | tail -3; }
{
run $B
run $B WALK=45
run $B WALK=80
run $B M1=60 M2=60
run $B WMAX=0
run $B ERR=walk_miss
run $B ERR=turn_steps
} > zw_gridB.txt 2>&1
