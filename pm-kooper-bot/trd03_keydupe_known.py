"""Observe the known 33rd-key-item glitch (DIAGNOSTIC SETUP: the 32 key-item slots and some consumables are written
directly so the throw-away flow can be watched; the pickup and menu choice are inputs).
In trd_03 walk onto Fortress Key A (-580, 0, -60), A through the "can't carry more" text, pick menu entry CHOICE
(0 = the new key itself, 1 = first consumable, ...), finish the text, then report key items, consumables and the
item entities left in the room.  usage: trd03_keydupe_known.py CHOICE"""
import os, sys
from emu import *
from pm import *
from nav import go_to
CHOICE = int(sys.argv[1])
KEY = 16                       # ITEM_KOOPA_FORTRESS_KEY (read from the item entity)
MUSH = 0x8A
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kd%d' % os.getpid())
e.load(os.environ.get('START', 'states/trd03_ready.st')); e.step(0, 0, 0, 2)
for i in range(32): e.w16(PLAYER_DATA + 0x74 + 2 * i, KEY)          # DIAGNOSTIC: 32 key items
INV = [int(x, 0) for x in os.environ.get("INV", "0,0,0,0,0,0,0,0x8A,0x8A,0x8A").split(",")]
for i in range(10): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, INV[i])   # DIAGNOSTIC: consumables, packed at the back like sort_items leaves them
def inv():
    return ([e.s16(PLAYER_DATA + 0x74 + 2 * i) for i in range(32)].count(KEY),
            [e.s16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10)])
def items():
    out = []
    for i in range(256):
        p = e.u32(0x8015AD20 + 4 * i)
        if 0x80000000 < p < 0x80800000 and e.u32(p) & 1:
            out.append((e.s16(p + 0x18), round(e.f32(p + 8)), round(e.f32(p + 0x10)), e.s16(p + 4)))
    return out
print('before: keys', inv()[0], 'consumables', inv()[1], 'room items', items(), flush=True)
e.wf32(PLAYER + PS_POS, -560.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, -60.0)   # DIAGNOSTIC: place Mario by key A
for i in range(3): e.step(0, 0, 0, 2)
go_to(e, -580, -60, maxf=60, tol=2)
print('at', player(e), 'mode', e.s16(GAME_MODE), flush=True)
POP = 0x8010D85C
for f in range(600):
    p = e.u32(POP)
    if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) != 4 and e.s32(p + 0x324) > 0 and e.s32(p + 0x32C) == 0:
        break
    e.step(A if f % 10 == 0 else 0, 0, 0, 2)
print('menu entries', e.s32(p + 0x324), [e.s32(p + 0x108 + 4 * i) for i in range(e.s32(p + 0x324))], flush=True)
for i in range(30): e.step(0, 0, 0, 2)
for k in range(CHOICE):
    for i in range(2): e.step(0, 0, -80, 1)
    for i in range(8): e.step(0, 0, 0, 2)
for i in range(2): e.step(A, 0, 0, 1)
for f in range(300):
    e.step(A if f % 15 == 0 else 0, 0, 0, 2)
    if f in (5, 20, 60, 120, 200): print('  step', f, 'room items', items(), flush=True)
print('after choice %d: keys' % CHOICE, inv()[0], 'consumables', inv()[1], 'room items', items(), flush=True)
e.save('/tmp/claude-0/pm/keydupe_choice%d.st' % CHOICE); e.step(0, 0, 0, 1)
