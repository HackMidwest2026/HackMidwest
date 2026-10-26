"""What does hammering the stone block change in RAM? From the same state, branch A hits the block NHITS times
(2 steps B + 28 idle per hit), branch B stands still for the same number of steps. Diff all 8 MB of RDRAM between A
and B (and A vs the start), group changed words into ranges, label each range with the nearest JP symbol, and report
the save-file region (game flags / bytes) separately. usage: tik23_hammer_ramdiff.py NHITS OUT.json"""
import os, sys, json, bisect, array
from emu import *
from pm import *
from nav import go_to
NH, out = int(sys.argv[1]), sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rd%d' % os.getpid())
e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
go_to(e, -235, -20, maxf=200, tol=2)
for i in range(6): e.step(0, -60, 0, 2)
for i in range(10): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/rd%d_base.st' % os.getpid(); e.save(base); e.step(0, 0, 0, 1)
def snap():
    return array.array('I', bytes(e.ram))
e.load(base); e.step(0, 0, 0, 2); S0 = snap()
for k in range(NH):
    for i in range(2): e.step(B, 0, 0, 2)
    for i in range(28): e.step(0, 0, 0, 2)
SA = snap()
e.load(base); e.step(0, 0, 0, 2)
for k in range(NH * 30): e.step(0, 0, 0, 2)
SB = snap()
# symbols
syms = []
for l in open('/tmp/claude-0/pm/papermario/ver/jp/symbol_addrs.txt'):
    if '=' not in l: continue
    n, a = l.split('=', 1)
    try: syms.append((int(a.split(';')[0].strip(), 16), n.strip()))
    except ValueError: pass
syms.sort(); sa = [s[0] for s in syms]
def label(a):
    i = bisect.bisect_right(sa, a) - 1
    return '%s+0x%x' % (syms[i][1], a - syms[i][0]) if i >= 0 else '?'
REGIONS = [(0x800DACA0, 0x800DACA0 + 0x1380, 'save file (gCurrentSaveFile: flags, bytes)'),
           (0x80268000, 0x80280000, 'collision heap (0x18000)'), (0x802FB800, 0x8034F800, 'general heap'),
           (0x8034F800, 0x803DA800, 'sprite heap'), (0x803DA800, 0x80400000, 'battle heap'),
           (0x8010F450, 0x8010F450 + 0x400, 'gPlayerData'), (0x800B42C0, 0x800B42C0 + 0x20, 'gCollisionData header')]
def region(a):
    for lo, hi, n in REGIONS:
        if lo <= a < hi: return n
    return None
def ranges(X, Y):
    out = []; cur = None
    for i in range(len(X)):
        if X[i] != Y[i]:
            a = 0x80000000 + 4 * i
            if cur and a - cur[1] <= 16: cur[1] = a
            else:
                cur = [a, a]; out.append(cur)
    return out
res = {}
for name, X, Y in (('hammer_vs_idle', SA, SB), ('hammer_vs_start', SA, S0)):
    rr = ranges(X, Y)
    byreg = {}
    for lo, hi in rr:
        n = region(lo) or label(lo)
        byreg.setdefault(n, [0, 0]); byreg[n][0] += 1; byreg[n][1] += (hi - lo) // 4 + 1
    res[name] = {'n_ranges': len(rr), 'by_region': sorted(byreg.items(), key=lambda x: -x[1][1])}
    sv = [(hex(lo), hex(hi), [hex(X[(a - 0x80000000) // 4]) + '/' + hex(Y[(a - 0x80000000) // 4]) for a in range(lo, hi + 4, 4)][:4])
          for lo, hi in rr if region(lo) and region(lo).startswith('save')]
    res[name]['save_file_changes'] = sv
    print(name, 'ranges', len(rr), flush=True)
    for n, (c, w) in res[name]['by_region'][:25]: print('   %-55s %4d ranges %7d words' % (n, c, w))
    print('   save file changes:', sv)
    det = []
    for lo, hi in rr:
        if 0x80268000 <= lo < 0x802FB800 or 0x800DACA0 <= lo < 0x800DC020 or 0x8010F450 <= lo < 0x8010F850:
            det.append((hex(lo), hex(hi), label(lo), [hex(X[(a - 0x80000000) // 4]) + '/' + hex(Y[(a - 0x80000000) // 4]) for a in range(lo, min(hi, lo + 12) + 4, 4)]))
    res[name]['detail'] = det
    for d in det: print('     ', d)
json.dump(res, open(out, 'w'), indent=1)
