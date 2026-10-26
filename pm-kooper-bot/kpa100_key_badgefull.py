"""Ch8 Castle Key pickup in kpa_100 with a full badge list. DIAGNOSTIC SETUP (stands in for the Happy Flower dupe
plus a full badge collection): BADGES badge slots filled with Happy Flower (321), KEYS key-item slots filled with
Castle Keys, consumables from env INV. Then inputs only: walk onto the key at (-100, 0, 100), mash A, and if the
throw-away menu opens pick entry CHOICE. Reports keys / badges / consumables / room items.
usage: kpa100_key_badgefull.py BADGES KEYS CHOICE"""
import os, sys
from emu import *
from pm import *
from nav import go_to
NB, NK, CHOICE = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kb%d' % os.getpid())
e.load('states/kpa100_e0.st'); e.step(0, 0, 0, 2)
POP = 0x8010D85C
def room():
    out = []
    for i in range(256):
        p = e.u32(0x8015AD20 + 4 * i)
        if 0x80000000 < p < 0x80800000 and e.u32(p) & 1: out.append(e.s16(p + 0x18))
    return out
KEY = room()[0]                                             # the Castle Key's item id, read from its entity
for i in range(128): e.w16(PLAYER_DATA + 0xB4 + 2 * i, 321 if i < NB else 0)    # DIAGNOSTIC: badges
for i in range(32): e.w16(PLAYER_DATA + 0x74 + 2 * i, KEY if i < NK else 0)     # DIAGNOSTIC: key items
INV = [int(x, 0) for x in os.environ.get('INV', '0,0,0,0,0,0,0,0x8A,0x8A,0x8A').split(',')]
for i in range(10): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, INV[i])                # DIAGNOSTIC: consumables
def state():
    k = [e.s16(PLAYER_DATA + 0x74 + 2 * i) for i in range(32)]
    return {'keys': k.count(KEY), 'badges': sum(1 for i in range(128) if e.s16(PLAYER_DATA + 0xB4 + 2 * i)),
            'consumables': [e.s16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10)], 'room': room()}
print('key id', KEY, 'before', state(), flush=True)
go_to(e, -100, 100, maxf=200, tol=2)
p = None
for f in range(400):
    q = e.u32(POP)
    if 0x80000000 < q < 0x80800000 and e.s32(q + 0x318) != 4 and e.s32(q + 0x324) > 0 and e.s32(q + 0x32C) == 0:
        p = q; break
    e.step(A if f % 10 == 0 else 0, 0, 0, 2)
    if f > 60 and KEY not in room(): break
if p:
    print('throw-away menu', [e.s32(p + 0x108 + 4 * i) for i in range(e.s32(p + 0x324))], flush=True)
    for i in range(30): e.step(0, 0, 0, 2)
    for k in range(CHOICE):
        for i in range(2): e.step(0, 0, -80, 1)
        for i in range(8): e.step(0, 0, 0, 2)
    for i in range(2): e.step(A, 0, 0, 1)
for f in range(80): e.step(A if f % 15 == 0 else 0, 0, 0, 2)
print('menu opened' if p else 'no menu', 'after', state(), flush=True)
