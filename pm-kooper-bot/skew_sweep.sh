#!/bin/bash
# Build flo_08 entry-0 states for a list of exitTangent values (args), then classify Laki's behaviour with skew_probe.py.
export M64P_DATA=/usr/share/games/mupen64plus
for T in "$@"; do
  [ -f states/flo08_e0_skew$T.st ] || PRA_MAP=flo_08 PRA_AREA=19 PRA_ENTRY=0 TANGENT=$T PM_TMP=/dev/shm/pmbot/sw$$ timeout 280 python3 make_state_skew.py > /dev/null 2>&1
  python3 skew_probe.py states/flo08_e0_skew$T.st $T 2>/dev/null | grep -v ^core
done
