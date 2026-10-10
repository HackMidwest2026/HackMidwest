#!/bin/bash
# usage: run.sh rom.z64 outdir [boot_seconds]
# Boots the rom in mupen64plus under Xvfb, then:
#   shot 1: before saving
#   press D-left (save state), shot 2
#   wait, shot 3 (scene has moved on)
#   press D-right (load state), shot 4 (should match the saved moment)
#   wait, shot 5 (still running after load)
rom="$1"; out="$2"; boot="${3:-45}"
mkdir -p "$out"; rm -f "$out"/*.png
export DISPLAY=:99
pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 2; }

/usr/games/mupen64plus --windowed --resolution 640x480 --nosaveoptions \
    --gfx mupen64plus-video-rice --audio dummy --emumode 2 "$rom" > "$out/m64.log" 2>&1 &
pid=$!

press() { # key, hold seconds
    xdotool keydown --window "$win" "$1"; sleep "${2:-0.4}"; xdotool keyup --window "$win" "$1"
}
shot() { import -window root "$out/$1.png"; }

win=""
for i in $(seq 1 30); do
    win=$(xdotool search --name "Mupen64Plus" 2>/dev/null | head -1)
    [ -n "$win" ] && break; sleep 1
done
[ -z "$win" ] && { echo "no emulator window"; kill $pid; exit 1; }
xdotool windowactivate --sync "$win" 2>/dev/null; xdotool windowfocus "$win" 2>/dev/null

sleep "$boot";            shot 1-before-save
press a;  sleep 3;        shot 2-after-save
sleep 8;                  shot 3-later
press d;  sleep 3;        shot 4-after-load
sleep 8;                  shot 5-running-after-load

kill $pid 2>/dev/null; wait $pid 2>/dev/null
grep -iE "error|exception|crash" "$out/m64.log" | grep -v "Warning" | head
ls "$out"
