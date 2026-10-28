"""Find touching-push sequences (steered push, pra18_ns_ne_push.py push()) from the ORIGINAL NE-pocket freeze
(first trail point ~(701,-113), so Laki's way back passes south of the north-wall bump) that carry Laki far west while
he keeps hovering with the history frozen. usage: pra18_ns_pushsearch.py"""
import os, sys, math, itertools
sys.argv = ['x', '0', '1', '/dev/null']; os.environ['CORNER'] = '0'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_ne_push.py')).read().split('TARGETS =')[0])
e.load(b0); ptr0 = e.u32(PTR); k = ptr0
print('freeze: laki (%.1f,%.1f) P (%.0f,%.0f) ptr %d' % (L()[0], L()[1], e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12), ptr0), flush=True)
res = []
s1 = '/dev/shm/pmbot/ps_s1.st'
for c1 in (150, 200, 250):
    e.load(b0); push(180, c1, 4); e.save(s1)
    lx, lz, _ = L(); print('push180 %d -> laki (%.1f,%.1f) st %d ptr %d' % (c1, lx, lz, fstate(), e.u32(PTR)), flush=True)
    for a2, g2 in itertools.product(range(200, 271, 10), (5, 6, 7, 9)):
        e.load(s1); push(a2, 120, g2); push(180, 250, 4)
        lx, lz, _ = L(); ok = fstate() == 5 and e.u32(PTR) == ptr0
        res.append((round(lx, 1), round(lz, 1), c1, a2, g2, ok))
res = [r for r in res if r[5]]; res.sort()
for r in res[:8]: print('laki x %.1f z %.1f | push180 %d, then angle %d gap %d, then push180 250 | frozen %s' % r, flush=True)
