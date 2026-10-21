"""Goombario off an out-of-bounds edge (mac_01 west grass, edge (-625,259)-(-259,625)). Mario is placed OUT units
from the edge (negative = inside), faces inland; then B is held and C-down tapped every 40 game frames (each tattle
opens and B closes it; Goombario re-faces Mario and walks to the other side). The first frame Goombario is not
grounded, C-down is pressed (JP: SelectTattleMsg returns without a message when he is airborne -> TattleEnd).
Logs Goombario / Mario / partner state. usage: goomb_ledge.py OUT [EX [PER]] (PER: game frames between C-down taps)"""
import math, sys
from emu import *
from pm import *
from nav import stick_world
OUT = float(sys.argv[1]); EX = float(sys.argv[2]) if len(sys.argv) > 2 else -470; PER = int(sys.argv[3]) if len(sys.argv) > 3 else 40
ez = EX + 884
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gbl')
e.load('states/mac01_e0_goomb.st'); e.step(0, 0, 0, 2)
mx, mz = EX - OUT / math.sqrt(2), ez + OUT / math.sqrt(2)
e.wf32(PLAYER + PS_POS, mx); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, mz)
gk = [n for n in npcs(e) if n['id'] == -4][0]['addr']
e.wf32(gk + 0x38, mx + 25); e.wf32(gk + 0x3C, 20.0); e.wf32(gk + 0x40, mz - 25)
e.step(0, 0, 0, 200)
s = stick_world(e, 45, 30); e.step(0, s[0], s[1], 2); e.step(0, 0, 0, 60)
def g(): return [n for n in npcs(e) if n['id'] == -4][0]
def out(x, z): return (-(x - EX) + (z - ez)) / math.sqrt(2)
p = player(e); print('mario out %.1f' % out(p['x'], p['z']), p)
pressed = None; last = None
for f in range(600):
    q = g(); fl = e.u32(q['addr'])
    b = B
    if f % PER == 20: b |= D_CBUTTON
    if pressed is None and not fl & 0x1000 and q['y'] < 19.9 and e.s8(PLAYER + 0x15) == 0:
        b = D_CBUTTON; pressed = f
    e.step(b, 0, 0, 2)
    q = g(); fl = e.u32(q['addr']); p = player(e)
    r = (round(q['y']) if q['y'] > -100 else '<-100', bool(fl & 0x1000), e.s8(0x8010ED70), e.s8(0x8010ED73), e.s8(PLAYER + 0x15), e.s32(0x8009A5B8), p['action'])
    if r != last or f == pressed: print(f, 'goomb (%.1f %.1f %.1f) out %.1f' % (q['x'], q['y'], q['z'], out(q['x'], q['z'])), 'y/grounded/pstate/acting/inDis/freeze/act', r, '<- C-down' if f == pressed else '')
    last = r
print('C-down pressed at', pressed, 'mario', player(e))
