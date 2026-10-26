"""Advance a boss battle to a later phase with real turns. DIAGNOSTIC SETUP: actors whose type is in KILL get HP 1
(re-applied whenever new ones appear, e.g. a spawned phase). Then inputs only: on Mario's menu Jump the default target,
on the partner's menu use the default ability on the default target, otherwise tap A every 20 frames for text.
Stops at Mario's menu once COND holds and saves OUT.
usage: btl_autopilot.py IN.st OUT.st KILLTYPES COND   (COND: 'gone:T1,T2' = no live actor of those types;
       'present:T' = a live actor of type T exists; KILLTYPES comma list or '-')"""
import os, sys
from emu import *
from pm import *
from btl import *
src, dst, killarg, cond = sys.argv[1:5]
KILL = set() if killarg == '-' else {int(t) for t in killarg.split(',')}
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ap%d' % os.getpid())
e.load(src); e.step(0, 0, 0, 2)
HPSET = int(os.environ.get('HP', '0'))
def actors():
    out = []
    for i in range(24):
        a = e.u32(BSTATUS + 0xE0 + 4 * i)
        if 0x80000000 < a < 0x80800000: out.append((i, a, e.u8(a + 0x136), e.s8(a + 0x1B8)))
    return out
def weaken():
    if HPSET and e.s8(PLAYER_DATA + 2) < HPSET // 2:
        e.w8(PLAYER_DATA + 2, HPSET); e.w8(PLAYER_DATA + 3, HPSET)      # DIAGNOSTIC: keep Mario alive
        pa = e.u32(BSTATUS + 0xD8)
        if 0x80000000 < pa < 0x80800000: e.w8(pa + 0x1B8, HPSET); e.w8(pa + 0x1B9, HPSET)
    for i, a, t, hp in actors():
        if t in KILL and hp > 1: e.w8(a + 0x1B8, 1)          # DIAGNOSTIC
def ok():
    kind, ts = cond.split(':'); ts = {int(t) for t in ts.split(',')}
    live = {t for i, a, t, hp in actors() if hp > 0}
    if kind == 'only': return live <= ts
    return (not (live & ts)) if kind == 'gone' else bool(live & ts)
turns = 0
for f in range(20000):
    weaken()
    s = bstate(e)
    if f % 1000 == 0: print('f', f, 'state', s, 'turns', turns, 'actors', [(i, t, hp) for i, a, t, hp in actors()], flush=True)
    if s == 13:
        for i in range(10): e.step(0, 0, 0, 2)
        if ok():
            print('condition met after', turns, 'player turns; actors', [(i, t, hp) for i, a, t, hp in actors()], flush=True)
            e.save(dst); e.step(0, 0, 0, 1); sys.exit(0)
        turns += 1
        e.step(A, 0, 0, 2)
        for i in range(15): e.step(0, 0, 0, 2)
        for r in range(turns % 4):                     # cycle the target so weakened actors get hit too
            e.step(0, 70, 0, 2)
            for i in range(6): e.step(0, 0, 0, 2)
        e.step(A, 0, 0, 2)
        for i in range(30): e.step(0, 0, 0, 2)
    elif s == 14:
        pturn = globals().get('pturn', 0); globals()['pturn'] = pturn + 1
        for k in range(3):
            if k == 2:                                     # on the target cursor: cycle the partner's target too
                for r in range(pturn % 5):
                    e.step(0, 70, 0, 2)
                    for i in range(6): e.step(0, 0, 0, 2)
            e.step(A, 0, 0, 2)
            for i in range(15): e.step(0, 0, 0, 2)
        for i in range(30): e.step(0, 0, 0, 2)
    else:
        e.step(A if f % 20 == 0 else 0, 0, 0, 2)
    if e.s16(GAME_MODE) != 8:
        print('left battle, mode', e.s16(GAME_MODE), 'state', s, flush=True); sys.exit(1)
print('gave up; actors', [(i, t, hp) for i, a, t, hp in actors()], 'state', bstate(e))
