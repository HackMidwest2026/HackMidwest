"""kpa_17 jail: how much Laki speed does the mount push (C-down teleport) need to get Mario through the bombable
doorway block (x 1200..1280, z -600..-550) onto the exit floor (collider 14)? Mario walks into the doorway, Laki's
moveSpeed and yaw are set in RAM on the C-down frame, then the mount is played out and Mario's floor/position/map logged.
usage: kpa17_push_test.py STATE S1,S2,... [YAW=90] [Z=-575]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
st0 = sys.argv[1]; speeds = [float(v) for v in sys.argv[2].split(',')]
YAW = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0; Z = float(sys.argv[4]) if len(sys.argv) > 4 else -575.0
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kpt%d' % os.getpid())
for S in speeds:
    e.load(st0); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS + 8, Z)
    for i in range(30): e.step(0, *stick_for(0, 80), 2)      # into the doorway (east)
    for i in range(3): e.step(0, 0, 0, 2)
    p0 = player(e); a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
    e.wf32(a + 0x18, S); e.wf32(a + 0x0C, YAW)
    e.step(0x400, 0, 0, 2)
    e.wf32(a + 0x18, S); e.wf32(a + 0x0C, YAW)
    maxx, out = p0['x'], None
    for i in range(80):
        e.step(0, 0, 0, 2)
        if e.s16(GAME_MODE) != GM_WORLD: out = 'map change -> %s' % (where(e),); break
        p = player(e); maxx = max(maxx, p['x'])
    p = player(e)
    print('speed %6.1f: start x %.1f, max x %.1f, end (%.1f %.1f %.1f) act %d floor %d %s' % (S, p0['x'], maxx, p['x'], p['y'], p['z'], p['action'], e.s16(COLLISION + 2), out or ''))
