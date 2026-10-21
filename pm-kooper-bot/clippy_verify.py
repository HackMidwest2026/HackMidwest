"""Clippy mechanism check (exploration: Mario/Laki and the Koopa are placed with RAM writes). Mario rides on the
nok_13 stump spot (X, Z) where Laki's PutAway reaches FINISH_1 on its first movement frame; the Koopa is put at
(KX, KZ) and Mario pushes toward it. On the frame contact registers (found by rewinding) C-right is pressed, the
cursor moved (MOVE), A pressed D frames later. Logs the collision counter around the battle start.
usage: clippy_verify.py X Z KX KZ D MOVE [SAVE.st]"""
import math, sys
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT = 0x8009A5E0, 0x8010ED70
X, Z, KX, KZ = (float(a) for a in sys.argv[1:5]); D, MOVE = int(sys.argv[5]), int(sys.argv[6])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/clv')
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2); e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 60)
lk = [n for n in npcs(e) if n['id'] == -4][0]['addr']
for a in (lk + 0x38, PLAYER + PS_POS): e.wf32(a, X); e.wf32(a + 8, Z)
e.wf32(lk + 0x3C, 80.0); e.wf32(PLAYER + PS_POS + 4, 90.0)
e.step(0, 0, 0, 60)
kp = [n for n in npcs(e) if n['id'] == 0][0]['addr']
e.wf32(kp + 0x38, KX); e.wf32(kp + 0x3C, 75.0); e.wf32(kp + 0x40, KZ)
def row():
    return (e.s16(GAME_MODE), e.s32(ENC), e.s8(PLAYER_DATA + 0x12), e.s8(PSTAT), e.u8(PLAYER + PS_ACTION),
            e.s8(PLAYER + 0x14), int(bool(e.u32(PLAYER) & 0x1000)), e.s8(PLAYER + 0x15))
tmp = '/dev/shm/pmbot/clv_t.st'
c = None
for f in range(300):
    p = player(e)
    st = stick_world(e, math.degrees(math.atan2(KX - p['x'], -(KZ - p['z']))) % 360, 40)
    e.save(tmp)
    e.step(0, st[0], st[1], 2)
    if f % 30 == 0: print(f, [(round(n["x"]), round(n["y"]), round(n["z"])) for n in npcs(e) if n["id"] == 0], round(p["x"]), round(p["z"]))
    if e.s32(ENC) == 3:
        e.load(tmp); e.step(R_CBUTTON, st[0], st[1], 2); c = f; break
print('contact frame', c, 'action', e.u8(PLAYER + PS_ACTION), 'mario', player(e), 'row', row())
last = None
for g in range(1, 120):
    b = A if g == D else 0
    sy = MOVE if D - 6 <= g < D - 4 else 0
    e.step(b, 0, sy, 2)
    r = row()
    if r != last: print(g, r)
    last = r
if len(sys.argv) > 7: e.save(sys.argv[7])
