#!/bin/bash
# run rta_wide.py FAMILY in 4 parallel parts; results in states/wide_FAMILY_<part>.jsonl
export M64P_DATA=/usr/share/games/mupen64plus
for i in 0 1 2 3; do PART=$i NPARTS=4 timeout 7000 python3 rta_wide.py $1 states/wide_$1_$i.jsonl 2>&1 | grep --line-buffered -v ^core > states/wide_$1_$i.log & done
wait
