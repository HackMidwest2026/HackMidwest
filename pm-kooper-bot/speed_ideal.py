"""Idealized multi-frame check of the turnaround: Mario standing in the clip strip (MX, -20, MZ); Lakilester planted at
the rock turnaround (555, LY, -13) in follow state 0, with every history entry from his pointer on set to the far
point (HX, HY, HZ) (Mario's position when the first new history was recorded). Step 12 frames and print his speed
each frame: shows how the climb from below Mario (speed capped at 6) eats into the peak.
usage: speed_ideal.py"""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/si')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
for MX, MZ in ((884, -144), (878, -100)):
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, float(MX)); e.wf32(PLAYER + PS_POS + 4, -17.0); e.wf32(PLAYER + PS_POS + 8, float(MZ))
    for i in range(15): e.step(0, 0, 0, 2)
    e.save('/dev/shm/pmbot/si/b.st')
    for LY in (-40.0, -20.0):
        for HX, HY, HZ in ((987, -30, -212), (987, 0, -165), (987, 30, -212), (987, 60, -212)):
            e.load('/dev/shm/pmbot/si/b.st'); e.step(0, 0, 0, 2)
            l = laki()
            e.wf32(l['addr'] + 0x38, 555.0); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, -13.0)
            e.w32(PTR, 5); e.w32(IDX, 25)
            for k in range(40):
                a = HIST + 16 * k; e.wf32(a + 4, HX); e.wf32(a + 8, HY); e.wf32(a + 12, HZ)
            e.w16(STATE, 0)
            sp = []
            for f in range(12):
                e.step(0, 0, 0, 2)
                l = laki(); sp.append((round(l['speed'], 1), round(l['y'], 1)))
            print('Mario (%d, %d)  Laki y %d  next point (%d, y %d, %d): best %.1f  per frame (speed, laki y): %s' % (MX, MZ, LY, HX, HY, HZ, max(s for s, _ in sp), HX and sp[:8]))
