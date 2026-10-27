"""pra_18 north->south RIGHT SIDE: (optional Speedy Spin) + jump + run, after the frozen-history touching push.
Setup (pra18_ns_ne_push.py, Speedy Spin equipped as a DIAGNOSTIC badge write): frozen history in the NE pocket,
touching push to the north-wall bump. Mario walks to S (within 38 of Laki), Z-spins at angle a for k frames (k=0: no
spin, walks at angle a instead for w frames), jumps (A held h frames) steering toward the clip spot T, and after
landing RUNS to T and stops. While Mario is above Laki, Laki's speed is capped at 6 (delays him); his dash fires when
he reaches the end of the frozen trail, aimed at where Mario was when Laki ate the trail's first point.
C-down is tried on every idle/walk/run frame on the clip spot while Laki's speed > 20.
usage: pra18_ns_jumprun.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); PUSHT = sum(push(pa, pc, pg) for pa, pc, pg in eval(os.environ.get('PUSHSEQ', '[(180, %s, 4)]' % os.environ.get('PUSHC', 110))))
pushed = '/dev/shm/pmbot/jr%d_p.st' % os.getpid(); e.save(pushed)
T = eval(os.environ.get('T', '(572, -15)'))
STARTS = eval(os.environ.get('STARTS', '[(638, -98), (642, -104), (646, -104), (650, -108)]'))
if os.environ.get('REL'):
    _lx, _lz, _ = L()
    STARTS = [(round(_lx + dx), round(_lz + dz)) for dx, dz in eval(os.environ['REL'])]
jobs = list(itertools.product(STARTS, eval(os.environ.get('ANGS', '[120 + 2.0 * i for i in range(8)]')), eval(os.environ.get('KS', '(0, 1, 2, 3)')),
                              eval(os.environ.get('WS', '(0, 2, 4)')), eval(os.environ.get('HS', '(1, 3, 6)'))))[part::nparts]
fo = open(out, 'a'); cache = {}
for S, a, k, w, h in jobs:
    if k and w: continue
    if S not in cache:
        e.load(pushed)
        for f in range(60):
            q = player(e); dd = math.hypot(q['x'] - S[0], q['z'] - S[1])
            if dd < 1.0: break
            e.step(0, *st(math.degrees(math.atan2(S[1] - q['z'], S[0] - q['x'])), 80 if dd > 6 else 25), 2)
        for i in range(3): e.step(0, 0, 0, 2)
        if fstate() != 5: cache[S] = None
        else: fn = '/dev/shm/pmbot/jr%d_s%d.st' % (os.getpid(), len(cache)); e.save(fn); cache[S] = fn
    if cache[S] is None: continue
    e.load(cache[S]); best = (0, None); landed = None; hits = []; j0 = k + w
    for f in range(50):
        q = player(e); dd = math.hypot(q['x'] - T[0], q['z'] - T[1]); toT = math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x']))
        if f < k: b, s = (Z if f == 0 else 0), st(a, 80)
        elif f < j0: b, s = 0, st(a, 80)
        else:
            b = A if j0 <= f < j0 + h else 0
            if landed is None and f > j0 + 1 and q['action'] in (0, 1, 2): landed = f
            if landed is None: s = st(toT, 80)
            else: s = st(toT, 80 if dd > 6 else 25) if dd > 1.0 else (0, 0)
        pre = '/dev/shm/pmbot/jr%d_pre.st' % os.getpid(); e.save(pre)
        e.step(b, *s, 2)
        q = player(e); sp = L()[2]
        if 566 <= q['x'] <= 578 and -20 <= q['z'] <= -12 and sp > 20:
            if sp > best[0]: best = (round(sp, 2), (round(q['x'], 2), round(q['z'], 2), f))
            post = '/dev/shm/pmbot/jr%d_post.st' % os.getpid(); e.save(post)
            for cs in (s, (0, 0)):                 # C-down ON this frame (the follow speed spikes this frame)
                e.load(pre); e.step(D_CBUTTON | b, *cs, 2); q2 = player(e); s2 = L()[2]
                for j in range(30): e.step(0, 0, 0, 2)
                r = player(e)
                if r['action'] == 33 and r['z'] > 0: hits.append((f, cs, round(q2['x'], 2), round(q2['z'], 2), round(s2, 2)))
            e.load(post)
    rec = {'pushc': int(os.environ.get('PUSHC', 110)), 'touched': PUSHT, 'S': S, 'a': a, 'k': k, 'w': w, 'h': h, 'landed': landed, 'end': [round(q['x'], 2), round(q['z'], 2)], 'best_on_spot': best, 'clips': hits}
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', json.dumps(rec), flush=True)
    print(json.dumps(rec), flush=True)
print('done')
