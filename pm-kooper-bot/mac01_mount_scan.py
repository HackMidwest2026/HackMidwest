"""Inputs only from STATE (just after the mac_01 OOB respawn, Mario idle): C-down on frame k, record the speed the
mount reads, where Mario ends after the mount, and the displacement. usage: mac01_mount_scan.py STATE K0 K1 OUT.json"""
import json, math, sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mms')
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
res = []
for k in range(int(sys.argv[2]), int(sys.argv[3]) + 1):
    e.load(sys.argv[1])
    for i in range(k): e.step(0, 0, 0, 2)
    p0, l0 = player(e), lk(); e.step(D_CBUTTON, 0, 0, 2)
    spd = None
    for i in range(25):
        if e.u8(PLAYER + PS_ACTION) == 33: spd = e.f32(lk()['addr'] + 0x18); break
        e.step(0, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    p = player(e)
    r = {'k': k, 'laki_before': [round(l0['x'], 1), round(l0['y'], 1), round(l0['z'], 1)], 'laki_spd_before': round(l0['speed'], 2), 'mount_speed': None if spd is None else round(spd, 2),
         'mario_end': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], 'moved': round(math.hypot(p['x'] - p0['x'], p['z'] - p0['z']), 1), 'action': p['action']}
    res.append(r); print(r, flush=True)
json.dump(res, open(sys.argv[4], 'w'))
