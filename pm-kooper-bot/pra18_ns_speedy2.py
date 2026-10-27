"""pra_18 north->south RIGHT SIDE, Speedy Spin aimed straight at the clip spot.
Setup (pra18_ns_ne_push.py + Speedy Spin equipped as a DIAGNOSTIC badge write): frozen history in the NE pocket,
full touching push to the north-wall bump (Laki pinned ~(620,-132)). Then Mario walks to a spin start S while staying
within 40 of Laki (Laki keeps hovering, history stays frozen), Z-spins at stick angle a, holding mode h:
 'a' = keep holding a, 'down' = hold straight down once z > -35, 'none' = release once z > -35.
C-down is tried on every frame Mario is grounded (idle/walk/run) on the clip spot with Laki speed > 20.
usage: pra18_ns_speedy2.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); push(180, 110, 4)
pushed = '/dev/shm/pmbot/s2%d_p.st' % os.getpid(); e.save(pushed)
LX, LZ, _ = L()
starts = [(x, z) for x in range(588, 645, 4) for z in range(-130, -93, 4) if math.hypot(x - LX, z - LZ) <= 37]
jobs = list(itertools.product(starts, [95 + 2.5 * i for i in range(17)], ('a', 'down', 'none')))[part::nparts]
fo = open(out, 'a'); cache = {}
for S, a, h in jobs:
    if S not in cache or not os.path.exists(cache[S]):
        e.load(pushed); ok = True
        for f in range(60):
            q = player(e); dd = math.hypot(q['x'] - S[0], q['z'] - S[1])
            if dd < 1.0: break
            e.step(0, *st(math.degrees(math.atan2(S[1] - q['z'], S[0] - q['x'])), 80 if dd > 6 else 25), 2)
            if fstate() != 5: ok = False; break
        for i in range(3): e.step(0, 0, 0, 2)
        if not ok or fstate() != 5: cache[S] = None; continue
        fn = '/dev/shm/pmbot/s2%d_s%d_%d.st' % (os.getpid(), S[0], -S[1]); e.save(fn); cache[S] = fn
    if cache[S] is None: continue
    e.load(cache[S]); best = (0, None); reopen = None; trace = []
    for f in range(45):
        q = player(e)
        if f == 0: b, s = Z, st(a, 80)
        elif h == 'a' or q['z'] <= -35: b, s = 0, st(a, 80)
        elif h == 'down': b, s = 0, st(90, 80)
        else: b, s = 0, (0, 0)
        e.step(b, *s, 2)
        q = player(e); sp = L()[2]
        if reopen is None and fstate() == 0 and sp > 25: reopen = (f, round(q['x'], 1), round(q['z'], 1), q['action'], round(sp, 1))
        if 566 <= q['x'] <= 578 and q['z'] > -22 and sp > best[0]: best = (round(sp, 2), (round(q['x'], 2), round(q['z'], 2), q['action'], f))
        if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12 and sp > 20:
            ok, s2 = try_clip()
            if ok:
                rec = {'S': S, 'a': a, 'h': h, 'f': f, 'at': [q['x'], q['z']], 'speed': s2}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    print(json.dumps({'S': S, 'a': a, 'h': h, 'reopen': reopen, 'best_near_spot': best}), flush=True)
print('done')
