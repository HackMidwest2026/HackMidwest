"""pra_18 north->south RIGHT SIDE with Speedy Spin + a full touching push.
Setup (pra18_ns_ne_push.py): frozen 40-entry history in the NE pocket (trail ends ~(733,-120)); touching push west
along the north wall to the bump (Laki pinned at ~(620,-132)). Speedy Spin equipped (DIAGNOSTIC badge write).
Then: Z spin holding angle a1 for k1 frames (keeps Laki's frozen target within 90 deg of Mario so Laki flies back to
the NE pocket instead of skipping the trail), steer to (xt, -20), then hold straight down into the mirror: Mario
stays pinned (pinned frames are not recorded), Laki finishes the frozen trail and idles ~170 units away. After W idle
frames, a 1-frame nudge (stick angle na, magnitude nm) records one new history point; Laki's next speed is 1/4 of his
distance to it. C-down is tried on each of the next frames. usage: pra18_ns_speedy.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
sys.argv, ARGV = ['x', '0', '1', '/dev/null'], sys.argv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
part, nparts, out = int(ARGV[1]), int(ARGV[2]), ARGV[3]
e.load(b0)
slots = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in slots: e.w16(PLAYER_DATA + 0x208 + 2 * slots.index(0), 0x11F)            # DIAGNOSTIC: equip Speedy Spin
e.step(0, 0, 0, 2); e.save(b0)
pushed = {}
for C in (110,):
    e.load(b0); t = push(180, C, 4); fn = '/dev/shm/pmbot/sp%d_p%d.st' % (os.getpid(), C); e.save(fn); pushed[C] = (fn, t)
fo = open(out, 'a')
jobs = list(itertools.product((110,), (80, 90, 100), (2, 4, 6), [570 + 0.5 * i for i in range(17)]))[part::nparts]
for C, a1, k1, xt in jobs:
    e.load(pushed[C][0])
    for f in range(k1): e.step(Z if f == 0 else 0, *st(a1, 80), 2)
    for f in range(40):
        q = player(e); dd = math.hypot(q['x'] - xt, q['z'] + 20)
        if dd < 2.5 or q['z'] > -20: break
        e.step(Z if (k1 == 0 and f == 0) else 0, *st(math.degrees(math.atan2(-20 - q['z'], xt - q['x'])), 80), 2)
    for f in range(30): e.step(0, *st(90, 80), 2)                 # pin into the mirror until the spin ends
    pinned = player(e); lx, lz, sp0 = L()
    base = '/dev/shm/pmbot/sp%d_b.st' % os.getpid(); e.save(base)
    res = []
    for W, na, nm in itertools.product((0, 4, 10), (0, 180, 270, 90), (20, 30, 45)):
        e.load(base)
        for i in range(W): e.step(0, 0, 0, 2)
        e.step(0, *st(na, nm), 2)
        for j in range(6):
            q = player(e); sp = L()[2]
            if q['action'] in (0, 1, 2) and q['z'] < 0:
                ok, s2 = try_clip()
                need = 616 - q['x']
                res.append((round(sp, 2), round(need, 2)))
                if ok:
                    rec = {'C': C, 'a1': a1, 'k1': k1, 'xt': xt, 'W': W, 'na': na, 'nm': nm, 'j': j, 'at': [q['x'], q['z']], 'speed': s2}
                    fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
            e.step(0, 0, 0, 2)
    near = min(res, key=lambda r: abs(r[0] - r[1])) if res else None
    print(json.dumps({'C': C, 'a1': a1, 'k1': k1, 'xt': xt, 'pinned': [round(pinned['x'], 2), round(pinned['z'], 2), pinned['action']],
                      'laki': [round(lx, 1), round(lz, 1), round(sp0, 2)], 'closest(speed,need)': near, 'max': max(r[0] for r in res) if res else 0}), flush=True)
print('done')
