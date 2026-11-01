"""Bowser's Castle room state (DIAGNOSTIC setup): rewrite the nok_14 left exit to GotoMap(MAP, ENTRY), story = reached
Bowser's Castle (94), Bombette as the partner, walk through. Usage: make_state_kpa.py kpa_61 0"""
import os, sys, struct
from emu import *
from pm import *
MAP, ENTRY = sys.argv[1], int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mk_%s_%d' % (MAP, ENTRY))
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
e.w8(STORY, 94)                                  # DIAGNOSTIC setup: story = reached Bowser's Castle
e.w8(PLAYER_DATA + 0x14 + 3 * 8, 1); e.w8(PLAYER_DATA + 0x12, 3)   # DIAGNOSTIC setup: Bombette recruited + active
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e)[0] == 22 and e.s16(GAME_MODE) == GM_WORLD: break
for i in range(150): e.step(0, 0, 0, 2)
print(MAP, ENTRY, 'now in', where(e), {k: round(v) if isinstance(v, float) else v for k, v in player(e).items()}, 'mode', e.s16(GAME_MODE))
e.save('states/%s_e%d.st' % (MAP.replace('_', ''), ENTRY)); print('saved')
