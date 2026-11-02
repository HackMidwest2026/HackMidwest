"""(run from bot1/) (run from bot1/) Blooper battle state (DIAGNOSTIC setup): warp nok_14's exit to tik_01, Power Bounce (0xE4) owned and
equipped, walk left into Blooper's trigger (x < 200), advance to Mario's first battle menu, save states/blooper_menu.st."""
import os, sys, struct
from emu import *
from pm import *
from btl import *
MAP, ENTRY = 'tik_01', int(os.environ.get('ENTRY', '0'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mk_blooper')
e.load('../bot/states/nok14_start_goombario.st'); e.step(0, 0, 0, 2)
lo, hi = 0x80200000, 0x80400000
raw = b''.join(struct.pack('>I', e.u32(a)) for a in range(lo, hi, 4))
hits = []; i = raw.find(b'nok_13\x00')
while i >= 0: hits.append(lo + i); i = raw.find(b'nok_13\x00', i + 1)
ok = False
for s in hits:
    j = raw.find(struct.pack('>II', s, 2))
    while j >= 0:
        for k, ch in enumerate(MAP.encode() + b'\x00\x00'): e.w8(s + k, ch)
        e.w32(lo + j + 4, ENTRY); ok = True; j = raw.find(struct.pack('>II', s, 2), j + 1)
assert ok
e.w8(STORY, int(os.environ.get('STORY', '20')))                       # DIAGNOSTIC setup: story
e.w16(PLAYER_DATA + 0xB4, 0xE4); e.w16(PLAYER_DATA + 0x208, 0xE4)   # DIAGNOSTIC setup: Power Bounce owned + equipped
e.w8(PLAYER_DATA + 8, max(3, e.s8(PLAYER_DATA + 8)))                  # DIAGNOSTIC setup: max BP 3
e.w8(PLAYER_DATA + 0xA, 1)                                            # DIAGNOSTIC setup: action commands on (this save is from before the Lucky Star)
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e)[0] != 6 and e.s16(GAME_MODE) == GM_WORLD: break
print('in', where(e), player(e), flush=True)
for f in range(1500):
    if bstate(e) > 0 and e.s16(GAME_MODE) != GM_WORLD: break
    e.step(0, -80, 0, 2)
print('battle start after', f, 'mode', e.s16(GAME_MODE), 'bstate', bstate(e), flush=True)
to_first_menu(e)
e.save('states/blooper_menu.st'); print('saved; boots', e.s8(PLAYER_DATA))
