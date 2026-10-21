"""Clippy without RAM placement (nok_13, riding Lakilester; the only RAM writes are the Lucky Star flag and the Spike
Shield badge). Ride south of the Koopa and then north into it, so Mario touches it himself (no first strike). On the
contact frame (found by rewinding one frame) press C-right: the partner menu opens during the battle wind-up and stays
open through the battle. In battle: Strategies -> Run Away, mash A. Back on the field the menu is still open: cursor
down (MOVE -80 = Goombario, +80 = Bombette), A. Logs the collision counter (PlayerStatus+0x14) and flag.
usage: clippy_natural.py MOVE OUT.st"""
import math, sys
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT, FREEZE = 0x8009A5E0, 0x8010ED70, 0x8009A5B8
PATH = [(-760, 20), (-650, 20), (-650, -150)]
MOVE, outp = int(sys.argv[1]), sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cln')
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2)
e.w8(PLAYER_DATA + 0x0A, 1)                                         # hasActionCommands (Lucky Star)
e.w16(PLAYER_DATA + 0xB4, 229); e.w16(PLAYER_DATA + 0x208, 229)     # Spike Shield owned + equipped
e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 60)
def st(): return dict(mode=e.s16(GAME_MODE), enc=e.s32(ENC), freeze=e.s32(FREEZE), partner=e.s8(PLAYER_DATA + 0x12),
                      pstate=e.s8(PSTAT), inDis=e.s8(PLAYER + 0x15), cnt=e.s8(PLAYER + 0x14), nsc=int(bool(e.u32(PLAYER) & 0x1000)), act=e.u8(PLAYER + PS_ACTION))
tmp = '/dev/shm/pmbot/cln_t.st'; k = 0; c = None
for f in range(300):
    p = player(e); tx, tz = PATH[k]
    if math.hypot(tx - p['x'], tz - p['z']) < 15 and k < len(PATH) - 1: k += 1
    s = stick_world(e, math.degrees(math.atan2(tx - p['x'], -(tz - p['z']))) % 360)
    e.save(tmp); e.step(0, s[0], s[1], 2)
    if e.s32(ENC) == 3:
        e.load(tmp); e.step(R_CBUTTON, s[0], s[1], 2); c = f; break
print('contact frame', c, 'action', e.u8(PLAYER + PS_ACTION), st())
while e.s16(GAME_MODE) != 8: e.step(0, 0, 0, 2)
e.step(0, 0, 0, 240)                                                # battle intro; menu wheel up
print('in battle', st())
for i in range(2): e.step(0, 0, 70, 4); e.step(0, 0, 0, 20)          # wheel up x2: Strategies
e.step(A, 0, 0, 4); e.step(0, 0, 0, 30)
for i in range(2): e.step(0, 0, -70, 4); e.step(0, 0, 0, 16)         # Run Away
e.step(A, 0, 0, 4)
for f in range(1500):
    if e.s16(GAME_MODE) == 4: break
    e.step(A if f % 2 == 0 else 0, 0, 0, 2)
for f in range(400):
    if e.s32(FREEZE) == 3: break
    e.step(0, 0, 0, 2)
e.step(0, 0, 0, 20)
print('field, menu open', st())
e.step(0, 0, MOVE, 4); e.step(0, 0, 0, 12); e.step(A, 0, 0, 4)
for f in range(200): e.step(0, 0, 0, 2)
print('after picking', st(), player(e))
e.save(outp)
