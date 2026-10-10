#!/bin/bash
# longer sequence: save, load, load again, re-save over the slot, next slot + save, load, open states menu
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
step=0
act() { # name, key(s)
    step=$((step+1)); press "$2"; sleep 0.5; shot "$(printf %02d $step)-$1-log"; sleep "${3:-4}"; shot "$(printf %02d $step)-$1-after"
}
sleep "$boot"
shot 00-start
act save1 a 6
act load1 d 6
act load2 d 6
act resave a 6
act load3 d 6
# R+L opens the kz menu (c = R, x = L)
xdotool keydown --window "$win" c x; sleep 0.4; xdotool keyup --window "$win" c x; sleep 1; shot 90-menu
kill $pid 2>/dev/null; wait $pid 2>/dev/null
grep -iE "exception|crash|unhandled" "$out/m64.log" | head
ls "$out" | wc -l
