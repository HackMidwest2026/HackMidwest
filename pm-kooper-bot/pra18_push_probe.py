"""pra_18 north side: Lakilester stop-and-go push (walk into Laki 1 frame, stand 2 frames, repeat) as a speed source.
DIAGNOSTIC SETUP: Mario placed at START, mounts and dismounts (resets Laki's follow history so no stale point from the
placement), then pushes Laki toward DIR until Mario's x passes X_END; then walks away holding AWAY and the script logs
Laki's moveSpeed every frame. usage: pra18_push_probe.py"""
import os, sys, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pp')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
def prep(x, z):
    e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 8, z)                         # DIAGNOSTIC
    for i in range(20): e.step(0, 0, 0, 2)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(D_CBUTTON, 80, 0, 2)                                                         # get off facing right
    for i in range(60): e.step(0, 0, 0, 2)
def show(tag):
    p = player(e); L = laki()
    return '%s mario (%.1f,%.1f) laki (%.1f,%.1f) spd %.2f' % (tag, p['x'], p['z'], e.f32(L['addr'] + 0x38), e.f32(L['addr'] + 0x40), e.f32(L['addr'] + 0x18))
for x0, push, away in ((720, (-80, 0), (0, 80)), (720, (-80, 0), (80, 0)), (540, (80, 0), (0, 80))):
    prep(float(x0), -60.0)
    print('== start', show(''))
    # put Laki on the push side: walk around him first if needed
    L = laki(); lx = e.f32(L['addr'] + 0x38)
    print('   laki before push at x %.1f' % lx)
    for k in range(60):
        e.step(0, *push, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    print('  ', show('after push'))
    for f in range(30):
        e.step(0, *away, 2)
        if f % 2 == 1 or f < 12: print('   away %2d' % f, show(''))
