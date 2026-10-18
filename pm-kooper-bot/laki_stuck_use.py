"""Can the stuck state be turned into Laki speed? Builds the stuck state (laki_ptr0 inputs with walk-left A=19) and a
control (A=24, normal idle), then from each runs an "unstick" action (pause, menus, jump, spin jump, hammer, walks,
C-down) and logs Laki's follow state, speed and distance for 90 frames.
usage: laki_stuck_use.py STATE [ACTION ...]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu, START, Z, B, A, R_CBUTTON, L_CBUTTON, D_CBUTTON
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0 = sys.argv[1]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lsu%d' % os.getpid())
_last = [None]
def laki():
    L = [n for n in npcs(e) if n['id'] == -4]
    if L: _last[0] = L[0]
    return _last[0]  # npc list is hidden while paused / in menus: keep the last value
def build(A_left, path):
    if os.path.exists(path): return
    e.load(st0); e.step(0, 0, 0, 2)
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for i in range(36): e.step(0, *stick_for(0, 80), 2)
    for i in range(40): e.step(0, 0, 0, 2)
    for f in range(200): e.step(0, *(up if f % 2 == 0 else dn), 2)
    for i in range(5): e.step(0, 0, 0, 2)
    for i in range(A_left): e.step(0, *stick_for(180, 80), 2)
    for i in range(200): e.step(0, 0, 0, 2)
    e.save(path)
W = lambda d, n=20: [(0, stick_for(d, 80))] * n
ACTIONS = {
    'none': [], 'pause': [(START, (0, 0))] + [(0, (0, 0))] * 40 + [(START, (0, 0))],
    'cleft_menu': [(L_CBUTTON, (0, 0))] + [(0, (0, 0))] * 30 + [(B, (0, 0))],
    'cright_menu': [(R_CBUTTON, (0, 0))] + [(0, (0, 0))] * 30 + [(B, (0, 0))],
    'jump': [(A, (0, 0))] * 6, 'spinjump': [(A, (0, 0))] * 6 + [(Z, (0, 0))], 'hammer': [(B, (0, 0))],
    'walk_left': W(180), 'walk_right': W(0), 'walk_up': W(270), 'walk_down': W(90), 'walk_left_long': W(180, 60),
    'cdown': [(D_CBUTTON, (0, 0))],
}
names = sys.argv[2:] or list(ACTIONS)
for tag, A_left in (('stuck', 19), ('control', 24)):
    path = 'states/laki_%s.st' % tag; build(A_left, path)
    for nm in names:
        e.load(path); e.step(0, 0, 0, 2)
        seq = ACTIONS[nm] + [(0, (0, 0))] * (90 - len(ACTIONS[nm]))
        best = (0, 0); rows = []
        for f, (b, s) in enumerate(seq):
            e.step(b, *s, 2)
            p, l = player(e), laki(); d = math.hypot(p['x'] - l['x'], p['z'] - l['z'])
            if l['speed'] > best[0]: best = (l['speed'], f)
            rows.append('%d:%d/%.1f/%.0f' % (f, e.u32(STATE) >> 16, l['speed'], d))
        print('%-7s %-15s max Laki speed %6.2f at f%-3d  end state %d dist %.1f  Mario (%.1f %.1f %.1f) act %d' % (tag, nm, best[0], best[1], e.u32(STATE) >> 16, d, p['x'], p['y'], p['z'], p['action']))
        if os.environ.get('V'): print('   ', ' '.join(rows[:60]))
