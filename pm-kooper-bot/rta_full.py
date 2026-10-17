"""Full simple-input ending from the top-right corner, with the real Lakilester:
up 10, right 10 (very top-right corner), down 6, A + down N, neutral 4, left until the drop onto step 3 (released
during the forced drop), neutral 8, left T frames, then hold up (Mario funnels into the corner at z -145). While up is
held, try C-down on every frame f with stick DIR on that same frame (default left); follow 60 frames and report which
f clip and Laki's frozen speed. usage: rta_full.py [N=26] [T=6] [DIR=left] [F=200]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
DIRS = {'up': 270, 'down': 90, 'left': 180, 'right': 0, 'upleft': 225, 'downleft': 135, 'none': None}
N, T = int(os.environ.get('N', 26)), int(os.environ.get('T', 6))
D = os.environ.get('DIR', 'left'); DS = stick_for(DIRS[D], 80) if DIRS[D] is not None else (0, 0)
F = int(os.environ.get('F', 200))
U_, R_, Dn, L = stick_for(270, 80), stick_for(0, 80), stick_for(90, 80), stick_for(180, 80)
w = '/dev/shm/pmbot/rfull%d' % os.getpid()
e = Emu(os.environ['PM_ROM'], w)
def laki():
    return [n for n in npcs(e) if n['id'] == -4][0]
e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2)
fr = 0
HIST, IDX, PTR = 0x8010CEF8, 0x8010D178, 0x8010D17C
LOG = int(os.environ.get('LOG', 0))
def st(b, s):
    global fr
    e.step(b, *s, 2); fr += 1
    if LOG and fr % LOG == 0:
        p, l = player(e), laki(); ptr = e.u32(PTR)
        tx, tz = e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)
        ix = e.u32(IDX)
        print('fr %3d M (%.1f,%.1f,%.1f) a%d  L (%.1f,%.1f) ly %.1f spd %.1f idx %d ptr %d tgt (%.0f,%.0f) last (%.0f,%.0f)' % (fr, p['x'], p['y'], p['z'], p['action'], l['x'], l['z'], l['y'], l['speed'], ix, ptr, tx, tz, e.f32(HIST + 16 * ix + 4), e.f32(HIST + 16 * ix + 12)))
for i in range(10): st(0, U_)
for i in range(10): st(0, R_)
for i in range(6): st(0, Dn)
for i in range(N): st(0x80 if i < 12 else 0, Dn)
for i in range(4): st(0, (0, 0))
while player(e)['action'] != 9: st(0, L)
for i in range(8): st(0, (0, 0))
p = player(e); print('landed on step 3 at (%.2f, %.2f, %.2f), frame %d' % (p['x'], p['y'], p['z'], fr))
for i in range(T): st(0, L)
for i in range(2): st(0, (0, 0))
p = player(e); print('after left %d: x %.2f' % (T, p['x']))
hits = []
PRE = int(os.environ.get('PRE', 0)); F0 = int(os.environ.get('F0', 0))
for i in range(F0): st(0, U_)
for f in range(F0, F):
    e.save(w + '/s.st')
    for i in range(PRE): e.step(0, *DS, 2)
    st(CD, DS)
    l = laki(); spd = l['speed']; pc = player(e)
    for i in range(60): e.step(0, 0, 0, 2)
    p = player(e); ok = p['z'] > 1
    if ok or f % 10 == 0 or 25 <= f <= 55:
        print('f %3d (frame %d) Mario at C-down (%.2f, %.2f) Laki speed %.2f -> %s' % (f, fr, pc['x'], pc['z'], spd, 'CLIP' if ok else '-'))
    if ok: hits.append(f)
    e.load(w + '/s.st'); st(0, U_)
print('clipping frames:', hits)
