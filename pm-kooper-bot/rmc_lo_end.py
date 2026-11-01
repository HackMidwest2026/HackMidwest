"""Laki-outside hold-up ending (rta_holdup2 route) in the T framework, from a top-right state already loaded into t:
up 10, right 10, B+down + 9 swing, down 4, A + down N, B+left + 9 swing, run left; B+up at the frame Mario is on
step 3 (x 878..893); hold up; C-down on frame c. search() returns the clip with the earliest C-down."""
from rmc_tim import *
from corner_sweep import stick_for
SD = {'L': stick_for(180, 80), 'D': stick_for(90, 80), 'R': stick_for(0, 80), 'U': stick_for(270, 80)}
def pre(t, N):
    for i in range(10): t.step(0, *SD['U'])
    for i in range(10): t.step(0, *SD['R'])
    t.step(B, *SD['D'])
    for i in range(9): t.step(0, *SD['D'])
    for i in range(4): t.step(0, *SD['D'])
    for i in range(N): t.step(A if i < 12 else 0, *SD['D'])
    t.step(B, *SD['L'])
    for i in range(9): t.step(0, *SD['L'])
def search(t, Ns=range(24, 42), tag='x'):
    e = t.e; S0 = '/dev/shm/pmbot/le_%s_0.st' % tag
    t.step(); e.save(S0); n0 = t.n; best = None
    for N in Ns:
        e.load(S0); t.n = n0; pre(t, N)
        for k in range(60):
            t.step(0, *SD['L']); p = player(e)
            if abs(p['y'] + 10) < 0.01 and 878 <= p['x'] <= 893 and p['action'] in (1, 2):
                h = t.n; Sh = '/dev/shm/pmbot/le_%s_h.st' % tag; e.save(Sh)
                for c in range(h + 12, h + 45):
                    if best and c >= best[0]: break
                    e.load(Sh); t.n = h
                    t.step(B, *SD['U'])
                    while t.n < c - 1: t.step(0, *SD['U'])
                    q = player(e); t.step(D_CBUTTON, *SD['U']); spd = BC.laki()['speed']
                    if spd < 115.5 or q['action'] not in (0, 1, 2): continue
                    for i in range(40): t.step()
                    if player(e)['z'] > 1: best = (c, N, h, round(spd, 2)); break
                e.load(Sh); t.n = h
            if p['x'] < 878: break
    return best
def replay(t, N, h, c):
    pre(t, N)
    while t.n < h: t.step(0, *SD['L'])
    t.step(B, *SD['U'])
    while t.n < c - 1: t.step(0, *SD['U'])
    t.step(D_CBUTTON, *SD['U'])
