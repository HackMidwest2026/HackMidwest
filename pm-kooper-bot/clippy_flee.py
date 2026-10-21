"""Run away from the clippy-setup battle (exploration). Loads a battle state saved by clippy_verify.py, pages the
first-strike tutorial (6 x A), opens Strategies (stick up x2, A), picks Run Away (stick down x2, A), mashes A until
the field returns, then logs the encounter/freeze/partner/input/collision-counter state for 1200 more frames.
usage: clippy_flee.py BATTLE.st [FIELD_OUT.st]"""
import sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/clfl')
e.load(sys.argv[1])
e.step(0, 0, 0, 120)
for i in range(6): e.step(A, 0, 0, 4); e.step(0, 0, 0, 50)
for i in range(2): e.step(0, 0, 70, 4); e.step(0, 0, 0, 20)
e.step(A, 0, 0, 4); e.step(0, 0, 0, 30)
for i in range(2): e.step(0, 0, -70, 4); e.step(0, 0, 0, 16)
e.step(A, 0, 0, 4)
for f in range(1500):
    e.step(A if f % 2 == 0 else 0, 0, 0, 2)
    if e.s16(GAME_MODE) == 4: break
def st(): return dict(mode=e.s16(GAME_MODE), enc=e.s32(0x8009A5E0), freeze=e.s32(0x8009A5B8), partner=e.s8(PLAYER_DATA + 0x12),
                      pstate=e.s8(0x8010ED70), acting=e.s8(0x8010ED73), inDis=e.s8(PLAYER + 0x15), cnt=e.s8(PLAYER + 0x14), nsc=int(bool(e.u32(PLAYER) & 0x1000)))
print('field returned', st())
e.step(0, 0, 0, 2400)
print('after 1200 frames', st())
if len(sys.argv) > 2: e.save(sys.argv[2])
