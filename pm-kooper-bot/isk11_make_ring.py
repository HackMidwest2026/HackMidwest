"""isk_11: walk to the push start (-110, 508) left of the leftmost pedestal, fill the move history so Laki idles in
follow state 5 with his target frozen there, save OUT.st. (Phase 1 of isk11_push.py.)"""
import math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
from nav import go_to
IDX, PTR, STATE, HIST = 0x8010D178, 0x8010D17C, 0x8010D188, 0x8010CEF8
SX, SZ = float(os.environ.get("SX", "-110")), 508.0
e = Emu('pm-jp.z64', '/dev/shm/pmbot/imr')
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
go_to(e, SX + 50, SZ + 10, maxf=300); go_to(e, SX, SZ, maxf=200, tol=3)
for i in range(60): e.step(0, 0, 0, 2)
for k in range(400):
    e.step(0, *stick_for(-90 if k % 2 == 0 else 90, 25), 2)
    if e.u32(IDX) == (e.u32(PTR) - 1) % 40: break
for i in range(10): e.step(0, 0, 0, 2)
p = e.u32(PTR); print('ring: state', e.u32(STATE) >> 16, 'ptr', p, 'target', e.f32(HIST + 16 * p + 4), e.f32(HIST + 16 * p + 12), player(e))
e.save(sys.argv[1])
