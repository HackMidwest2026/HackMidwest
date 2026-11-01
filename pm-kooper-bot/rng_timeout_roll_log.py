import sys
from emu import *
from pm import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/tor')
e.load('states/boss_2302_on_timeout.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
def enemies():
    out = []
    for i in range(24):
        a = e.u32(BSTATUS + 0xE0 + 4 * i)
        if 0x80000000 < a < 0x80800000: out.append((i, e.s8(a + 0x210), e.s8(a + 0x211)))
    return out
s = e.u32(SEED); prevd = enemies(); f = 0
for i in range(520):
    e.step(A if i in (2, 14, 15) else 0, 0, 0, 2); f += 1
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if hex(x['ra']) not in ('0x800269ac', '0x80146d54') and not hex(x['ra']).startswith('0xe0'): print('frame %d call ra %s max %d -> %d' % (f, hex(x['ra']), mx, v))
    d = enemies()
    if d != prevd: print('frame %d enemies (slot, debuff, duration): %s' % (f, d)); prevd = d
    if bstate(e) in (21, 13, 20) and f > 50: print('state', bstate(e), 'at', f); break
