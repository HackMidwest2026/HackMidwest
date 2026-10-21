"""Scan the frame Mario walks off the kmr_11 strip edge (south-east into the void) relative to Bombette's C-down, and
report how long Bombette's BOMBETTE_3 state lasts and where she / Mario end up. usage: bombette_oob_scan.py W0 W1 STEP FRAMES"""
import sys
from emu import *
from pm import *
PSTAT = 0x8010ED70
w0, w1, wst, frames = (int(a) for a in sys.argv[1:5])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/boobs')
e.load('states/kmr11_e0_bombette.st'); e.step(0, 0, 0, 2)
e.w8(game_status(e) + 0x74, 1)
e.wf32(PLAYER + PS_POS, -230.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, 10.0)
e.step(0, 0, 0, 40)
e.step(0, -80, 0, 2); e.step(0, 0, 0, 10)
e.step(D_CBUTTON, 0, 0, 2)
e.step(0, 0, 0, 1); base = '/dev/shm/pmbot/boobs_base.st'; e.save(base)
def bomb(): return [n for n in npcs(e) if n['id'] == -4][0]
for w in range(w0, w1 + 1, wst):
    e.load(base)
    s3, end3, lift_my, respawn_f, minmy = None, None, None, None, 1e9
    prevy = 0
    for f in range(frames):
        st = (0, 56, -56) if w <= f < w + 40 else (0, 0, 0)
        e.step(*st, 2)
        s = e.s8(PSTAT); p = player(e)
        minmy = min(minmy, p['y'])
        if s == 3 and s3 is None: s3, lift_my = f, p['y']
        if s3 is not None and s != 3 and end3 is None: end3 = f
        if p['y'] - prevy > 300 and respawn_f is None: respawn_f = f
        prevy = p['y']
    b = bomb(); p = player(e)
    dur = (end3 - s3) if end3 is not None else ('still open after %d' % (frames - s3) if s3 is not None else None)
    print('walk %3d: window from f%s, mario y at liftoff %s, respawn f%s, window length %s, end: state %d bomb y %.1f mario (%.1f, %.1f, %.1f) act %d' % (
        w, s3, None if lift_my is None else round(lift_my, 1), respawn_f, dur, e.s8(PSTAT), b['y'], p['x'], p['y'], p['z'], p['action']), flush=True)
