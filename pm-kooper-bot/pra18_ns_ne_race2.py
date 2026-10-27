"""pra_18 north->south RIGHT SIDE race test v2: Speedy Spin EQUIPPED (diagnostic setup write to the badge list) and the
touching push carried all the way to the north-wall bump (Laki pinned at x ~620, the furthest a push can take him).
After the push Mario spins (Z) holding angle a1 for k1 frames, then aims at the clip spot T, re-pressing Z whenever a
spin ends while more than R units away, and stops on T. Logs when the history reopens (Laki's dash) and Mario's
distance to T then; tries C-down on every grounded frame on the spot. usage: pra18_ns_ne_race2.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
SPEEDY = 0x11F
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if SPEEDY not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), SPEEDY)              # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); e.save(b0)
T = (572, -15)
pushed = {}
for C in (90, 110, 130):
    e.load(b0); t = push(180, C, 4); fn = '/dev/shm/pmbot/ne%d_p%d.st' % (os.getpid(), C); e.save(fn); pushed[C] = (fn, t, L()[:2])
jobs = list(itertools.product(sorted(pushed), range(30, 151, 10), range(0, 15, 2), (0, 20, 40)))[part::nparts]
fo = open(out, 'a')
for C, a1, k1, R in jobs:
    e.load(pushed[C][0]); reopen = None; best = 0; arrived = None; spins = 0; prev_act = None
    for f in range(70):
        q = player(e); dd = math.hypot(q['x'] - T[0], q['z'] - T[1])
        b = 0
        if f == 0: b = Z; spins += 1
        elif arrived is None and q['action'] in (1, 2) and dd > R and R and prev_act == 26: b = Z; spins += 1
        if f < k1: s = st(a1, 80)
        elif dd > 1.5 and arrived is None: s = st(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])), 80 if dd > 8 else 25)
        else:
            s = (0, 0)
            if arrived is None: arrived = f
        prev_act = q['action']
        e.step(b, *s, 2)
        sp = L()[2]; q = player(e)
        if reopen is None and sp > 10: reopen = (f, round(math.hypot(q['x'] - T[0], q['z'] - T[1]), 1), round(sp, 1))
        if q['action'] in (0, 1, 2) and 568 <= q['x'] <= 576 and -20 <= q['z'] <= -12:
            best = max(best, sp)
            if abs(sp - (616 - q['x'])) < 3:
                ok, s2 = try_clip()
                if ok: print('CLIP', C, a1, k1, R, f, s2, flush=True); fo.write(json.dumps({'C': C, 'a1': a1, 'k1': k1, 'R': R, 'f': f, 'speed': s2}) + '\n'); fo.flush()
    print(json.dumps({'C': C, 'touched': pushed[C][1], 'laki_after_push': [round(v, 1) for v in pushed[C][2]], 'a1': a1, 'k1': k1, 'R': R,
                      'spins': spins, 'arrived_frame': arrived, 'reopen': reopen, 'best_on_spot': round(best, 2)}), flush=True)
print('done')
