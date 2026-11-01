# (run from the emulator working dir, bot1/) """Every RNG call in a Bowser's Castle room for 600 frames standing + 600 walking, by caller. Calls other than the
per-frame step (ra 0x800269AC) and the status-bar coin (0x80146D54) break the coin-chain model."""
import os, sys, collections
os.environ['M64P_DBG'] = '1'
from emu import *
from pm import *
from rngsim import *
st = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rr_' + st)
e.load('states/' + st); e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
yaw = player(e)['yaw']; dx = 70 if yaw < 180 else -70
other = collections.Counter(); calls = collections.Counter(); first = {}
for f in range(int(os.environ.get("NF", "1200"))):
    if f < int(os.environ.get("NF", "1200")) // 2: b, x = 0, 0
    else: b, x = 0, (dx if (f // 90) % 2 == 0 else -dx)
    e.step(b, x, 0, 2)
    if e.s16(GAME_MODE) != GM_WORLD: print('  left world mode at frame', f); break
    for ev in e.dbg_events():
        ra = ev['ra']; mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        if ra in (0x800269AC, 0x80146D54): calls[hex(ra)] += 1
        else: other[(hex(ra), mx, 'walk' if f >= 600 else 'stand')] += 1; first.setdefault((hex(ra), mx), f)
print(st, where(e), 'frame/coin calls', dict(calls), '| OTHER:', dict(other) or 'none', '| first at', first)
