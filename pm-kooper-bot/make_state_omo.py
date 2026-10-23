"""Crystal Palace room start state with Lakilester: rewrite the nok_14 left exit to GotoMap(MAP, ENTRY) (env PRA_MAP, default pra_03; PRA_ENTRY), make Lakilester the partner, walk through."""
import os, struct
from emu import *
from pm import *

ENTRY = int(os.environ.get('PRA_ENTRY', '0'))
MAP = os.environ.get('PRA_MAP', 'pra_03')
e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), os.environ.get('PM_TMP', '/dev/shm/pmbot/pra'))
e.load(os.environ.get('NOK14', '../bot/states/nok14_start_goombario.st'))
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
        for k, ch in enumerate(MAP.encode() + b"\x00\x00"):
            e.w8(s + k, ch)
        e.w32(a + 4, ENTRY)
        patched = True
        j = raw.find(needle, j + 1)
assert patched
# optional game bytes, env GB_SET="0x129=2,..." (GameByte index = value), written before the map load
for kv in filter(None, os.environ.get('GB_SET', '').split(',')):
    k, v = kv.split('='); e.w8(STORY + int(k, 0), int(v, 0))
# Lakilester (partner 8): mark him recruited and make him the current partner before the map load
PART = int(os.environ.get("PARTNER", "8"))
for i in range(1, 12): e.w8(PLAYER_DATA + 0x14 + 8 * i, 0) if os.environ.get("ONLY") else None
e.w8(PLAYER_DATA + 0x14 + 8 * PART, 1)
e.w8(PLAYER_DATA + 0x12, PART)
for i in range(300):
    e.step(0, -80, 0, 2)
    if where(e)[0] == int(os.environ.get('PRA_AREA', '21')) and e.s16(GAME_MODE) == GM_WORLD:
        break
for i in range(200):
    e.step(0, 0, 0, 2)
print('now in', where(e), player(e), 'partner', e.s8(PLAYER_DATA + 0x12))
print('npcs', [(n['id'], round(n['x']), round(n['y']), round(n['z']), n['diam'], n['height'], hex(n['flags'])) for n in npcs(e)])
os.makedirs('states', exist_ok=True)
e.save('states/%s_e%d%s.st' % (MAP.replace('_', ''), ENTRY, os.environ.get('STATE_SUFFIX', '')))
print('saved')
