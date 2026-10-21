"""Finish the clippy-setup battle with a win (exploration only: enemy HP set to 1, Ultra Hammer, Mario HP held).
Each cycle: stick down (hammer), A presses. Then logs the field state (encounter, freeze, partner, input count,
collision counter, NO_STATIC_COLLISION) and saves it.
usage: clippy_win.py BATTLE.st FIELD_OUT.st"""
import sys
from emu import *
from pm import *
BS = 0x800DC050
e = Emu('pm-jp.z64', '/dev/shm/pmbot/clwin')
e.load(sys.argv[1])
e.w8(PLAYER_DATA + 1, 2)
def st(): return dict(mode=e.s16(GAME_MODE), enc=e.s32(0x8009A5E0), freeze=e.s32(0x8009A5B8), partner=e.s8(PLAYER_DATA + 0x12),
                      pstate=e.s8(0x8010ED70), acting=e.s8(0x8010ED73), inDis=e.s8(PLAYER + 0x15), cnt=e.s8(PLAYER + 0x14), nsc=int(bool(e.u32(PLAYER) & 0x1000)))
for f in range(30000):
    if e.s16(GAME_MODE) == 8:
        e.w8(PLAYER_DATA + 2, 10)
        for i in range(24):
            a = e.u32(BS + 0xE0 + 4 * i)
            if 0x80000000 <= a < 0x80800000 and e.s8(a + 0x1B8) > 1: e.w8(a + 0x1B8, 1)
    ph = f % 40
    e.step(A if ph in (10, 25) else 0, 0, -70 if ph < 3 else 0, 2)
    if e.s16(GAME_MODE) == 4 and f > 100: break
print('field returned at', f, st())
e.step(0, 0, 0, 1200)
print('after 600 frames', st(), player(e))
e.save(sys.argv[2])
