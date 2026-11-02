"""Mt. Lava Lava kzn_03 room state (DIAGNOSTIC setup, same warp as make_state_kpa.py): rewrite the nok_14 left exit to
GotoMap(kzn_03, ENTRY), story = got Ultra Hammer (28, Kolorado still wanders), walk through, stand.
run from /tmp/claude-0/pm/bot1. usage: make_state_kzn03.py [ENTRY]   (entry 2 is the floor of the Save Block)"""
import os, sys, struct
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
MAP = 'kzn_03'; ENTRY = int(sys.argv[1]) if len(sys.argv) > 1 else 2
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mk_kzn03_%d' % ENTRY)
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
e.w8(STORY, 28)                                  # DIAGNOSTIC setup: STORY_CH5_GOT_ULTRA_HAMMER
start = where(e)
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e) != start and e.s16(GAME_MODE) == GM_WORLD: break
for i in range(200): e.step(0, 0, 0, 2)
print(MAP, ENTRY, 'now in', where(e), {k: round(v) if isinstance(v, float) else v for k, v in player(e).items()}, 'mode', e.s16(GAME_MODE))
e.save('states/kzn03_e%d.st' % ENTRY); print('saved')
