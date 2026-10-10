#!/bin/bash
# save, wait, load, then watch 30s to confirm the game keeps running into later scenes,
# then open the kz menu (hold R, press L) and enter the states menu (4 x D-down, A)
rom="$1"; out="$2"; boot="${3:-40}"
mkdir -p "$out"; rm -f "$out"/*.png
export DISPLAY=:99
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 2; }
/usr/games/mupen64plus --windowed --resolution 640x480 --nosaveoptions \
    --gfx mupen64plus-video-rice --audio dummy --emumode 2 "$rom" > "$out/m64.log" 2>&1 &
pid=$!
press() { xdotool keydown --window "$win" $1; sleep "${2:-0.4}"; xdotool keyup --window "$win" $1; }
shot() { import -window root "$out/$1.png"; }
win=""
for i in $(seq 1 30); do win=$(xdotool search --name "Mupen64Plus" 2>/dev/null | head -1); [ -n "$win" ] && break; sleep 1; done
xdotool windowactivate --sync "$win" 2>/dev/null; xdotool windowfocus "$win" 2>/dev/null
sleep "$boot"
press a; sleep 0.5; shot 01-save
sleep 6
press d; sleep 0.5; shot 02-load
for k in 01 02 03 04 05 06 07 08 09 10; do sleep 3; shot 03-run-$k; done
# hold R (c), tap L (x)
xdotool keydown --window "$win" c; sleep 0.3; press x 0.3; sleep 0.2; xdotool keyup --window "$win" c
sleep 1; shot 04-menu
for i in 1 2 3 4; do press s 0.25; sleep 0.3; done
shot 05-menu-states-selected
press Shift_L 0.3; sleep 1; shot 06-states-menu
kill $pid 2>/dev/null; wait $pid 2>/dev/null
ls "$out" | wc -l
