"""pra_18 north->south RIGHT SIDE, RTA-style ending search (full-tilt cardinal/diagonal sticks only).
Setup (pra18_ns_ne_push.py CORNER freeze, Speedy Spin equipped as a DIAGNOSTIC badge write, touching pushes
(180,250)+(240,120)+(180,250) that leave Laki stuck at ~(517.5,-132.6)). Then:
  walk d0 for n0 frames -> Z spin holding d1 for k frames -> A (held h frames) holding d2 until landing ->
  hold d3 for m frames after landing -> release. C-down is tried on EVERY frame (pressed on that frame).
Angles: 0 right, 45 down-right, 90 down, 135 down-left. usage: pra18_ns_rta.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
os.environ.setdefault('CORNER', '1')
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2)
for pa, pc, pg in eval(os.environ.get('PUSHSEQ2', '[(180, 250, 4), (240, 120, 6), (180, 250, 4)]')): push(pa, pc, pg)
for i in range(10): e.step(0, 0, 0, 2)
if os.environ.get('ALIGN'):                                   # hold LEFT along the north wall: Mario stops at x 513.00
    for i in range(30): e.step(0, *st(180, 80), 2)
    for i in range(3): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/rt%d_b.st' % os.getpid(); e.save(base)
p = player(e); lx, lz, _ = L(); print('after push: mario (%.1f,%.1f) laki (%.1f,%.1f) state %d' % (p['x'], p['z'], lx, lz, fstate()), flush=True)
D = (0, 45, 90, 135)
def run(n0, d0, d1, k, h, d2, m, d3, cdf=None, log=None):
    """returns list of (frame, x, z, speed, clipped?) for C-down attempts, or plays to cdf."""
    e.load(base); seq = []
    for i in range(n0): seq.append((0, d0))
    seq.append((Z, d1))
    for i in range(k - 1): seq.append((0, d1))
    for i in range(h): seq.append((A, d2))
    return seq
D0 = int(os.environ.get('D0', 90))
fo = open(out, 'a')
JOBS = os.environ.get('JOBS')
jobs = eval(JOBS) if JOBS else list(itertools.product((1, 2, 3, 4), (0, 3), (45, 90), range(2, 7), (6,), (45, 90), (0, 1, 2, 3, 5), (90, 45, 0, 180)))
jobs = jobs[part::nparts]
def inputs(n0, w, d1, k, h, d2, m, d3, landed_at=None):
    """yields (button, stick) per frame given the landing frame (stick after landing depends on it)."""
    pass
def play(n0, w, d1, k, h, d2, m, d3, cd=None):
    e.load(base); f = 0; log = []; landed = None
    for i in range(n0): e.step(0, *st(D0, 80), 2); f += 1
    for i in range(w): e.step(0, 0, 0, 2); f += 1
    for i in range(k):
        b = Z if i == 0 else 0
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(d1, 80), 2); f += 1
    for f2 in range(40):
        q = player(e)
        if landed is None and f2 > 2 and q['action'] in (0, 1, 2): landed = f2
        d = d2 if landed is None else (d3 if f2 - landed < m else None)
        s = st(d, 80) if d is not None else (0, 0)
        b = A if f2 < h else 0
        if cd == f: b |= D_CBUTTON
        e.step(b, *s, 2); q = player(e); log.append((f, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2))); f += 1
        if cd is not None and f > cd + 30: break
    return log, landed
for job in jobs:
    log, landed = play(*job)
    cands = [(f, x, z, a, sp) for f, x, z, a, sp in log if 566 <= x <= 576 and -22 <= z <= -12 and sp > 30]
    near = min(cands, key=lambda c: abs(c[4] - (616 - c[1])), default=None)
    hits = []
    for f, x, z, a, sp in cands:
        if 616 - x - 1.5 <= sp <= 616 - x + 0.6:
            lg, _ = play(*job, cd=f)
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append((f, x, z, sp))
    rec = {'d0': D0, 'job': job, 'landed': landed, 'near': near, 'end': log[-1][1:3], 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
