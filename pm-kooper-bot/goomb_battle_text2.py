"""Goombario's tattle text into a battle. nok_13 with Goombario: Mario walks straight at the Koopa (it notices and
charges). C-down on game frame C (Mario stops; the tattle disables input and waits 3 frames, then checks whether
anything else disabled input before committing). Logs, per C: the contact frame, the partner action state on that
frame and at the battle switch, and saves a screenshot at the battle start when the tattle was active.
usage: goomb_battle_text2.py C0 C1 [SHOTDIR]"""
import math, os, subprocess, sys
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT, FREEZE = 0x8009A5E0, 0x8010ED70, 0x8009A5B8
c0, c1 = int(sys.argv[1]), int(sys.argv[2]); shot = sys.argv[3] if len(sys.argv) > 3 else None
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gbt2')
e.load(os.environ.get('GSTATE', 'states/nok13_e0_goomb.st')); e.step(0, 0, 0, 20)
base = '/dev/shm/pmbot/gbt2.st'; e.save(base)
def run(C, n=260):
    e.load(base); con = None; rows = []; got = None
    for f in range(n):
        p = player(e)
        st = stick_world(e, math.degrees(math.atan2(-650 - p['x'], -(-150 - p['z']))) % 360) if f < C else (0, 0)
        e.step(D_CBUTTON if f == C else 0, st[0], st[1], 2)
        r = (e.s16(GAME_MODE), e.s32(ENC), e.s8(PSTAT), e.s8(PLAYER + 0x15), e.s32(FREEZE), e.u8(PLAYER + PS_ACTION))
        if con is None and r[1] == 3: con = (f, r)
        if r[0] == 8 and got is None:
            got = (f, r)
            if shot and con and con[1][2] == 1 or (shot and r[2] == 1):
                e.step(0, 0, 0, 30); subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '-resize', '50%', os.path.join(shot, 'gbt2_%d.png' % C)])
            break
        rows.append(r)
    return con, got, rows
for C in range(c0, c1 + 1):
    con, got, rows = run(C)
    flag = ' <== tattle active at contact' if con and con[1][2] == 1 else ''
    print('C', C, 'contact', con, 'battle', got, 'max pstate', max(r[2] for r in rows) if rows else None, flag, flush=True)
