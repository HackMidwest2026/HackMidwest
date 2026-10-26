"""Pick up the stacked Happy Flowers at (-250, 0) in flo_09 one after another (inputs only: stand on the pile and mash
A through each "You got a badge" text). Logs the badge count after each pickup and stops when the throw-away menu
opens (badge list full) or after MAXP pickups. If the menu opens, picks entry CHOICE and reports what happened.
usage: flo09_hf_pickup.py STATE MAXP CHOICE OUT.st   (env INV: DIAGNOSTIC consumables, like the trd_03 test)"""
import os, sys
from emu import *
from pm import *
from nav import go_to
st, MAXP, CHOICE, outst = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hp%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
if os.environ.get('INV'):
    INV = [int(x, 0) for x in os.environ['INV'].split(',')]
    for i in range(10): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, INV[i])   # DIAGNOSTIC: consumables
POP = 0x8010D85C
if os.environ.get('FILLB'):
    for i in range(int(os.environ['FILLB'])): e.w16(PLAYER_DATA + 0xB4 + 2 * i, 321)   # DIAGNOSTIC: badge slots
def nbadges(): return sum(1 for i in range(128) if e.s16(PLAYER_DATA + 0xB4 + 2 * i))
def nitems():
    return sum(1 for i in range(256) if 0x80000000 < e.u32(0x8015AD20 + 4 * i) < 0x80800000 and e.u32(e.u32(0x8015AD20 + 4 * i)) & 1)
def inv(): return [e.s16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10)]
def menu_open():
    p = e.u32(POP)
    return p if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) != 4 and e.s32(p + 0x324) > 0 and e.s32(p + 0x32C) == 0 else None
print('start: badges', nbadges(), 'item entities', nitems(), 'consumables', inv(), flush=True)
go_to(e, -200 + 60, 58, maxf=300, tol=3)        # same lane the dupe loop uses, then walk around tree 1 to the pile
go_to(e, -290, 58, maxf=300, tol=3)
go_to(e, -250, 0, maxf=200, tol=2)
last = nbadges(); p = None
for f in range(MAXP * 120):
    p = menu_open()
    if p: break
    e.step(A if f % 6 == 0 else 0, 0, 0, 2)
    if f % 30 == 0 and nbadges() != last:
        last = nbadges(); print('  badges', last, 'item entities', nitems(), flush=True)
    if nbadges() >= MAXP: break
print('badges', nbadges(), 'item entities', nitems(), 'menu', bool(p), flush=True)
if p:
    print('menu entries', e.s32(p + 0x324), [e.s32(p + 0x108 + 4 * i) for i in range(e.s32(p + 0x324))], flush=True)
    for i in range(30): e.step(0, 0, 0, 2)
    for k in range(CHOICE):
        for i in range(2): e.step(0, 0, -80, 1)
        for i in range(8): e.step(0, 0, 0, 2)
    for i in range(2): e.step(A, 0, 0, 1)
    for f in range(60): e.step(A if f % 15 == 0 else 0, 0, 0, 2)
    print('after choice', CHOICE, ': badges', nbadges(), 'consumables', inv(), 'item entities', nitems(), flush=True)
e.save(outst); e.step(0, 0, 0, 1)
