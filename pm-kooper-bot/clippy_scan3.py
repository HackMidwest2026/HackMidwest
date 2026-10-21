"""Clippy scan, normal contact (nok_13, riding Laki; path south of the Koopa then north into it; Mario touches it on
game frame 44 while still in RIDE, no first strike). C-right on CR, cursor moved on CR+D-6 (MOVE: -80 Goombario,
+80 Bombette), A on CR+D. Logs the collision counter (PlayerStatus+0x14) min/max and when it goes negative.
usage: clippy_scan3.py CR0 CR1 D0 D1 [MOVE]  or  clippy_scan3.py trace CR D MOVE"""
import json, math, sys
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT = 0x8009A5E0, 0x8010ED70
PATH = [(-760, 20), (-650, 20), (-650, -150)]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cls3')
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 60)
base = '/dev/shm/pmbot/cls3_base.st'; e.save(base)
def row():
    return (e.s16(GAME_MODE), e.s32(ENC), e.s8(PLAYER_DATA + 0x12), e.s8(PSTAT), e.u8(PLAYER + PS_ACTION),
            e.s8(PLAYER + 0x14), int(bool(e.u32(PLAYER) & 0x1000)), e.s8(PLAYER + 0x15))
def run(cr, d, move, n=200, trace=False, hook=None):
    e.load(base)
    k, lo, neg = 0, 99, None
    last = None
    for f in range(n):
        p = player(e)
        tx, tz = PATH[k]
        if math.hypot(tx - p['x'], tz - p['z']) < 15 and k < len(PATH) - 1: k += 1
        st = stick_world(e, math.degrees(math.atan2(tx - p['x'], -(tz - p['z']))) % 360) if f < cr else (0, 0)
        if cr + d - 6 <= f < cr + d - 4: st = (0, move)
        b = R_CBUTTON if f == cr else (A if f == cr + d else 0)
        e.step(b, st[0], st[1], 2)
        r = row()
        if hook: hook(f, r)
        if trace and r != last: print(f, r)
        last = r
        lo = min(lo, r[5])
        if r[5] < 0 and neg is None: neg = f
    return {'cr': cr, 'd': d, 'move': move, 'lo': lo, 'neg': neg, 'end': row()}
if __name__ == '__main__':
    if sys.argv[1] == 'trace':
        print(run(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), 200, True)); sys.exit()
    cr0, cr1, d0, d1 = (int(a) for a in sys.argv[1:5]); mv = int(sys.argv[5]) if len(sys.argv) > 5 else -80
    for cr in range(cr0, cr1 + 1):
        for d in range(d0, d1 + 1, 2):
            print(json.dumps(run(cr, d, mv)), flush=True)
