"""Can Bombette's post-blast state (BOMBETTE_3, interaction gate open) be extended by Mario falling out of bounds while
she falls? kmr_11 (after the Goomba King) with Bombette: the strip behind Bush2 has an open void east edge at x ~-200.
Mario is placed on the strip facing west (so Bombette walks west), C-down, then walks east off the edge at game
frame WALK (relative to C-down). Logs partner state / Bombette y / Mario y / action / mode every LOG frames.
usage: bombette_oob.py WALK FRAMES [LOG]"""
import sys
from emu import *
from pm import *
PSTAT = 0x8010ED70
walk, frames = int(sys.argv[1]), int(sys.argv[2])
logk = int(sys.argv[3]) if len(sys.argv) > 3 else 30
e = Emu('pm-jp.z64', '/dev/shm/pmbot/boob')
e.load('states/kmr11_e0_bombette.st'); e.step(0, 0, 0, 2)
e.w8(game_status(e) + 0x74, 1)
e.wf32(PLAYER + PS_POS, -230.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, 10.0)
e.step(0, 0, 0, 40)
e.step(0, -80, 0, 2); e.step(0, 0, 0, 10)                   # face west
def bomb(): return [n for n in npcs(e) if n['id'] == -4][0]
e.step(D_CBUTTON, 0, 0, 2)
prev = None
for f in range(frames):
    st = (0, 56, -56) if f >= walk and f < walk + 40 else (0, 0, 0)
    e.step(*st, 2)
    s = e.s8(PSTAT); b = bomb(); p = player(e)
    key = (s, p['action'], e.s16(GAME_MODE))
    if f % logk == 0 or key != prev:
        print('f%5d state %d bomb y %10.1f vel? mario (%.1f, %10.1f, %.1f) act %2d mode %d map %s ign %d' % (
            f, s, b['y'], p['x'], p['y'], p['z'], p['action'], e.s16(GAME_MODE), where(e), 1 if b['flags'] & 0x100 else 0), flush=True)
        prev = key
