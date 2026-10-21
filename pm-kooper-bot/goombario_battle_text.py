"""Goombario tattle (C-down) timed against an enemy contact (nok_13, Goombario out, walking south of the Koopa and
then north into it). Finds the contact frame C with no C-down, then presses C-down on C-K for each K and logs what
the tattle and the encounter do (partner action state, input count, freeze mode, game mode).
usage: goombario_battle_text.py [SHOTDIR]"""
import math, os, subprocess, sys
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT, FREEZE = 0x8009A5E0, 0x8010ED70, 0x8009A5B8
PATH = [(-760, 20), (-650, 20), (-650, -150)]
shot = sys.argv[1] if len(sys.argv) > 1 else None
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gbt')
e.load('states/nok13_e0_laki.st'); e.step(0, 0, 0, 20)
base = '/dev/shm/pmbot/gbt.st'; e.save(base)
def run(cd, n=400, k_shot=None):
    e.load(base); k = 0; c = None; rows = []
    for f in range(n):
        p = player(e)
        tx, tz = PATH[k]
        if math.hypot(tx - p['x'], tz - p['z']) < 15 and k < len(PATH) - 1: k += 1
        st = stick_world(e, math.degrees(math.atan2(tx - p['x'], -(tz - p['z']))) % 360)
        e.step(D_CBUTTON if f == cd else 0, st[0], st[1], 2)
        r = (e.s16(GAME_MODE), e.s32(ENC), e.s8(PSTAT), e.s8(PLAYER + 0x15), e.s32(FREEZE), e.u8(PLAYER + PS_ACTION))
        if c is None and r[1] == 3: c = f
        if not rows or r != rows[-1][1]: rows.append((f, r))
        if shot and k_shot is not None and c is not None and f == c + 150:
            subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '-resize', '50%', os.path.join(shot, 'gbt_%s.png' % k_shot)])
    return c, rows
c0, _ = run(-1)
print('contact frame without C-down', c0)
for K in range(-8, 1):
    c, rows = run(c0 + K, 400, K)
    print('C-down at C%+d: contact %s' % (K, c), rows[:8])
