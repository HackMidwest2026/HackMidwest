"""Push the stale target further left while keeping the history fill on the rock top: walk at PA for PRE frames,
wait W1, jump left (stick R frames, A held 8), wiggle until the ring is full, 1 neutral frame, hop right (stick 8).
Good = wiggle on the rock top (y > -45), ring full, Laki idle (state 5) with the target intact after the hop.
Prints good runs sorted by stale target x. usage: fill_left_search.py"""
import itertools, os, sys
from multiprocessing import Pool
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
def run(a):
    PA, PRE, W1, R = a[:4]; JA = a[4] if len(a) > 4 else 180
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/fl%d' % os.getpid())
    e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
    def jump(stick, hold):
        for i in range(30):
            e.step(0x80 if i < 8 else 0, *(stick if i < hold else (0, 0)), 2)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(PRE): e.step(0, *stick_for(PA, 80), 2)
    for i in range(W1): e.step(0, 0, 0, 2)
    jump(stick_for(JA, 80), R)
    rp = player(e)
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for f in range(160):
        if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
        e.step(0, *(up if f % 2 == 0 else dn), 2)
    full = (e.u32(IDX) + 1) % 40 == e.u32(PTR)
    ptr = e.u32(PTR); tgt = (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12))
    e.step(0, 0, 0, 2)
    jump(stick_for(0, 80), 8)
    ok = full and rp['y'] > -45 and (e.u32(STATE) >> 16) == 5 and e.u32(PTR) == ptr and (e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)) == tgt
    return a, ok, round(tgt[0], 1), round(tgt[1], 1), (round(rp['x'], 1), round(rp['y'], 1), round(rp['z'], 1))
if __name__ == '__main__':
    grid = list(itertools.product((150, 155, 160, 165, 170, 175, 180), range(8, 17), (1, 10, 30), (0, 2, 4, 6, 8, 10, 12))) if not os.environ.get('BACK') else \
           list(itertools.product((160, 170, 180), range(12, 23, 2), (10, 30), (2, 4, 6, 8, 10), (30, 45, 60, 90, 120, 135)))
    with Pool(4, maxtasksperchild=1) as p: res = p.map(run, grid, chunksize=1)
    good = sorted([r for r in res if r[1]], key=lambda r: r[2])
    print(len(good), 'good of', len(res))
    for r in good[:25]: print(r)
