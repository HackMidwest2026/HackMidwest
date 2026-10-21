"""Lakilester remount speed after a dismount (isk_11 west -520 floor, no RAM edits): ride Laki to START, dismount
(C-down) while holding world direction DIR, keep holding, and remount (C-down) on frame k after the dismount press.
Reports the speed the mount reads (Laki's moveSpeed on the C-down frame).
  A: hold DIR only, scan k.
  B: hold DIR, Z (spin) on the frame Mario lands from the dismount, A for 1 frame J frames after the spin press,
     C-down K frames after the jump press; scan J and K.
usage: laki_remount_speed.py [DIR] [SX SZ]   env SPEEDY=1 equips Speedy Spin (RAM)"""
import math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
from nav import go_to
DIR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0          # corner_sweep world angle: 0 = +x
SX, SZ = (float(a) for a in sys.argv[2:4]) if len(sys.argv) > 3 else (-300.0, 560.0)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lrs')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
import os
if os.environ.get('SPEEDY'):                                  # Speedy Spin badge (item 287) owned + equipped (RAM)
    e.w16(PLAYER_DATA + 0xB4, 287); e.w16(PLAYER_DATA + 0x208, 287)
go_to(e, SX, SZ, maxf=300); e.step(0, 0, 0, 30)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(60):
    e.step(0, 0, 0, 2)
    if e.u8(PLAYER + PS_ACTION) == 33: break
e.step(0, 0, 0, 30)
st = stick_for(DIR, 80)
for i in range(6): e.step(0, st[0], st[1], 2)              # riding, moving in DIR
base = '/dev/shm/pmbot/lrs_ride.st'; e.save(base)
def mount_speed():
    a = laki()['addr']
    for i in range(12):
        if e.u8(PLAYER + PS_ACTION) == 33: return e.f32(a + 0x18)
        e.step(0, 0, 0, 2)
    return None
def dismount():
    e.load(base); e.step(D_CBUTTON, st[0], st[1], 2)
    for i in range(40):                                     # wait until Mario is off Laki and landed
        e.step(0, st[0], st[1], 2)
        if e.u8(PLAYER + PS_ACTION) in (0, 1, 2) and i > 2: return i + 2
    return None
# A
best = (0, None); rowA = []
for k in range(1, 40):
    land = dismount()
    if land is None: break
    e.load(base); e.step(D_CBUTTON, st[0], st[1], 2)
    for i in range(1, k): e.step(0, st[0], st[1], 2)
    e.step(D_CBUTTON, st[0], st[1], 2)
    s = mount_speed(); rowA.append((k, None if s is None else round(s, 2)))
    if s is not None and s > best[0]: best = (s, k)
print('landing frame after the dismount press:', land)
print('A: hold only; mount speed by C-down frame k:', rowA)
print('A best: %.2f on k=%s' % best)
# B
bestB = (0, None); tab = {}
for J in range(1, 21):
    for K in range(1, 36):
        e.load(base); e.step(D_CBUTTON, st[0], st[1], 2); f = 1
        while f < land: e.step(0, st[0], st[1], 2); f += 1
        e.step(Z, st[0], st[1], 2)                          # spin on landing
        for i in range(1, J): e.step(0, st[0], st[1], 2)
        e.step(A, st[0], st[1], 2)                          # 1-frame jump
        for i in range(1, K): e.step(0, st[0], st[1], 2)
        e.step(D_CBUTTON, st[0], st[1], 2)
        s = mount_speed()
        if s is not None:
            tab[(J, K)] = round(s, 2)
            if s > bestB[0]: bestB = (s, (J, K))
print('B best: %.2f with jump J=%s frames after the spin, C-down K=%s frames after the jump' % (bestB[0], bestB[1][0] if bestB[1] else None, bestB[1][1] if bestB[1] else None))
top = sorted(tab.items(), key=lambda kv: -kv[1])[:8]
print('B top:', top)
print('delta B - A: %.2f' % (bestB[0] - best[0]))
