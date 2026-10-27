"""pra_18 north->south RIGHT SIDE race test: after the NE-pocket frozen history + touching push (pra18_ns_ne_push.py
setup, C push frames along the north wall), Mario Speedy-Spins away holding angle a1 for k1 frames (so Laki's frozen
target stays within 90 degrees of Mario's direction when Laki leaves hover), then aims at the clip spot T and stops on
it. The history reopens when Laki reaches the end of the frozen trail; for a clip Mario must already be standing on T
then (the dash is 0.25 x Laki->Mario's first new history point). Logs Mario's distance to T at the reopen frame and the
best Laki speed on the clip spot; tries C-down there. usage: pra18_ns_ne_race.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
T = (572, -15)
pushed = {}
for C in (40, 55, 70, 85, 110):
    e.load(b0); t = push(180, C, 4); fn = '/dev/shm/pmbot/ne%d_p%d.st' % (os.getpid(), C); e.save(fn); pushed[C] = (fn, t)
jobs = list(itertools.product(sorted(pushed), range(40, 131, 10), range(0, 13, 2)))[part::nparts]
fo = open(out, 'a')
for C, a1, k1 in jobs:
    e.load(pushed[C][0]); reopen = None; best = 0; prev_ptr = e.u32(PTR); f = 0; arrived = None
    while f < 70:
        q = player(e); dd = math.hypot(q['x'] - T[0], q['z'] - T[1])
        if f < k1: s = st(a1, 80)
        elif dd > 1.5 and arrived is None: s = st(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])), 80 if dd > 8 else 25)
        else: s = (0, 0); arrived = arrived if arrived is not None else f
        e.step(Z if f == 0 else 0, *s, 2); f += 1
        sp = L()[2]; q = player(e)
        if reopen is None and sp > 10: reopen = (f, round(math.hypot(q['x'] - T[0], q['z'] - T[1]), 1), round(sp, 1))
        if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
            best = max(best, sp)
            if abs(sp - (616 - q['x'])) < 3:
                ok, s2 = try_clip()
                if ok: print('CLIP', C, a1, k1, f, s2, flush=True); fo.write(json.dumps({'C': C, 'a1': a1, 'k1': k1, 'f': f, 'speed': s2}) + '\n'); fo.flush()
    print(json.dumps({'C': C, 'touched': pushed[C][1], 'a1': a1, 'k1': k1, 'arrived_frame': arrived, 'reopen': reopen, 'best_on_spot': round(best, 2)}), flush=True)
print('done')
