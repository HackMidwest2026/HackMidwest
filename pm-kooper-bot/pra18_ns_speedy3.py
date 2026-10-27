"""pra_18 north->south RIGHT SIDE: Speedy Spin + full touching push, 'stop dead' plan.
Setup as pra18_ns_ne_push.py (+ Speedy Spin equipped, DIAGNOSTIC badge write): frozen history in the NE pocket,
touching push to the north-wall bump (Laki ~(620.9,-132.2)). Mario walks to S (staying within 40 of Laki so the
history stays frozen), Z-spins holding angle a; when Mario reaches x <= xr (or z > -16) the stick is released, which
stops him dead (spinning in place records nothing). Pass 1 logs whether Laki's history was still frozen when Mario
stopped and where Laki ends up idling. Pass 2 (only for runs where it was): wait W frames for the spin to end, a 1-frame
nudge (angle na, magnitude nm) records one point, C-down on frame j after. usage: pra18_ns_speedy3.py PART NPARTS OUT"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); push(180, 110, 4)
pushed = '/dev/shm/pmbot/s3%d_p.st' % os.getpid(); e.save(pushed)
LX, LZ, _ = L()
starts = [(x, z) for x in range(int(os.environ.get("X0", 604)), int(os.environ.get("X1", 651)), int(os.environ.get("DX", 3))) for z in range(int(os.environ.get("Z0", -134)), int(os.environ.get("Z1", -99)), int(os.environ.get("DX", 3))) if math.hypot(x - LX, z - LZ) <= 38]
jobs = list(itertools.product(starts, [float(os.environ.get("A0", 104)) + float(os.environ.get("DA", 1)) * i for i in range(int(os.environ.get("NA", 22)))], (573, 576)))[part::nparts]
fo = open(out, 'a'); cache = {}
for S, a, xr in jobs:
    if S not in cache:
        e.load(pushed); ok = True
        for f in range(60):
            q = player(e); dd = math.hypot(q['x'] - S[0], q['z'] - S[1])
            if dd < 1.0: break
            e.step(0, *st(math.degrees(math.atan2(S[1] - q['z'], S[0] - q['x'])), 80 if dd > 6 else 25), 2)
            if fstate() != 5: ok = False; break
        for i in range(3): e.step(0, 0, 0, 2)
        if not ok or fstate() != 5: cache[S] = None
        else: fn = '/dev/shm/pmbot/s3%d_s%d_%d.st' % (os.getpid(), S[0], -S[1]); e.save(fn); cache[S] = fn
    if cache[S] is None: continue
    e.load(cache[S]); stopped = None; ptr0 = e.u32(PTR); skipped = False
    for f in range(30):
        q = player(e)
        go_on = stopped is None and q['x'] > xr and q['z'] <= -16
        e.step(Z if f == 0 else 0, *(st(a, 80) if go_on else (0, 0)), 2)
        if fstate() == 0 and e.u32(PTR) != ptr0 and not (31 <= e.u32(PTR) <= 39): skipped = True
        if stopped is None and not go_on:
            k = e.u32(PTR); hx = e.f32(HIST + 16 * k + 4)
            stopped = (f, round(q['x'], 2), round(q['z'], 2), k, round(hx))
    for f in range(30): e.step(0, 0, 0, 2)
    p = player(e); lx, lz, sp = L(); k = e.u32(PTR); hx, hz = e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)
    frozen_ok = hx > 690 and fstate() == 0 and sp < 0.5        # Laki idles at the end of the frozen trail
    rec = {'S': S, 'a': a, 'xr': xr, 'stopped': stopped, 'mario': [round(p['x'], 2), round(p['z'], 2), p['action']],
           'laki': [round(lx, 1), round(lz, 1), round(sp, 2), fstate()], 'tgt': [round(hx), round(hz)], 'idle_far': frozen_ok,
           'pred': round(0.25 * math.hypot(lx - p['x'], lz - p['z']), 2), 'need': round(616 - p['x'], 2)}
    if frozen_ok and 566 <= p['x'] <= 578 and p['z'] > -22:
        base = '/dev/shm/pmbot/s3%d_b.st' % os.getpid(); e.save(base); hits = []
        for na, nm in itertools.product((0, 180, 90, 270, 45, 135), (18, 24, 30, 40)):
            e.load(base); e.step(0, *st(na, nm), 2)
            for j in range(4):
                q = player(e); sp = L()[2]
                if q['action'] in (0, 1, 2):
                    ok, s2 = try_clip()
                    if ok: hits.append((na, nm, j, round(q['x'], 2), round(s2, 2)))
                e.step(0, 0, 0, 2)
        rec['clips'] = hits
        if hits: fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', json.dumps(rec), flush=True)
    print(json.dumps(rec), flush=True)
print('done')
