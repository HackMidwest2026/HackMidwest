"""Test the "early Laki" hypothesis: Lakilester with his follow AI switched off (wPartnerFollowState 50, as a
partner-joining cutscene leaves it until EnablePartnerAI). Optionally also set D_8010CFC4 = 2 (the instant take-out
marker) and walk through a loading zone to see if the AI stays off in the next room.
usage: laki_ai_off.py STATE [MODE=state50|cfc4]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE, CFC4 = 0x8010D188, 0x8010D184
st0 = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else 'state50'
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lao%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
print('before: follow state %d  D_8010CFC4 %d' % (e.u32(STATE) >> 16, e.u32(CFC4)))
def log(t):
    p = player(e); ls = [n for n in npcs(e) if n['id'] == -4]
    l = ls[0] if ls else {'x': 0, 'y': 0, 'z': 0, 'speed': 0}
    print('%-26s map %s  st %3d cfc4 %d  M (%7.1f %6.1f %7.1f)  L (%7.1f %6.1f %7.1f) dist %.1f' % (t, where(e), e.u32(STATE) >> 16, e.u32(CFC4),
          p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], math.hypot(p['x'] - l['x'], p['z'] - l['z'])))
if MODE == 'state50':
    e.w16(STATE, 50)
    log('set state 50')
    for nm, d, n in (('walk right 40', 0, 40), ('stand 30', None, 30), ('walk left 60 (into Laki)', 180, 60), ('stand 30', None, 30),
                     ('walk right 60', 0, 60), ('stand 30', None, 30)):
        for i in range(n): e.step(0, *(stick_for(d, 80) if d is not None else (0, 0)), 2)
        log(nm)
    e.step(0x0400, 0, 0, 2)
    for i in range(60): e.step(0, 0, 0, 2)
    log('C-down + 60')
else:
    e.w32(CFC4, 2)
    for i in range(400):
        e.step(0, *stick_for(180, 80), 2)
        if i % 40 == 0: log('walk left %d' % i)
    for i in range(120): e.step(0, 0, 0, 2)
    log('stand 120 (new room)')
    for i in range(60): e.step(0, *stick_for(0, 80), 2)
    for i in range(60): e.step(0, 0, 0, 2)
    log('walk right 60, stand 60')
