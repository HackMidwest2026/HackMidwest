#!/bin/bash
# v87: rebuild the emulator and every savestate the v84-v87 rngtool scripts use, after a container restart (states, the
# harness and the cores are never committed). One command:  PM_ROM=/path/to/mario-story-jp.z64 bash make_states.sh
#   BUILD=0 skips the core / harness build (already there).  Takes about 5 minutes (the cores' build; the states take seconds).
# Layout made here (what the scripts expect):
#   ../../mupen64plus-core      core ba95bab + ../mupen64plus-core-headless.patch (NEW_DYNAREC, the normal core)
#   ../../mupen64plus-core-dbg  the same with DEBUGGER=1 (M64P_DBG=1: rand_int breakpoints, the RNG-trace logs)
#   /tmp/claude-0/pm/bot1       the harness dir: symlinks to ../*.py and harness.so, pm-jp.z64 -> PM_ROM, states/
#   /tmp/claude-0/pm/mupen64plus-core{,-dbg} -> the cores (emu.py finds them as ../mupen64plus-core* from bot1)
# Every battle state is a DIAGNOSTIC setup (labelled RAM writes in boss_battle_start_setup.py): the battle id written on
# the nok_14 Koopa's encounter, partner / rank / badges / boots / HP / FP / items / Peach Beam written before the walk.
# The original states were made the same way (READMEs: dup_charge, charge_live v84-v86, fb2_route); the v87 rebuild is not
# byte-identical to them (frame counters, the RNG at the menu), which no script depends on: every logging script writes its
# own gRandSeed at the menu.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; BOT="$(dirname "$HERE")"; REPO="$(dirname "$BOT")"
ROM=${PM_ROM:-/tmp/claude-0/pm/rom/mario-story-jp.z64}; B=/tmp/claude-0/pm/bot1
if [ "${BUILD:-1}" = 1 ]; then
  command -v apt-get >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -q mupen64plus-rsp-hle \
    mupen64plus-video-glide64mk2 mupen64plus-data libsdl2-dev xvfb imagemagick >/dev/null || true
  cd "$REPO"
  [ -d mupen64plus-core ] || { git clone -q https://github.com/mupen64plus/mupen64plus-core && (cd mupen64plus-core && git checkout -q ba95bab && git apply "$BOT/mupen64plus-core-headless.patch"); }
  [ -d mupen64plus-core-dbg ] || cp -a mupen64plus-core mupen64plus-core-dbg
  grep -qx 'mupen64plus-core/' .git/info/exclude 2>/dev/null || printf 'mupen64plus-core/\nmupen64plus-core-dbg/\n' >> .git/info/exclude
  make -C mupen64plus-core/projects/unix all NETPLAY=0 OSD=0 NEW_DYNAREC=1 VULKAN=0 -j2 >/dev/null &
  make -C mupen64plus-core-dbg/projects/unix all DEBUGGER=1 DEBUGGER_NO_DISASM=1 OSD=0 NETPLAY=0 VULKAN=0 -j2 >/dev/null &
  wait
  gcc -O2 -shared -fPIC -o "$BOT/harness.so" "$BOT/harness.c" -I"$REPO/mupen64plus-core/src/api" -ldl -lpthread 2>/dev/null
fi
mkdir -p "$B/states" /dev/shm/pmbot /dev/shm/fb2r
ln -sfn "$REPO/mupen64plus-core" /tmp/claude-0/pm/mupen64plus-core; ln -sfn "$REPO/mupen64plus-core-dbg" /tmp/claude-0/pm/mupen64plus-core-dbg
for f in "$BOT"/*.py "$BOT/harness.so"; do ln -sfn "$f" "$B/"; done
ln -sfn "$ROM" "$B/pm-jp.z64"
cd "$B"; Q() { "$@" 2>&1 | grep -v '^core:' | tail -1; }
# the field states the battle setups start from (new file -> Koopa Village; make_state_room breaks on its first frame in
# area 6, so "nok13_e0_laki2" stands in nok_14 next to the Koopa at (-650, -150) that boss_battle_start_setup walks into)
Q python3 make_state2.py
Q env PRA_MAP=nok_13 PRA_AREA=6 PARTNER=8 NOK14=states/nok14_start_goombario.st STATE_SUFFIX=_laki2 python3 make_state_room.py
S() { echo "== $*"; Q env "$@"; }
# Final Bowser phase 2, Ultra Boots route (fb2_route README): Lakilester Super, Power Bounce / S.Jump Charge / Power Rush /
# Close Call, Ultra Boots, 10 HP / 15 FP, Jammin' Jelly + Life Shroom, the Peach Beam
S AC=1 PARTNER=8 BRANK=1 BADGES=e4,10c,10d,112 BOOTS=2 HP=10 FP=15 ITEMS=a2,95 NOFS=1 STARBEAM=2 SUF=_peach python3 boss_battle_start_setup.py 2304
Q env PYTHONPATH=. python3 "$HERE/fb2_route/t1menu_state.py" /dev/shm/fb2r/t1menu.st
# Final Bowser phase 2, Normal Boots (charge_live v86 section 3), and its T2 menu (fb2_route/nb_p2_state.py)
S AC=1 PARTNER=1 BRANK=1 BADGES=10c,e4,112,11f BOOTS=0 FP=10 HP=10 ITEMS=93,95,95,a3 NOFS=1 STARBEAM=2 SUF=_nbg python3 boss_battle_start_setup.py 2304
Q env PYTHONPATH=. python3 "$HERE/fb2_route/nb_p2_state.py"
# Jr. Troopa, Ultra Boots route (dup_charge README: "the Jr. Troopa route state's setup"): Bombette Super, S.Jump Charge,
# Power Bounce, Close Call, Speedy Spin, Ultra Boots, 10 HP / 10 FP; items as the v85 / v87 logs write them
S AC=1 PARTNER=3 BRANK=1 BADGES=10c,e4,112,11f BOOTS=2 FP=10 ITEMS=93,a3,95,95 NOFS=1 SUF=_route python3 boss_battle_start_setup.py 0207
# Jr. Troopa, Normal Boots (charge_live v85 section 1)
S AC=1 PARTNER=1 BRANK=1 BADGES=10c,e4,112,11f BOOTS=0 FP=10 ITEMS=93,95,95,a3 NOFS=1 SUF=_nbg python3 boss_battle_start_setup.py 0207
# Hallway Bowser, Ultra Boots (rngtool README: Lakilester Super, Jump Charge + Power Bounce + Close Call, 10 HP / 15 FP)
S AC=1 PARTNER=8 BRANK=1 BADGES=10c,e4,112 BOOTS=2 HP=10 FP=15 ITEMS=95 NOFS=1 SUF=_route python3 boss_battle_start_setup.py 2302
# Hallway Bowser, Normal Boots (v84: Goombario)
S AC=1 PARTNER=1 BRANK=1 BADGES=10c,e4,112,11f BOOTS=0 FP=10 ITEMS=93,95,95,a3 NOFS=1 SUF=_goomba python3 boss_battle_start_setup.py 2302
# Duplighosts (dup_charge README)
S AC=1 PARTNER=3 BRANK=1 BADGES=10c,e4,112,11f BOOTS=2 FP=10 NOFS=1 SUF=_dchg python3 boss_battle_start_setup.py 2402
ls -la "$B/states"
