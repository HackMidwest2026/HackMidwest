#!/bin/bash
# g64start.sh <rom> : start gopher64 on :99 in the background (dummy audio)
mkdir -p "${EMU_DIR:-/tmp/kz-emu}"
export DISPLAY=:99
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 2; }
pkill -x gopher64; pkill -x mupen64plus; sleep 1
HOME=${G64_HOME:-/tmp/kz-gopher64} XDG_DATA_HOME=${G64_HOME:-/tmp/kz-gopher64}/data XDG_CONFIG_HOME=${G64_HOME:-/tmp/kz-gopher64}/config SDL_AUDIO_DRIVER=dummy \
  nohup ${GOPHER64:-gopher64} "$1" > ${EMU_DIR:-/tmp/kz-emu}/gopher64.log 2>&1 &
for i in $(seq 1 40); do w=$(xdotool search --name "gopher64" 2>/dev/null | head -1); [ -n "$w" ] && break; sleep 1; done
echo "$w" > ${EMU_DIR:-/tmp/kz-emu}/win; xdotool windowactivate --sync "$w" 2>/dev/null; xdotool windowfocus "$w" 2>/dev/null; echo "window $w"; xdotool getwindowgeometry "$w"
