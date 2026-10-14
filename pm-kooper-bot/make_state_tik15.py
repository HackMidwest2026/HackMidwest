"""tik_15 start state with goombario: load the nok_14 goombario state, rewrite the left exit's
GotoMap("nok_13", entry 2) in RAM to GotoMap("tik_15", entry ENTRY), and walk through it."""
import os, struct
from emu import *
from pm import *

ENTRY = int(os.environ.get('TIK15_ENTRY', '0'))
e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), os.environ.get('PM_TMP', '/dev/shm/pmbot'))
e.load('states/nok14_start_goombario.st')
e.step(0, 0, 0, 2)

def find_bytes(pat, lo=0x80200000, hi=0x80400000):
    out = []
    raw = b''.join(struct.pack('>I', e.u32(a)) for a in range(lo, hi, 4))
    i = raw.find(pat)
    while i >= 0:
        out.append(lo + i); i = raw.find(pat, i + 1)
    return out, raw

hits, raw = find_bytes(b'nok_13\x00')
print('"nok_13" strings at', [hex(h) for h in hits])
patched = False
for s in hits:
    # the GotoMap call holds the string's address followed by the entry index (nok_13_ENTRY_2 = 2)
    needle = struct.pack('>II', s, 2)
    j = raw.find(needle)
    while j >= 0:
        a = 0x80200000 + j
        print('GotoMap args at', hex(a))
        for k, ch in enumerate(b'tik_15\x00\x00'):
            e.w8(s + k, ch)
        e.w32(a + 4, ENTRY)
        patched = True
        j = raw.find(needle, j + 1)
assert patched
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e)[:2] == (2, 12) and e.s16(GAME_MODE) == GM_WORLD:
        break
for i in range(200):
    e.step(0, 0, 0, 2)
print('now in', where(e), player(e), 'partner', e.s8(PLAYER_DATA + 0x12))
print('npcs', [(n['id'], round(n['x']), round(n['y']), round(n['z']), n['diam'], n['height'], hex(n['flags'])) for n in npcs(e)])
os.makedirs('states', exist_ok=True)
e.save('states/tik15_start.st')
print('saved')
