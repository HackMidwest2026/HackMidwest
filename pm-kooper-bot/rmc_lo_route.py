"""Laki-outside stages in the T framework (same logic as save_corners.py / fast_wall.py), each pipeline 'load + 1
neutral frame' kept as a real neutral frame so the whole thing replays continuously."""
import json, math
from rmc_tim import *
from corner_sweep import stick_for
import fast_setup
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
def to_rock(t, P=600, X1=565, W=0):
    e = t.e
    go_fast(t, P, -14, 60, 60, 3)
    for i in range(200):
        if player(e)['x'] <= X1: break
        t.step(0, -80, 0)
    for i in range(W): t.step()
    fast_setup.rock_part2(e, lambda b, s, tag='': t.step(b, *s))
def arc(t, seq):
    e = t.e; t.step()
    for g, th, sl in seq:
        p, l = player(e), BC.laki()
        sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(g): t.step(0, sx, sy)
        for i in range(sl): t.step()
def ledge_wall(t, w):
    e = t.e; t.step()
    U, jumps, _ = w['plan']
    for i in range(U): t.step(0, *stick_for(270, 80))
    for W, H, D in jumps:
        s = stick_for(D, 80)
        for i in range(W): t.step(0, *s)
        for i in range(24):
            t.step(A if i < 8 else 0, *(s if i < H else (0, 0)))
            if i > 3 and player(e)['action'] in (0, 1, 2): break
        for i in range(3): t.step()
    th, G, S = w['aim'], w['G'], w['S']
    for c in range(300):
        p, l = player(e), BC.laki()
        s = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(G): t.step(0, *s)
        for i in range(S): t.step()
        p, l = player(e), BC.laki()
        if l['x'] >= 983 or p['x'] > l['x'] + 5: break
    for i in range(w.get('wait', 0)): t.step()
    t.step()
def status(t):
    e = t.e; p, l = player(e), BC.laki(); ptr = e.u32(PTR)
    return 'n %d M (%.1f,%.1f,%.1f) L (%.1f,%.1f) st %d ptr %d tgt (%.1f,%.1f)' % (t.n, p['x'], p['y'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12))
