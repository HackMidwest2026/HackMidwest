"""Replay one laki_stuck_search.py seed and log Laki per frame (state, pointer/index, target, speed, flags, positions).
usage: laki_stuck_replay.py STATE SEED [F=900] [EVERY=1] [SAVE_AT SAVE_PATH]"""
import math, os, random, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import laki_stuck_search_policy as P
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, seed = sys.argv[1], int(sys.argv[2]); F = int(sys.argv[3]) if len(sys.argv) > 3 else 900
EVERY = int(sys.argv[4]) if len(sys.argv) > 4 else 1
SAVE = (int(sys.argv[5]), sys.argv[6]) if len(sys.argv) > 6 else None
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lsr%d' % os.getpid())
seq = P.policy(random.Random(seed), F)
e.load(st0); e.step(0, 0, 0, 2)
for f, (b, x, y) in enumerate(seq):
    e.step(b, x, y, 2)
    if SAVE and f == SAVE[0]: e.save(SAVE[1])
    if f % EVERY: continue
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]; pt = e.u32(PTR)
    print('%4d b%02x stick(%4d,%4d) M (%7.1f %6.1f %7.1f) act %2d | L (%7.1f %6.1f %7.1f) st %2d ptr %2d idx %2d tgt (%7.1f %6.1f %7.1f) spd %6.2f fl %08x dM %.1f' % (
        f, b, x, y, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, pt, e.u32(IDX),
        e.f32(HIST + 16 * pt + 4), e.f32(HIST + 16 * pt + 8), e.f32(HIST + 16 * pt + 12), l['speed'], l['flags'], math.hypot(p['x'] - l['x'], p['z'] - l['z'])))
