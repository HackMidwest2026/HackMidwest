"""Wider ledge search from CORNER (Lakilester at the lower floor's top-right corner, stale target intact): optional
pre-steps up to the top wall (U frames of stick up), then one or two jumps; a jump = W frames of stick at angle D,
then A held 8 frames with the stick at D for H frames, then neutral until landed. After the jumps: stop-and-go
right along the top wall (go G / stop 2) until stuck or the target is lost. Reports the best plans by distance from
Lakilester to his frozen target. usage: rev_ledge4.py <out.json>"""
import json, math, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
CORNER = os.environ.get('CORNER', 'states/pra01_corner.st')
W_ = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/l4%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W_['e'] = Emu(os.environ['PM_ROM'], d)
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(plan):
    U, jumps, G = plan
    e = W_['e']
    e.load(CORNER); e.step(0, 0, 0, 2)
    ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
    def intact():
        return e.u32(PTR) == ptr0 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz and (e.u32(STATE) >> 16) == 5
    for i in range(U): e.step(0, *stick_for(270, 80), 2)
    for W, H, D in jumps:
        s = stick_for(D, 80)
        for i in range(W): e.step(0, *s, 2)
        for i in range(24):
            e.step(0x80 if i < 8 else 0, *(s if i < H else (0, 0)), 2)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
        for i in range(3): e.step(0, 0, 0, 2)
        if not intact(): return None
    rx, ry = stick_for(0, 80); best = 0
    for c in range(110):
        for i in range(G): e.step(0, rx, ry, 2)
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if not intact(): break
        l = laki(e); best = max(best, math.hypot(l['x'] - tx, l['z'] - tz))
        if l['x'] > 984: break
    p, l = player(e), laki(e)
    return (round(best, 1), plan, (round(p['x']), round(p['y']), round(p['z'])), (round(l['x']), round(l['z'])))
if __name__ == '__main__':
    J = [(W, H, D) for W in (0, 1, 2, 4) for H in (0, 4, 8, 12, 16) for D in (0, 340)]
    plans = [(U, [j], G) for U in (0, 3) for j in J for G in (1,)] + [(U, [(0, 12, 0), j], 1) for U in (0, 3) for j in J] + [(U, [(0, 12, 340), j], 1) for U in (0, 3) for j in J]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for r in pool.imap_unordered(run, plans, chunksize=4) if r]
    res.sort(key=lambda r: -r[0])
    json.dump(res, open(sys.argv[1], 'w'))
    for r in res[:8]: print(r)
    pool.terminate()
