"""kpa_62: does Laki stay frozen while Mario stands still after the post-dismount return, and what speed does he get on
the first frame Mario moves again?
usage: kpa62_freeze.py STATE WA WK D N WAIT TAP [CDOFF]
  walk from the seed at WA for WK frames, mount, ride 40, dismount (B), hold stick D for N frames from frame 4, release,
  wait until frame WAIT, then hold TAP direction and press C-down CDOFF frames after the first TAP frame."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0 = sys.argv[1]; WA, WK, D, N, WAIT, TAP = (int(v) for v in sys.argv[2:8]); CDOFF = int(sys.argv[8]) if len(sys.argv) > 8 else 0
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kfz%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
for i in range(WK): e.step(0, *stick_for(WA, 80), 2)
for i in range(6): e.step(0, 0, 0, 2)
e.step(0x400, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
L = lambda: [q for q in npcs(e) if q['id'] == -4][0]
prog = [(0x40, 0, 0)] + [(0, 0, 0)] * 3 + [(0,) + stick_for(D, 80)] * N
prog += [(0, 0, 0)] * max(0, WAIT - len(prog))
prog += [(0,) + stick_for(TAP, 80)] * CDOFF + [(0x400,) + stick_for(TAP, 80)] + [(0,) + stick_for(TAP, 80)] * 25 + [(0, 0, 0)] * 6
for f, (b, sx, sy) in enumerate(prog):
    e.step(b, sx, sy, 2); p, l = player(e), L()
    if f % 4 == 0 or f >= WAIT - 2 and f <= WAIT + CDOFF + 8:
        print('%3d b%04x M (%7.1f %5.1f %6.1f) act %2d | L (%7.1f %5.1f %6.1f) spd %5.2f st %d' % (f, b, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], l['speed'], e.u16(0x8010D188)))
q = player(e); print('END', round(q['x'], 1), round(q['z'], 1), 'INSIDE' if inside_tower(q['x'], q['z']) else 'outside')
