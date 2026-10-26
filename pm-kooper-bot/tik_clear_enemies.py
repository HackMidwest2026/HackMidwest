"""DIAGNOSTIC setup: move every enemy NPC (id >= 0) in the loaded room to y = -1000 (stands in for defeating them),
let it settle, and save.  usage: tik_clear_enemies.py IN.st OUT.st"""
import os, sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ce%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] >= 0:
        e.wf32(n['addr'] + 0x38, 0.0); e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x40, 0.0)
for i in range(60): e.step(0, 0, 0, 2)
print(where(e), player(e), [(n['id'], round(n['y'])) for n in npcs(e)], flush=True)
e.save(sys.argv[2]); e.step(0, 0, 0, 1)
