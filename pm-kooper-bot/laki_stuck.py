"""Reproduce the Lakilester stuck/drift glitch: teleport Laki to (LX, LY, LZ) with a wall between him and Mario at
(MX, MZ), let Mario stand still for N frames and log Laki's follow state, history pointer vs index, position and speed;
then Mario takes one step (dir, 1 frame) and logs on. usage: laki_stuck.py STATE LX LY LZ MX MZ [N=120] [DIR=L]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0 = sys.argv[1]; LX, LY, LZ, MX, MZ = map(float, sys.argv[2:7])
N = int(sys.argv[7]) if len(sys.argv) > 7 else 120; DIR = sys.argv[8] if len(sys.argv) > 8 else 'L'
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ls%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 8, MZ)
for i in range(20): e.step(0, 0, 0, 2)
l = laki(); e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
prev = None
def show(f, tag=''):
    global prev
    p, l = player(e), laki()
    key = (e.u32(STATE) >> 16, e.u32(PTR), e.u32(IDX))
    pos = (round(l['x'], 2), round(l['y'], 2), round(l['z'], 2))
    if key != prev or f % 15 == 0 or tag:
        print('%4d %-6s M (%.1f, %.1f) L %s spd %.2f flags %08x state %d ptr %d idx %d' % (f, tag, p['x'], p['z'], pos, l['speed'], l['flags'], *key))
    prev = key
for f in range(N): e.step(0, 0, 0, 2); show(f)
s = {'L': stick_for(180, 80), 'R': stick_for(0, 80), 'U': stick_for(270, 80), 'D': stick_for(90, 80)}[DIR]
e.step(0, *s, 2); show(N, 'step')
for f in range(N + 1, N + 60): e.step(0, 0, 0, 2); show(f)
