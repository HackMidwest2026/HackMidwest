#!/bin/bash
# k.sh key [key...] : tap each key (0.25s hold, 0.35s gap). "R+L" opens the kz menu. "wait:N" sleeps N seconds
export DISPLAY=:99; w=$(cat ${EMU_DIR:-/tmp/kz-emu}/win)
for k in "$@"; do
  case "$k" in
    R+L) xdotool keydown --window $w c; sleep 0.3; xdotool keydown --window $w x; sleep 0.25; xdotool keyup --window $w x; sleep 0.2; xdotool keyup --window $w c ;;
    wait:*) sleep "${k#wait:}" ;;
    *) xdotool keydown --window $w "$k"; sleep 0.3; xdotool keyup --window $w "$k" ;;
  esac
  sleep 1.5
done
