#!/bin/bash
# shot.sh name [crop] : screenshot the emulator area
export DISPLAY=:99; import -window root ${EMU_DIR:-/tmp/kz-emu}/full.png
convert ${EMU_DIR:-/tmp/kz-emu}/full.png -crop ${2:-640x480+80+60} "${EMU_DIR:-/tmp/kz-emu}/$1.png"; echo "${EMU_DIR:-/tmp/kz-emu}/$1.png"
