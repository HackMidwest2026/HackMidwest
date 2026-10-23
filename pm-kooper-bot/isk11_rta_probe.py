"""RTA-style probe (inputs only): from isk11_laki_ready.st walk to START, wait, tap TAP stick for TAPF frames, wait,
then hold raw stick HOLD for N frames. Logs every few frames: Mario, Laki, follow state, history write slot (idx),
Laki's slot (ptr), and the target Laki would fly to. usage: isk11_rta_probe.py  env START TAP TAPF HOLD N EVERY SAVE"""
import math, os, sys
from emu import *
from pm import *
from nav import go_to
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
P = lambda k, d: [float(v) for v in os.environ.get(k, d).split(',')]
WPS = [[float(v) for v in w.split(',')] for w in os.environ.get('START', '-180,580').split(';')]; TAP = [int(v) for v in P('TAP', '-80,0')]; TAPF = int(os.environ.get('TAPF', '1'))
HOLD = [int(v) for v in P('HOLD', '60,40')]; N = int(os.environ.get('N', '150')); EV = int(os.environ.get('EVERY', '5'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rp%d' % os.getpid())
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
for w in WPS: go_to(e, w[0], w[1], maxf=300, tol=3)
for i in range(30): e.step(0, 0, 0, 2)
for i in range(TAPF): e.step(0, TAP[0], TAP[1], 2)
for i in range(30): e.step(0, 0, 0, 2)
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
def show(tag):
    p, l = player(e), lk(); ptr = e.u32(PTR)
    print(tag, 'M (%.0f %.0f %.0f) L (%.0f %.0f %.0f) st %d idx %d ptr %d tgt (%.0f %.0f) dML %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, e.u32(IDX), ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12), math.hypot(p['x'] - l['x'], p['z'] - l['z'])))
show('ready')
for f in range(N):
    e.step(0, HOLD[0], HOLD[1], 2)
    if f % EV == 0: show('f%03d' % f)
if os.environ.get('SAVE'): e.save(os.environ['SAVE'])
