"""Any-room state (DIAGNOSTIC setup, same warp as make_state_kpa.py / make_state_kzn03.py): rewrite the nok_14 left exit
to GotoMap(MAP, ENTRY), set the story byte (signed enum value) and optionally a partner (1 Goombario, 3 Bombette...),
walk through, stand 200 frames, save states/<map>_e<entry>_s<story>.st.
run from /tmp/claude-0/pm/bot1. usage: make_state_warp.py MAP ENTRY STORY [PARTNER]
e.g. trd_00 0 -83 3: Koopa Bros. Fortress exterior, Bombette just joined."""
import os, sys, struct
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
MAP = sys.argv[1]; ENTRY = int(sys.argv[2]); STORY_V = int(sys.argv[3]); PARTNER = int(sys.argv[4]) if len(sys.argv) > 4 else 0
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
e.w8(STORY, STORY_V & 0xFF)                     # DIAGNOSTIC setup: story value (signed)
if PARTNER: e.w8(PLAYER_DATA + 0x14 + PARTNER * 8, 1); e.w8(PLAYER_DATA + 0x12, PARTNER)   # DIAGNOSTIC setup: partner recruited + active
start = where(e)
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e) != start and e.s16(GAME_MODE) == GM_WORLD: break
for i in range(200): e.step(0, 0, 0, 2)
print(MAP, ENTRY, 'now in', where(e), {k: round(v) if isinstance(v, float) else v for k, v in player(e).items()}, 'mode', e.s16(GAME_MODE))
e.save('states/%s_e%d_s%d.st' % (MAP.replace('_', ''), ENTRY, STORY_V)); print('saved')
