"""Shortest waits for the rock part of the setup: walk at PA for PRE frames, wait W1, jump left (stick R), wait W2,
wiggle until the ring is full, wait W3, hop right (stick H), wait W4. A run is good when Mario wiggled on the rock top
(y > -45), the stale target is the walk-left one (x < 556), the ring is full and Laki is idle (state 5) with the
target intact at the end. Prints good combinations by total frames. usage: fast_fill.py"""
import itertools, os, sys
from multiprocessing import Pool
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
PA, PRE, R, H = 160, 10, 12, 8
def run(w):
    W1, W2, W3, W4 = w
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ff%d' % os.getpid())
    e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2); n = 0
    def st(b, s):
        nonlocal n; e.step(b, *s, 2); n += 1
    def jump(stick, hold):
        for i in range(30):
            st(0x80 if i < 8 else 0, stick if i < hold else (0, 0))
            if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(PRE): st(0, stick_for(PA, 80))
    for i in range(W1): st(0, (0, 0))
    jump(stick_for(180, 80), R)
    for i in range(W2): st(0, (0, 0))
    ry = player(e)['y']
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for f in range(160):
        if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
        st(0, up if f % 2 == 0 else dn)
    full = (e.u32(IDX) + 1) % 40 == e.u32(PTR)
    ptr = e.u32(PTR); tgt = (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12))
    for i in range(W3): st(0, (0, 0))
    jump(stick_for(0, 80), H)
    for i in range(W4): st(0, (0, 0))
    ok = full and ry > -45 and tgt[0] < 556 and (e.u32(STATE) >> 16) == 5 and e.u32(PTR) == ptr and (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)) == tgt
    l = [x for x in npcs(e) if x['id'] == -4][0]; p = player(e)
    return w, n, ok, round(ry, 1), tgt, (round(p['x'], 1), round(p['z'], 1)), (round(l['x'], 1), round(l['z'], 1))
if __name__ == '__main__':
    grid = list(itertools.product((0, 5, 10, 20, 30, 45, 60), (0, 5, 10, 20, 40, 60), (0, 10), (0, 21))) if not os.environ.get('FINE') else list(itertools.product(range(0, 6), (0,), range(0, 11), (0,)))
    with Pool(4, maxtasksperchild=1) as p: res = p.map(run, grid, chunksize=1)
    good = sorted([r for r in res if r[2]], key=lambda r: r[1])
    print(len(good), 'good of', len(res))
    for r in good[:15]: print(r)
    print('original (60,60,10,21):', [r for r in res if r[0] == (60, 60, 10, 21)])
