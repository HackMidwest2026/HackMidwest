"""pra_18 north->south RIGHT SIDE: Speedy Spin + jump, after the frozen-history touching push.
Setup (pra18_ns_ne_push.py, Speedy Spin equipped as a DIAGNOSTIC badge write): frozen history in the NE pocket,
touching push to the north-wall bump. Mario walks to S (within 38 of Laki; history stays frozen), Z-spins at stick
angle a for k frames, then jumps (A held h frames; while Mario is above Laki, Laki's follow speed is capped at 6, which
delays him), steering jmode ('c' = toward the clip spot, 'a' = keep a, 'n' = neutral), lands, releases the stick.
C-down is tried on every idle/walk/run frame on the clip spot while Laki's speed > 20.
usage: pra18_ns_spinjump.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); push(180, 110, 4)
pushed = '/dev/shm/pmbot/sj%d_p.st' % os.getpid(); e.save(pushed)
T = (572, -15)
STARTS = eval(os.environ.get('STARTS', '[(638, -98), (640, -100), (642, -104), (644, -106), (646, -104), (648, -108), (650, -108)]'))
jobs = list(itertools.product(STARTS, eval(os.environ.get('ANGS', '[124 + 1.0 * i for i in range(10)]')), eval(os.environ.get('KS', 'range(2, 9)')), eval(os.environ.get('HS', '(1, 2, 4, 6)')), os.environ.get('JMS', 'can')))[part::nparts]
fo = open(out, 'a'); cache = {}
for S, a, k, h, jm in jobs:
    if S not in cache:
        e.load(pushed); ok = True
        for f in range(60):
            q = player(e); dd = math.hypot(q['x'] - S[0], q['z'] - S[1])
            if dd < 1.0: break
            e.step(0, *st(math.degrees(math.atan2(S[1] - q['z'], S[0] - q['x'])), 80 if dd > 6 else 25), 2)
        for i in range(3): e.step(0, 0, 0, 2)
        if fstate() != 5: cache[S] = None
        else: fn = '/dev/shm/pmbot/sj%d_s%d.st' % (os.getpid(), len(cache)); e.save(fn); cache[S] = fn
    if cache[S] is None: continue
    e.load(cache[S]); best = (0, None); landed = None; hits = []
    for f in range(45):
        q = player(e)
        if f < k: b, s = (Z if f == 0 else 0), st(a, 80)
        else:
            b = A if k <= f < k + h else 0
            air = q['action'] not in (0, 1, 2, 26) or f < k + 2
            if landed is None and not air: landed = f
            if landed is not None: s = (0, 0)
            elif jm == 'c': s = st(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])), 80)
            elif jm == 'a': s = st(a, 80)
            else: s = (0, 0)
        e.step(b, *s, 2)
        q = player(e); sp = L()[2]
        if 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12 and q['action'] in (0, 1, 2):
            if sp > best[0]: best = (round(sp, 2), (round(q['x'], 2), round(q['z'], 2), f))
            if sp > 20:
                ok, s2 = try_clip()
                if ok: hits.append((f, round(q['x'], 2), round(q['z'], 2), round(s2, 2)))
    rec = {'S': S, 'a': a, 'k': k, 'h': h, 'jm': jm, 'landed': landed, 'end': [round(q['x'], 2), round(q['z'], 2)], 'best_on_spot': best, 'clips': hits}
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', json.dumps(rec), flush=True)
    print(json.dumps(rec), flush=True)
print('done')
