#!/bin/bash
# start.sh <rom> : start mupen64plus on :99 in the background
mkdir -p "${EMU_DIR:-/tmp/kz-emu}"
export DISPLAY=:99
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 2; }
pkill -x mupen64plus; sleep 1
nohup /usr/games/mupen64plus --windowed --resolution 640x480 --nosaveoptions --gfx mupen64plus-video-rice --audio dummy --emumode 2 "$1" > ${EMU_DIR:-/tmp/kz-emu}/m64.log 2>&1 &
for i in $(seq 1 30); do w=$(xdotool search --name "Mupen64Plus" 2>/dev/null | head -1); [ -n "$w" ] && break; sleep 1; done
echo "$w" > ${EMU_DIR:-/tmp/kz-emu}/win; xdotool windowactivate --sync "$w" 2>/dev/null; xdotool windowfocus "$w"; echo "window $w"
