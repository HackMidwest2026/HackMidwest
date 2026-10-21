"""How many frames Lakilester's PutAway needs to reach FINISH_1 (the collision re-enable), by riding position.
nok_13 riding state; Mario+Laki teleported to (x, floor, z) (exploration), settle, open the partner menu, pick
Goombario; count game frames from the swap start (input count +1) to the counter dropping to 0.
usage: clippy_dismount_map.py OUT.jsonl"""
import json, math, sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cldm')
e.load('states/nok13_e0_laki2.st'); e.step(0, 0, 0, 2); e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 60)
base = '/dev/shm/pmbot/cldm.st'; e.save(base)
out = open(sys.argv[1], 'w')
for x in range(-720, -440, 6):
    for z in range(20, 130, 6):
        e.load(base)
        lk = [n for n in npcs(e) if n['id'] == -4][0]['addr']
        for a in (lk + 0x38, PLAYER + PS_POS): e.wf32(a, x); e.wf32(a + 8, z)
        e.wf32(lk + 0x3C, 80.0); e.wf32(PLAYER + PS_POS + 4, 90.0)
        e.step(0, 0, 0, 60)
        p = player(e)
        if p['action'] != 33 or e.s8(PLAYER + 0x14) != 1: continue
        e.step(R_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 40); e.step(0, 0, -80, 4); e.step(0, 0, 0, 8); e.step(A, 0, 0, 2)
        start = fin = None
        d0 = e.s8(PLAYER + 0x15)
        for f in range(60):
            e.step(0, 0, 0, 2)
            dn = e.s8(PLAYER + 0x15)
            if start is None and e.s8(PLAYER + 0x14) == 1 and dn > d0 and f > 2: start = f
            d0 = dn
            if e.s8(PLAYER + 0x14) == 0: fin = f; break
        r = {'x': x, 'z': z, 'y': round(p['y'], 1), 'lakiy': round(e.f32(lk + 0x3C), 1), 'start': start, 'fin': fin, 'dur': None if start is None or fin is None else fin - start}
        out.write(json.dumps(r) + '\n'); out.flush()
