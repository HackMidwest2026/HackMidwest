"""Locate gStatusBar and ShimmerEmitters in the JP build (US address + 0x1C0 guess, verified here).
DIAGNOSTIC RAM write: statusBar->shimmerState = 1 (STATUS_SHIMMER_BEGIN) to start the star-power shimmer.
run from /tmp/claude-0/pm/bot1 with PYTHONPATH=. python3 shimmer_find.py STATE"""
import sys, os
sys.path.insert(0, os.getcwd())
from emu import *
from rngsim import *
SB = 0x8010EF58 + 0x1C0
PD = 0x8010F450
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sf%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/' + sys.argv[1]); e.step(0, 0, 0, 2)
print('playerData hp/fp', e.s8(PD + 2), e.s8(PD + 5), ' statusBar dispHP/FP', e.s8(SB + 0x3D), e.s8(SB + 0x3E),
      'drawPos', e.s16(SB + 0x34), e.s16(SB + 0x36), 'hidden', e.u8(SB + 0x3A), 'disabled', e.s8(SB + 0x47),
      'dispSP', e.s16(SB + 0x48), 'shimmer', e.s8(SB + 0x57))
snap = bytes(e.u8(a) for a in range(0x8010C000, 0x8010F000))
e.w8(SB + 0x57, 1)                                                # DIAGNOSTIC
e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
print('shimmer state now', e.s8(SB + 0x57), e.s8(SB + 0x58))
# emitter: particles[0].alive=1, timeLeft ~38, lifetime ~2 ; 57 entries of 0x1C
for a in range(0x8010C000, 0x8010F000, 4):
    if e.u8(a) == 1 and 30 <= e.s8(a + 1) <= 39 and 1 <= e.u8(a + 2) <= 10:
        p = a + 0x1C
        cols = [(e.u8(p + 0x1C * j + 3), e.u8(p + 0x1C * j + 4), e.u8(p + 0x1C * j + 5)) for j in range(56)]
        if all(c[0] >= 128 and c[1] >= 128 and c[2] >= 128 for c in cols):
            print('emitter at %08x' % a, e.s8(a + 1), e.u8(a + 2), cols[:6])
